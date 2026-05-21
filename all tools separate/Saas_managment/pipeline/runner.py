"""Pipeline trial run orchestrator."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable

from pipeline.checks import (
    CheckResult,
    check_api_layer,
    check_ingestion,
    check_processing_layer,
    check_service_layer,
)

LOGGER = logging.getLogger(__name__)

CANONICAL_TABLES = ("vendor_overview", "hr_headcount", "license_utilization")
PATH_COLUMN_CANDIDATES = ("file_path", "source_path", "saved_path", "filepath", "path")


class ExistingDataNotFoundError(RuntimeError):
    """Raised when refresh cannot locate a complete prior ingestion source set."""


@dataclass
class TrialRunReport:
    table_name: str
    pending_version: int | None      # None if ingestion itself failed
    all_passed: bool
    promoted: bool
    rolled_back: bool
    checks: list[CheckResult] = field(default_factory=list)
    started_at: str = ""             # ISO timestamp
    completed_at: str = ""
    failure_summary: str | None = None  # first failure message, or None


def _resolve_existing_source_path(raw_path: str) -> Path:
    """Resolve a stored source path relative to the project root when needed."""

    from db.connection import get_project_root

    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = get_project_root() / candidate
    return candidate.resolve()


def _get_data_versions_path_column(connection) -> str:
    """Return the first supported path column in data_versions or raise clearly."""

    columns = {row[1] for row in connection.execute("PRAGMA table_info(data_versions)").fetchall()}
    for column in PATH_COLUMN_CANDIDATES:
        if column in columns:
            return column
    connection.execute("ALTER TABLE data_versions ADD COLUMN file_path TEXT")
    connection.commit()
    return "file_path"


def _record_source_path(table_name: str, version_id: int, file_path: str) -> None:
    """Persist the source CSV path for future refresh runs."""

    from db.connection import open_database_connection

    connection = open_database_connection()
    try:
        path_column = _get_data_versions_path_column(connection)
        resolved_path = str(_resolve_existing_source_path(file_path))
        connection.execute(
            f"UPDATE data_versions SET {path_column} = ? WHERE table_name = ? AND version_id = ?",
            (resolved_path, table_name, version_id),
        )
        connection.commit()
    finally:
        connection.close()


def _find_uploaded_source_for_table(table_name: str) -> Path | None:
    """Find the newest uploaded CSV matching a canonical table prefix."""

    from db.connection import get_uploads_dir

    uploads_dir = get_uploads_dir()
    candidates = [
        path for path in uploads_dir.glob("*.csv")
        if path.stem.lower().startswith(table_name)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime).resolve()


def _get_latest_existing_paths() -> list[tuple[Path, str]]:
    """Read and validate the most recent stored CSV path for each canonical table."""

    from db.connection import open_database_connection

    connection = open_database_connection()
    try:
        path_column = _get_data_versions_path_column(connection)
        rows_by_table = {}
        backfills: list[tuple[Path, str, int]] = []
        for table_name in CANONICAL_TABLES:
            row = connection.execute(
                f"""
                SELECT version_id, {path_column}
                FROM data_versions
                WHERE table_name = ?
                ORDER BY ingested_at DESC, version_id DESC
                LIMIT 1
                """,
                (table_name,),
            ).fetchone()
            if row is None:
                continue

            version_id = int(row[0])
            raw_path = row[1]
            if raw_path is None or str(raw_path).strip() == "":
                fallback_path = _find_uploaded_source_for_table(table_name)
                if fallback_path is None:
                    continue
                rows_by_table[table_name] = str(fallback_path)
                backfills.append((fallback_path, table_name, version_id))
            else:
                rows_by_table[table_name] = raw_path

        for path, table_name, version_id in backfills:
            connection.execute(
                f"UPDATE data_versions SET {path_column} = ? WHERE table_name = ? AND version_id = ?",
                (str(path), table_name, version_id),
            )
        if backfills:
            connection.commit()
    finally:
        connection.close()

    missing_tables = [table for table in CANONICAL_TABLES if table not in rows_by_table]
    if missing_tables:
        raise ExistingDataNotFoundError(
            "No existing data found. Missing prior ingestion path for: "
            + ", ".join(missing_tables)
        )

    resolved_pairs: list[tuple[Path, str]] = []
    missing_paths: list[str] = []
    for table_name in CANONICAL_TABLES:
        path = _resolve_existing_source_path(str(rows_by_table[table_name]))
        if not path.exists():
            missing_paths.append(f"{table_name}: {path}")
        resolved_pairs.append((path, table_name))

    if missing_paths:
        raise ExistingDataNotFoundError(
            "No existing data found. Stored CSV path is missing for: "
            + "; ".join(missing_paths)
        )

    return resolved_pairs


def _detect_vendor_from_pairs(file_table_pairs: list[tuple[Path, str]]) -> str | None:
    """Detect the vendor label from the existing vendor_overview source."""

    for csv_path, table_name in file_table_pairs:
        if table_name != "vendor_overview":
            continue
        try:
            import pandas as pd

            df = pd.read_csv(csv_path, nrows=1)
            if "vendor" in df.columns and not df.empty:
                return str(df["vendor"].iloc[0])
        except Exception as exc:
            LOGGER.warning("Could not detect vendor from existing CSV: %s", exc)
        return None
    return None


def run_from_existing_paths(
    audit_date: str | None = None,
    api_base_url: str | None = None,
    force_promote: bool = False,
    status_callback: Optional[Callable[[str, str], None]] = None,
) -> list[TrialRunReport]:
    """
    Re-run the pipeline using the latest stored source CSV paths.

    This intentionally delegates each table to run_trial so refresh uses the
    same ingestion, validation, vendor discovery, processing checks, promotion,
    rollback, and data_versions lifecycle as an upload-backed run.
    """

    if audit_date is None:
        audit_date = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    file_table_pairs = _get_latest_existing_paths()
    detected_vendor = _detect_vendor_from_pairs(file_table_pairs)

    reports: list[TrialRunReport] = []
    for csv_path, table_name in file_table_pairs:
        LOGGER.info("Refresh trial run: %s -> %s", csv_path.name, table_name)
        reports.append(
            run_trial(
                file_path=str(csv_path),
                table_name=table_name,
                audit_date=audit_date,
                vendor=detected_vendor,
                api_base_url=api_base_url,
                force_promote=force_promote,
                status_callback=status_callback,
            )
        )
    return reports


def run_initial_discovery_batch(
    file_table_pairs: list[tuple[str | Path, str]],
    audit_date: str | None = None,
    api_base_url: str | None = None,
    status_callback: Optional[Callable[[str, str], None]] = None,
) -> list[TrialRunReport]:
    """
    Ingest the first complete canonical dataset as one coherent batch.

    On an empty database, table versions are globally numbered, so per-table
    processing checks cannot use one pending version for every table. This path
    promotes the three canonical tables in dependency order, then validates the
    processing/API layers once against the complete current-version set.
    """

    if audit_date is None:
        audit_date = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    pairs = [(Path(path), table_name) for path, table_name in file_table_pairs]
    tables = {table_name for _, table_name in pairs}
    missing_tables = [table for table in CANONICAL_TABLES if table not in tables]
    if missing_tables:
        raise ExistingDataNotFoundError(
            "Initial discovery requires all three CSVs. Missing: " + ", ".join(missing_tables)
        )

    order = {table: index for index, table in enumerate(CANONICAL_TABLES)}
    pairs.sort(key=lambda item: order.get(item[1], 99))
    detected_vendor = _detect_vendor_from_pairs(pairs)

    reports: list[TrialRunReport] = []
    for csv_path, table_name in pairs:
        reports.append(
            run_trial(
                file_path=str(csv_path),
                table_name=table_name,
                audit_date=audit_date,
                vendor=detected_vendor,
                api_base_url=api_base_url,
                defer_global_checks=True,
                status_callback=status_callback,
            )
        )
        if not reports[-1].all_passed:
            return reports

    if status_callback:
        status_callback("processing", "running")

    final_checks: list[CheckResult] = []
    final_checks.extend(check_processing_layer(None, expected_vendors=[detected_vendor] if detected_vendor else None))
    final_checks.extend(check_api_layer(None, base_url=api_base_url))

    failed = next((check for check in final_checks if not check.passed), None)
    completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    reports.append(
        TrialRunReport(
            table_name="initial_discovery_batch",
            pending_version=None,
            all_passed=failed is None,
            promoted=failed is None,
            rolled_back=False,
            checks=final_checks,
            started_at=reports[0].started_at if reports else completed_at,
            completed_at=completed_at,
            failure_summary=(
                f"{failed.layer}: {failed.check_name} - {failed.message}"
                if failed is not None else None
            ),
        )
    )
    return reports


def rollback(table_name: str, pending_version: int) -> None:
    """
    1. DROP TABLE IF EXISTS {table_name}_v{pending_version}
    2. UPDATE data_versions SET status='trial_failed'
       WHERE table_name=? AND version_id=?
    Uses a raw sqlite3 connection. Does not call any service function.
    """

    from db.connection import get_versioned_table_name, open_database_connection

    versioned_table = get_versioned_table_name(table_name, pending_version)
    conn = open_database_connection()
    try:
        conn.execute(f"DROP TABLE IF EXISTS [{versioned_table}]")
        conn.execute(
            "UPDATE data_versions SET status = ? WHERE table_name = ? AND version_id = ?",
            ("trial_failed", table_name, pending_version),
        )
        conn.commit()
        LOGGER.info("Rolled back %s v%d", table_name, pending_version)
    finally:
        conn.close()


def _promote_pending_version(table_name: str, pending_version: int) -> None:
    """Promote a pending version and keep vendor metadata in sync."""

    from db.connection import promote_current_version, open_database_connection, sync_active_vendors_from_table

    conn = open_database_connection()
    try:
        promote_current_version(table_name, pending_version, connection=conn)
        if table_name == "vendor_overview":
            sync_active_vendors_from_table(pending_version, connection=conn)

        conn.execute(
            "UPDATE data_versions SET status = ? WHERE version_id = ?",
            ("promoted", pending_version),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        from processing.context_builder import clear_context_cache

        clear_context_cache()
    except Exception:
        LOGGER.exception("Failed to clear processing context cache after promotion")


def run_trial(
    file_path: str,
    table_name: str,
    audit_date: str | None = None,
    vendor: str | None = None,
    api_base_url: str | None = None,
    force_promote: bool = False,
    defer_global_checks: bool = False,
    status_callback: Optional[Callable[[str, str], None]] = None,
) -> TrialRunReport:
    """
    Full trial run for one CSV against one table.
    Returns a structured TrialRunReport regardless of pass/fail.
    Raises no exceptions — all failures are captured in the report.
    """

    if audit_date is None:
        audit_date = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    all_checks: list[CheckResult] = []
    pending_version: int | None = None

    try:
        # ── Step 1: Ingest with auto_promote=False ──
        from services.ingestion_service import ingest

        if status_callback:
            status_callback("ingestion", "running")

        ingest_result = ingest(
            filepath=file_path,
            vendor=vendor,  # vendor label for data_versions row
            table_name=table_name,
            audit_date=audit_date,
            auto_promote=False,
        )
        pending_version = ingest_result["version_id"]
        _record_source_path(table_name, pending_version, file_path)
        LOGGER.info("Ingested %s v%d (%d rows)", table_name, pending_version, ingest_result["row_count"])

        if force_promote:
            # Skip all checks — emergency escape hatch
            _promote_pending_version(table_name, pending_version)

            completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            return TrialRunReport(
                table_name=table_name,
                pending_version=pending_version,
                all_passed=True,
                promoted=True,
                rolled_back=False,
                checks=[],
                started_at=started_at,
                completed_at=completed_at,
                failure_summary=None,
            )

        # ── Step 2: Check ingestion ──
        ingestion_checks = check_ingestion(table_name, pending_version)
        all_checks.extend(ingestion_checks)

        if any(not c.passed for c in ingestion_checks):
            first_fail = next(c for c in ingestion_checks if not c.passed)
            rollback(table_name, pending_version)
            completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            return TrialRunReport(
                table_name=table_name,
                pending_version=pending_version,
                all_passed=False,
                promoted=False,
                rolled_back=True,
                checks=all_checks,
                started_at=started_at,
                completed_at=completed_at,
                failure_summary=f"ingestion: {first_fail.check_name} — {first_fail.message}",
            )

        # ── Step 3: Check service layer ──
        if status_callback:
            status_callback("service", "running")

        # Detect vendors in the pending data to ensure checks are calibrated to the actual upload
        from db.connection import open_database_connection, get_vendors_in_pending_version
        conn = open_database_connection()
        try:
            detected_vendors = get_vendors_in_pending_version(table_name, pending_version, conn)
        finally:
            conn.close()

        # If a specific vendor was targeted, only check that one. 
        # Otherwise, check all vendors discovered in this upload.
        expected_vendors = [vendor] if vendor else detected_vendors
        
        service_checks = check_service_layer(table_name, pending_version, expected_vendors=expected_vendors)
        all_checks.extend(service_checks)

        if any(not c.passed for c in service_checks):
            first_fail = next(c for c in service_checks if not c.passed)
            rollback(table_name, pending_version)
            completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            return TrialRunReport(
                table_name=table_name,
                pending_version=pending_version,
                all_passed=False,
                promoted=False,
                rolled_back=True,
                checks=all_checks,
                started_at=started_at,
                completed_at=completed_at,
                failure_summary=f"service: {first_fail.check_name} — {first_fail.message}",
            )

        # ── Step 4: Check processing layer ──
        if defer_global_checks:
            _promote_pending_version(table_name, pending_version)
            completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            return TrialRunReport(
                table_name=table_name,
                pending_version=pending_version,
                all_passed=True,
                promoted=True,
                rolled_back=False,
                checks=all_checks,
                started_at=started_at,
                completed_at=completed_at,
                failure_summary=None,
            )

        if status_callback:
            status_callback("processing", "running")

        processing_checks = check_processing_layer(pending_version, expected_vendors=expected_vendors)
        all_checks.extend(processing_checks)

        if any(not c.passed for c in processing_checks):
            first_fail = next(c for c in processing_checks if not c.passed)
            rollback(table_name, pending_version)
            completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            return TrialRunReport(
                table_name=table_name,
                pending_version=pending_version,
                all_passed=False,
                promoted=False,
                rolled_back=True,
                checks=all_checks,
                started_at=started_at,
                completed_at=completed_at,
                failure_summary=f"processing: {first_fail.check_name} — {first_fail.message}",
            )

        # ── Step 5: Check API layer (graceful skip) ──
        api_checks = check_api_layer(pending_version, base_url=api_base_url)
        all_checks.extend(api_checks)

        if any(not c.passed for c in api_checks):
            first_fail = next(c for c in api_checks if not c.passed)
            rollback(table_name, pending_version)
            completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            return TrialRunReport(
                table_name=table_name,
                pending_version=pending_version,
                all_passed=False,
                promoted=False,
                rolled_back=True,
                checks=all_checks,
                started_at=started_at,
                completed_at=completed_at,
                failure_summary=f"api: {first_fail.check_name} — {first_fail.message}",
            )

        # ── ALL PASS → promote ──
        _promote_pending_version(table_name, pending_version)

        # ── Portfolio export for newly onboarded vendors ──
        if table_name == "vendor_overview":
            try:
                from services.portfolio_export_service import write_new_contracts_to_portfolio

                import sqlite3 as _sqlite3
                _export_conn = open_database_connection()
                try:
                    _export_conn.row_factory = _sqlite3.Row
                    _vt = f"vendor_overview_v{pending_version}"
                    _promoted_rows = [
                        dict(r) for r in _export_conn.execute(
                            f"SELECT of_id, contract_event_type FROM [{_vt}]"
                            " WHERE contract_status = 'active'"
                        ).fetchall()
                    ]
                finally:
                    _export_conn.close()

                newly_promoted_of_ids = [
                    row["of_id"]
                    for row in _promoted_rows
                    if row.get("contract_event_type") == "new"
                ]
                if newly_promoted_of_ids:
                    written = write_new_contracts_to_portfolio(
                        new_of_ids=newly_promoted_of_ids,
                    )
                    LOGGER.info("Portfolio export: %d rows written", written)
            except Exception as exc:
                LOGGER.warning("Portfolio export failed but pipeline continues: %s", exc)

        completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return TrialRunReport(
            table_name=table_name,
            pending_version=pending_version,
            all_passed=True,
            promoted=True,
            rolled_back=False,
            checks=all_checks,
            started_at=started_at,
            completed_at=completed_at,
            failure_summary=None,
        )

    except Exception as exc:
        LOGGER.exception("Trial run failed with unhandled exception")
        if pending_version is not None:
            try:
                rollback(table_name, pending_version)
            except Exception:
                LOGGER.exception("Rollback also failed")

        completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return TrialRunReport(
            table_name=table_name,
            pending_version=pending_version,
            all_passed=False,
            promoted=False,
            rolled_back=pending_version is not None,
            checks=all_checks,
            started_at=started_at,
            completed_at=completed_at,
            failure_summary=f"Unhandled exception: {type(exc).__name__} — {exc}",
        )
