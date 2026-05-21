"""Deterministic CSV ingestion for the SaaS Spend project."""

from __future__ import annotations

import importlib.util
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pprint import pformat
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel

from db.connection import (
    get_database_path,
    get_next_version,
    get_project_root,
    get_uploads_dir,
    get_vendor_rules_path,
    get_versioned_table_name,
    open_database_connection,
    promote_current_version,
    resolve_current_version,
)

LOGGER = logging.getLogger(__name__)


class RuntimeSettings(BaseModel):
    """Resolved filesystem settings for the ingestion runtime."""

    project_root: Path
    database_path: Path
    uploads_dir: Path
    vendor_rules_path: Path


@dataclass(slots=True)
class DiscoveryProfile:
    """In-memory discovery profile for a single categorical column."""

    column_name: str
    observed_values: list[str]
    null_rate: float
    row_count: int


def get_runtime_settings() -> RuntimeSettings:
    """Resolve runtime paths from environment-aware helpers."""

    return RuntimeSettings(
        project_root=get_project_root(),
        database_path=get_database_path(),
        uploads_dir=get_uploads_dir(),
        vendor_rules_path=get_vendor_rules_path(),
    )


def _load_vendor_rules_file(path: Path) -> dict[str, Any]:
    """Load the persisted vendor rules module if it exists."""

    if not path.exists():
        return {}

    namespace: dict[str, Any] = {}
    spec = importlib.util.spec_from_file_location("vendor_rules_runtime", path)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    vendor_rules = getattr(module, "vendor_rules", {})
    if isinstance(vendor_rules, dict):
        return vendor_rules
    return {}


def _persist_vendor_rules_file(path: Path, vendor_rules: dict[str, Any]) -> None:
    """Persist vendor discovery output as a Python module."""

    # Discovery profiles are already stored in SQLite. Rewriting a watched .py
    # file during uvicorn --reload restarts the API and can kill the pipeline
    # background thread mid-run.
    if path.suffix == ".py":
        LOGGER.info("Skipping runtime vendor_rules.py rewrite to avoid dev-server reload.")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = pformat(vendor_rules, sort_dicts=True, width=120)
    path.write_text(f"vendor_rules = {serialized}\n", encoding="utf-8")


def _load_json_list(payload: object) -> list[str]:
    """Return a normalized list of string values from a JSON payload."""

    if not isinstance(payload, list):
        return []
    values: list[str] = []
    for value in payload:
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def _load_dataframe(filepath: str) -> pd.DataFrame:
    """Read a CSV file into a dataframe."""

    return pd.read_csv(filepath)


def _schema_fingerprint(df: pd.DataFrame) -> str:
    """Compute a deterministic schema fingerprint for a dataframe."""

    tokens = [f"{column}:{str(dtype)}" for column, dtype in zip(df.columns, df.dtypes)]
    digest_source = "|".join(sorted(tokens))
    return sha256(digest_source.encode("utf-8")).hexdigest()


def _is_categorical(series: pd.Series) -> bool:
    """Return True when a series should be treated as categorical."""

    return pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series) or pd.api.types.is_bool_dtype(series) or pd.api.types.is_categorical_dtype(series)


def _profile_discovery(df: pd.DataFrame) -> list[DiscoveryProfile]:
    """Build discovery profiles for categorical columns."""

    row_count = int(len(df))
    profiles: list[DiscoveryProfile] = []

    for column in df.columns:
        series = df[column]
        if not _is_categorical(series):
            continue

        non_null_values = (
            series.dropna()
            .astype(str)
            .map(lambda value: value.strip())
            .replace("", pd.NA)
            .dropna()
            .tolist()
        )
        observed_values = sorted(dict.fromkeys(non_null_values))
        null_rate = float(series.isna().mean()) if row_count else 0.0
        profiles.append(
            DiscoveryProfile(
                column_name=column,
                observed_values=observed_values,
                null_rate=null_rate,
                row_count=row_count,
            )
        )

    return profiles


def _merge_vendor_rules(
    current_rules: dict[str, Any],
    vendor: str,
    table_name: str,
    profiles: list[DiscoveryProfile],
) -> dict[str, Any]:
    """Merge discovery observations into the vendor rules document."""

    vendor_entry = current_rules.setdefault(vendor, {})
    table_entry = vendor_entry.setdefault(table_name, {})
    value_rules = table_entry.setdefault("value_rules", {})

    for profile in profiles:
        column_rule = value_rules.setdefault(profile.column_name, {})
        existing_values = column_rule.get("allowed_values", [])
        merged_values = sorted(
            dict.fromkeys([*map(str, existing_values), *map(str, profile.observed_values)])
        )
        column_rule["allowed_values"] = merged_values

    return current_rules


