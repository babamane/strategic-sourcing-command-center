"""Employee service queries for Phase 1B."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
import logging
from typing import Optional

from db.connection import get_connection
from exceptions import DataNotReadyError
from services.ingestion_service import get_discovered_values, get_last_ingested_count

LOGGER = logging.getLogger(__name__)


def _connection(table_name: str, version: Optional[int]) -> tuple[sqlite3.Connection, int]:
    connection, resolved_version = get_connection(table_name, version)
    connection.row_factory = sqlite3.Row
    return connection, resolved_version


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
    if "is_active" in payload:
        payload["is_active"] = _to_bool(payload["is_active"])
    for key in ("hire_date", "exit_date"):
        if key in payload:
            payload[key] = _to_date(payload[key])
    return payload


def _get_known_departments() -> list[str]:
    """Read discovered department values from vendor_profiles."""

    values = get_discovered_values("hr_headcount", "department")
    if not values:
        LOGGER.warning(
            "No discovered department values in vendor_profiles; headcount keys may be incomplete"
        )
    return values


def _get_allowed_exit_types() -> set[str]:
    """Read discovered exit_type values from vendor_profiles."""

    values = get_discovered_values("hr_headcount", "exit_type")
    if not values:
        LOGGER.warning("No discovered exit_type values in vendor_profiles")
    return set(values)


def _check_row_count(
    table_name: str,
    actual: int,
    threshold: float = float(os.getenv("ROW_COUNT_DEVIATION_THRESHOLD", "0.05")),
) -> None:
    """Warn when a row count deviates materially from the latest ingest."""

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


def get_active_employees(version: Optional[int] = None) -> list[dict]:
    """Return all currently employed employees."""

    connection, table_version = _connection("hr_headcount", version)
    try:
        rows = [
            _normalize_row(row)
            for row in connection.execute(
                f"""
                SELECT
                    employee_id,
                    email,
                    department,
                    sub_team,
                    job_level,
                    region,
                    is_active,
                    hire_date
                FROM hr_headcount_v{table_version}
                WHERE is_active = 1
                ORDER BY employee_id
                """
            ).fetchall()
        ]
    finally:
        connection.close()

    if any(not row["is_active"] for row in rows):
        raise ValueError("get_active_employees returned inactive rows")
    #_check_row_count("hr_headcount", len(rows))
    return rows


def get_exited_employees(version: Optional[int] = None) -> list[dict]:
    """Return all exited employees."""

    connection, table_version = _connection("hr_headcount", version)
    try:
        rows = [
            _normalize_row(row)
            for row in connection.execute(
                f"""
                SELECT
                    employee_id,
                    email,
                    department,
                    sub_team,
                    job_level,
                    region,
                    is_active,
                    exit_date,
                    exit_type
                FROM hr_headcount_v{table_version}
                WHERE employee_status = 'exited'
                ORDER BY exit_date DESC
                """
            ).fetchall()
        ]
    finally:
        connection.close()

    if any(row["is_active"] for row in rows):
        raise ValueError("get_exited_employees returned active rows")
    if any(row["exit_date"] is None for row in rows):
        raise ValueError("get_exited_employees returned null exit_date values")
    allowed_exit_types = _get_allowed_exit_types()
    if allowed_exit_types:
        for row in rows:
            exit_type = row.get("exit_type")
            if exit_type is not None and exit_type not in allowed_exit_types:
                LOGGER.warning("Unexpected exit_type value %r", exit_type)
    return rows


def get_future_hires(
    department: Optional[str] = None,
    before_date: Optional[date] = None,
    version: Optional[int] = None,
) -> list[dict]:
    """Return all future hires in the pre-hire window."""

    connection, table_version = _connection("hr_headcount", version)
    try:
        rows = [
            _normalize_row(row)
            for row in connection.execute(
                f"""
                SELECT
                    employee_id,
                    email,
                    department,
                    sub_team,
                    job_level,
                    region,
                    hire_date,
                    employee_status
                FROM hr_headcount_v{table_version}
                WHERE employee_status = 'pre-hire'
                ORDER BY hire_date, employee_id
                """
            ).fetchall()
        ]
    finally:
        connection.close()

    filtered: list[dict] = []
    for row in rows:
        if department is not None and row["department"] != department:
            continue
        if before_date is not None and row["hire_date"] is not None and row["hire_date"] > before_date:
            continue
        filtered.append(
            {
                key: row[key]
                for key in [
                    "employee_id",
                    "email",
                    "department",
                    "sub_team",
                    "job_level",
                    "region",
                    "hire_date",
                    "employee_status",
                ]
            }
        )
    return filtered


def get_employee_by_email(email: str, version: Optional[int] = None) -> dict:
    """Return a single employee record by email."""

    connection, table_version = _connection("hr_headcount", version)
    try:
        row = connection.execute(
            f"""
            SELECT
                employee_id,
                email,
                department,
                job_level,
                region,
                is_active,
                hire_date,
                exit_date,
                exit_type,
                manager_id
            FROM hr_headcount_v{table_version}
            WHERE email = ?
            LIMIT 1
            """,
            (email,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise DataNotReadyError(f"No employee record found for email: {email}")
    payload = _normalize_row(row)
    return {
        key: payload.get(key)
        for key in [
            "employee_id",
            "email",
            "department",
            "job_level",
            "region",
            "is_active",
            "hire_date",
            "exit_date",
            "exit_type",
            "manager_id",
        ]
    }


def get_department_headcount(version: Optional[int] = None) -> dict:
    """Return active headcount grouped by department."""

    connection, table_version = _connection("hr_headcount", version)
    try:
        rows = connection.execute(
            f"""
            SELECT
                department,
                COUNT(*) AS headcount
            FROM hr_headcount_v{table_version}
            WHERE is_active = 1
            GROUP BY department
            ORDER BY headcount DESC
            """
        ).fetchall()
    finally:
        connection.close()

    counts = {department: 0 for department in _get_known_departments()}
    for row in rows:
        counts[row["department"]] = int(row["headcount"])
    return counts
