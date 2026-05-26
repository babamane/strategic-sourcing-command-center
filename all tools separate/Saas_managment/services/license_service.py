"""License service queries for Phase 1B redefined services."""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import date, datetime
from typing import Optional

from db.connection import get_connection
from exceptions import DataNotReadyError
from services.ingestion_service import get_last_ingested_count

LOGGER = logging.getLogger(__name__)


def _get_active_vendors() -> list[str]:
    """Resolve active vendors dynamically from environment."""
    return [v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()]


def _connection(table_name: str, version: Optional[int]) -> tuple[sqlite3.Connection, int]:
    connection, resolved_version = get_connection(table_name, version)
    connection.row_factory = sqlite3.Row
    return connection, resolved_version


# DEPRECATED: resolved version now comes from get_connection


def _to_bool(value: object) -> bool:
    return bool(value)


def _to_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value)
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date value: {value!r}")


def _normalize_row(row: sqlite3.Row) -> dict:
    payload = dict(row)
    for key in ("reclamation_candidate", "auto_renewal", "true_down_rights"):
        if key in payload:
            payload[key] = _to_bool(payload[key])
    for key in ("notice_deadline", "provisioned_date", "effective_license_date", "last_active_date"):
        if key in payload:
            payload[key] = _to_date(payload[key])
    return payload


def _vendor_filter(vendor: Optional[str]) -> tuple[str, list[object]]:
    active_vendors = _get_active_vendors()
    if vendor is None:
        if not active_vendors:
            # No ACTIVE_VENDORS configured — return all rows
            return "1=1", []
        placeholders = ",".join("?" for _ in active_vendors)
        return f"vendor IN ({placeholders})", list(active_vendors)
    if active_vendors and vendor not in set(active_vendors):
        raise ValueError(f"Unsupported vendor: {vendor}")
    return "vendor = ?", [vendor]


def _check_row_count(
    table_name: str,
    actual: int,
    threshold: float = float(os.getenv("ROW_COUNT_DEVIATION_THRESHOLD", "0.05")),
) -> None:
    expected = get_last_ingested_count(table_name)
    if expected is None:
        LOGGER.warning("No ingested count found for %s; skipping row count check", table_name)
        return
    deviation = abs(actual - expected) / max(expected, 1)
    if deviation > threshold:
        LOGGER.warning(
            "Row count deviation for %s: expected ~%s, got %s (%.1f%% deviation; threshold %.0f%%)",
            table_name,
            expected,
            actual,
            deviation * 100,
            threshold * 100,
        )


def get_raw_licenses(
    vendor: Optional[str] = None,
    status_filter: Optional[list[str]] = None,
    version: Optional[int] = None,
    include_effective_license_date: bool = False,
) -> list[dict]:
    """Return raw license rows with optional vendor and status filtering."""

    vendor_clause, vendor_params = _vendor_filter(vendor)
    status_clause = ""
    status_params: list[object] = []
    if status_filter is not None:
        normalized_statuses = [status for status in status_filter if status]
        if not normalized_statuses:
            return []
        placeholders = ",".join("?" for _ in normalized_statuses)
        status_clause = f" AND license_status IN ({placeholders})"
        status_params = normalized_statuses

    connection, table_version = _connection("license_utilization", version)
    try:
        query = f"""
            SELECT
                license_id,
                vendor,
                sku,
                seat_type,
                assigned_email,
                employee_id,
                department,
                job_level,
                provisioned_date,
                effective_license_date,
                last_active_date,
                license_status,
                usage_tier,
                seat_tier_match,
                monthly_cost,
                cost_at_risk,
                annual_cost,
                active_usage_rate,
                login_events_30d,
                days_since_last_active,
                days_since_provisioned,
                contract_days_remaining,
                days_until_notice,
                renewal_urgency,
                notice_deadline,
                auto_renewal,
                true_down_rights,
                measurement_method,
                current_of_id,
                of_id,
                reclamation_candidate,
                churn_risk_score
            FROM license_utilization_v{table_version}
            WHERE {vendor_clause}
              {status_clause}
            ORDER BY vendor, sku, seat_type, license_id
        """
        rows = [_normalize_row(row) for row in connection.execute(query, [*vendor_params, *status_params]).fetchall()]
    finally:
        connection.close()

    if not include_effective_license_date:
        for row in rows:
            row.pop("effective_license_date", None)

    if not rows and vendor is None and status_filter is None:
        raise DataNotReadyError("No raw license rows are available.")

    if vendor is None and status_filter is None:
        _check_row_count("license_utilization", len(rows))

    return rows