def get_discovered_values(table_name: str, column_name: str) -> list[str]:
    """
    Return discovered categorical values for a table/column pair.

    The function is intentionally forgiving: if discovery is missing or
    malformed, an empty list is returned instead of raising.
    """

    try:
        connection = open_database_connection()
        try:
            rows = connection.execute(
                """
                SELECT observed_values
                FROM vendor_profiles
                WHERE table_name = ? AND column_name = ?
                ORDER BY derived_from_version DESC, created_at DESC, id DESC
                """,
                (table_name, column_name),
            ).fetchall()
        finally:
            connection.close()
    except Exception:
        return []

    discovered: list[str] = []
    seen: set[str] = set()
    for row in rows:
        payload = row[0]
        try:
            parsed = json.loads(payload)
        except Exception:
            continue
        for value in _load_json_list(parsed):
            if value in seen:
                continue
            seen.add(value)
            discovered.append(value)
    return discovered


def get_last_ingested_count(table_name: str) -> int | None:
    """
    Return the most recent ingested row count for a table.

    The preferred source is a loaded ingestion row. If the ingest lifecycle has
    already promoted rows away from the loaded state, we fall back to the most
    recent promoted row so the helper still reflects the latest successful load.
    """

    try:
        connection = open_database_connection()
        try:
            for statuses in (("loaded",), ("promoted",)):
                placeholders = ",".join("?" for _ in statuses)
                row = connection.execute(
                    f"""
                    SELECT row_count
                    FROM data_versions
                    WHERE table_name = ?
                      AND status IN ({placeholders})
                    ORDER BY ingested_at DESC, version_id DESC
                    LIMIT 1
                    """,
                    (table_name, *statuses),
                ).fetchone()
                if row is not None and row[0] is not None:
                    return int(row[0])
        finally:
            connection.close()
    except Exception:
        return None
    return None


def _prepare_license_utilization_frame(
    df: pd.DataFrame,
    audit_date: pd.Timestamp,
    connection: sqlite3.Connection,
) -> pd.DataFrame:
    """Recompute authoritative derived fields for license utilization."""

    updated = df.copy()

    if "last_active_date" in updated.columns:
        last_active = pd.to_datetime(updated["last_active_date"], errors="coerce")
        updated["days_since_last_active"] = (audit_date - last_active).dt.days
        updated.loc[last_active.isna(), "days_since_last_active"] = pd.NA
    else:
        LOGGER.warning("license_utilization ingest is missing last_active_date.")

    if "provisioned_date" in updated.columns:
        provisioned = pd.to_datetime(updated["provisioned_date"], errors="coerce")
        updated["days_since_provisioned"] = (audit_date - provisioned).dt.days
    else:
        LOGGER.warning("license_utilization ingest is missing provisioned_date.")

    required_contract_columns = {"current_of_id"}
    if not required_contract_columns.issubset(updated.columns):
        LOGGER.warning(
            "license_utilization ingest cannot recompute contract fields without current_of_id."
        )
        return updated

    try:
        current_version = resolve_current_version("vendor_overview")
    except Exception as exc:  # pragma: no cover - defensive log path
        LOGGER.warning("vendor_overview is not yet available for contract lookups: %s", exc)
        return updated

    vendor_table = get_versioned_table_name("vendor_overview", current_version)
    vendor_frame = pd.read_sql_query(
        f"""
        SELECT of_id, contract_expiry, notice_deadline, auto_renewal,
               true_down_rights, measurement_method
        FROM {vendor_table}
        """,
        connection,
    )

    if vendor_frame.empty:
        LOGGER.warning("vendor_overview lookup returned no rows for contract lookups.")
        return updated

    # --- FIX START: Consolidate vendor rows to prevent row tripling ---
    # Since contract terms (expiry, etc.) are the same across license tiers, 
    # we group by of_id and take the first occurrence.
    vendor_frame = vendor_frame.groupby("of_id").first().reset_index()
    # --- FIX END ---

    vendor_frame = vendor_frame.rename(columns={"of_id": "current_of_id"})
    
    # Now this merge is 1-to-1, keeping your row count at 16,700
    merged = updated.merge(vendor_frame, on="current_of_id", how="left", suffixes=("", "_vendor"))

    if "contract_expiry" in merged.columns:
        contract_expiry = pd.to_datetime(merged["contract_expiry"], errors="coerce")
        merged["contract_days_remaining"] = (contract_expiry - audit_date).dt.days
        merged.loc[contract_expiry.isna(), "contract_days_remaining"] = pd.NA
        merged["renewal_urgency"] = merged["contract_days_remaining"].apply(
            lambda value: "expired" if pd.notna(value) and int(value) < 0 else "ok"
        )
    else:
        LOGGER.warning("vendor_overview lookup did not provide contract_expiry.")

    if "notice_deadline" in merged.columns:
        notice_deadline = pd.to_datetime(merged["notice_deadline"], errors="coerce")
        merged["days_until_notice"] = (notice_deadline - audit_date).dt.days
        merged.loc[notice_deadline.isna(), "days_until_notice"] = pd.NA
    else:
        LOGGER.warning("vendor_overview lookup did not provide notice_deadline.")

    for column in ("auto_renewal", "true_down_rights", "measurement_method"):
        if column not in merged.columns:
            LOGGER.warning("vendor_overview lookup did not provide %s.", column)

    return merged


def _persist_profiles(
    connection: sqlite3.Connection,
    vendor: str,
    table_name: str,
    version_id: int,
    profiles: list[DiscoveryProfile],
) -> None:
    """Write discovery profile rows to SQLite."""

    if not profiles:
        return

    rows = [
        {
            "vendor": vendor,
            "table_name": table_name,
            "derived_from_version": version_id,
            "column_name": profile.column_name,
            "observed_values": json.dumps(profile.observed_values, sort_keys=True),
            "null_rate": profile.null_rate,
            "row_count": profile.row_count,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        for profile in profiles
    ]
    pd.DataFrame(rows).to_sql(
        "vendor_profiles",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=400,     # Adjust this number based on your column count
    )


def ingest(
    filepath: str,
    vendor: str,
    table_name: str,
    audit_date: str,
    auto_promote: bool = True,
) -> dict[str, Any]:
    """
    Ingest a CSV into a versioned SQLite table.

    If auto_promote=True (default): promotes immediately. Existing behavior.
    If auto_promote=False: writes table + data_versions row with status='pending'.
    Does NOT call promote_version. Caller is responsible for promotion or rollback.
    """

    settings = get_runtime_settings()
    source_path = Path(filepath).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {source_path}")

    LOGGER.info("Starting ingest for %s / %s", vendor, table_name)
    source_frame = _load_dataframe(str(source_path))
    fingerprint = _schema_fingerprint(source_frame)
    LOGGER.info("Schema fingerprint for %s/%s: %s", vendor, table_name, fingerprint)

    connection = open_database_connection()
    try:
        connection.execute("BEGIN")
        try:
            mode = "discovery"
            if connection.execute(
                "SELECT 1 FROM vendor_profiles WHERE vendor = ? AND table_name = ? LIMIT 1",
                (vendor, table_name),
            ).fetchone():
                mode = "validation"
            LOGGER.info("%s mode detected for %s/%s", mode.capitalize(), vendor, table_name)

            discovery_profiles = _profile_discovery(source_frame) if mode == "discovery" else []

            audit_timestamp = pd.Timestamp(audit_date)
            prepared_frame = source_frame.copy()
            if table_name == "license_utilization":
                prepared_frame = _prepare_license_utilization_frame(
                    prepared_frame,
                    audit_timestamp,
                    connection,
                )

            version_id = get_next_version(table_name)
            versioned_table_name = get_versioned_table_name(table_name, version_id)
            LOGGER.info("Writing versioned table %s...", versioned_table_name)

            prepared_frame.to_sql(
                versioned_table_name,
                connection,
                if_exists="replace",
                index=False,
                chunksize=400,
                method="multi",    # Adjust this number based on your column count
            )

            ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            connection.execute(
                """
                INSERT INTO data_versions (
                    version_id, table_name, row_count, schema_fingerprint, 
                    ingested_at, status, vendor, mode
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    table_name,
                    int(len(prepared_frame)),
                    fingerprint,
                    ingested_at,
                    "loaded",
                    vendor,
                    mode,
                ),
            )

            if discovery_profiles:
                _persist_profiles(connection, vendor, table_name, version_id, discovery_profiles)
                current_rules = _load_vendor_rules_file(settings.vendor_rules_path)
                merged_rules = _merge_vendor_rules(current_rules, vendor, table_name, discovery_profiles)
                _persist_vendor_rules_file(settings.vendor_rules_path, merged_rules)

            if auto_promote:
                promote_current_version(table_name, version_id, connection=connection)
                connection.execute(
                    "UPDATE data_versions SET status = ? WHERE version_id = ?",
                    ("promoted", version_id),
                )
                LOGGER.info("Promoted %s as current...", versioned_table_name)
            else:
                connection.execute(
                    "UPDATE data_versions SET status = ? WHERE version_id = ?",
                    ("pending", version_id),
                )
                LOGGER.info("Pending %s — awaiting trial run...", versioned_table_name)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    finally:
        connection.close()

    return {
        "vendor": vendor,
        "table_name": table_name,
        "version_id": version_id,
        "versioned_table_name": versioned_table_name,
        "mode": mode,
        "row_count": int(len(prepared_frame)),
        "schema_fingerprint": fingerprint,
        "promoted": auto_promote,
    }
