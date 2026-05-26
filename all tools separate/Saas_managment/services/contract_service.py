"""Contract service queries for Phase 1B."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
import logging
from typing import Optional

from db.connection import get_connection
from exceptions import DataNotReadyError

DATE_COLUMNS = {"contract_start", "contract_expiry", "notice_deadline"}
BOOL_COLUMNS = {"auto_renewal", "true_down_rights"}
LOGGER = logging.getLogger(__name__)


def _get_active_vendors() -> list[str]:
    """Resolve active vendors dynamically from environment."""
    return [v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()]


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


def _to_bool(value: object) -> bool:
    return bool(value)


def _connection(table_name: str, version: Optional[int]) -> tuple[sqlite3.Connection, int]:
    connection, resolved_version = get_connection(table_name, version)
    connection.row_factory = sqlite3.Row
    return connection, resolved_version


# DEPRECATED: resolved version now comes from get_connection


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


def _normalize_contract_row(row: sqlite3.Row) -> dict:
    payload = dict(row)
    for key in DATE_COLUMNS:
        payload[key] = _to_date(payload.get(key))
    for key in BOOL_COLUMNS:
        payload[key] = _to_bool(payload.get(key))
    return payload


def _text_sort_value(value: object) -> str:
    """Return a stable sortable string for nullable text fields."""

    return "" if value is None else str(value)


def _validate_dedup(rows: list[dict]) -> None:
    keys = [(row["vendor"], row["sku"], row["seat_type"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate vendor+sku+seat_type rows returned from get_entitlement")


def get_entitlement(vendor: Optional[str] = None, version: Optional[int] = None) -> list[dict]:
    """Return the active entitlement grain for true-up math."""

    vendor_clause, params = _vendor_filter(vendor)
    connection, table_version = _connection("vendor_overview", version)
    try:
        query = f"""
            WITH dedup AS (
                SELECT MAX(of_id) AS of_id
                FROM vendor_overview_v{table_version}
                WHERE contract_status = 'active'
                  AND {vendor_clause}
                GROUP BY vendor, sku, seat_type
            )
            SELECT
                vendor,
                sku,
                seat_type,
                effective_total_seats,
                unit_price,
                notice_deadline,
                auto_renewal,
                true_down_rights,
                measurement_method,
                contract_status
            FROM vendor_overview_v{table_version} AS v
            WHERE v.of_id IN (SELECT of_id FROM dedup)
            ORDER BY vendor, sku, seat_type
        """
        rows = [
            row for row in (
                _normalize_contract_row(row)
                for row in connection.execute(query, params).fetchall()
            )
            if row.get("vendor") and row.get("sku") and row.get("seat_type")
            and row.get("effective_total_seats", 0) > 0   # skip zero-seat rows
        ]
    finally:
        connection.close()

    _validate_dedup(rows)
    if not rows and vendor is None:
        raise DataNotReadyError("No active entitlement rows are available.")
    return [
        {
            key: value
            for key, value in row.items()
            if key
            in {
                "vendor",
                "sku",
                "seat_type",
                "effective_total_seats",
                "unit_price",
                "notice_deadline",
                "auto_renewal",
                "true_down_rights",
                "measurement_method",
                "contract_status",
            }
        }
        for row in rows
    ]


def get_active_contracts(vendor: Optional[str] = None, version: Optional[int] = None) -> list[dict]:
    """Return all active order forms including parallel chains."""

    vendor_clause, params = _vendor_filter(vendor)
    connection, table_version = _connection("vendor_overview", version)
    try:
        query = f"""
            SELECT
                of_id,
                vendor,
                sku,
                seat_type,
                contracted_seats,
                effective_total_seats,
                unit_price,
                contract_start,
                contract_expiry,
                notice_deadline,
                auto_renewal,
                true_down_rights,
                measurement_method,
                contract_event_type,
                contract_group_id,
                contract_status
            FROM vendor_overview_v{table_version}
            WHERE contract_status = 'active'
              AND {vendor_clause}
            ORDER BY vendor, sku, seat_type, contract_start
        """
        rows = [_normalize_contract_row(row) for row in connection.execute(query, params).fetchall()]
    finally:
        connection.close()

    deduped: list[dict] = []
    seen_of_ids: set[str] = set()
    for row in rows:
        if row["of_id"] in seen_of_ids:
            continue
        seen_of_ids.add(row["of_id"])
        deduped.append(row)

    deduped.sort(key=lambda row: _to_date(row["contract_start"]) or date.min)

    if any(row["contract_status"] != "active" for row in deduped):
        raise ValueError("get_active_contracts returned non-active rows")
    if len({row["of_id"] for row in deduped}) != len(deduped):
        raise ValueError("Duplicate of_id values returned from get_active_contracts")
    return [
        {
            key: value
            for key, value in row.items()
            if key
            in {
                "of_id",
                "vendor",
                "sku",
                "seat_type",
                "contracted_seats",
                "effective_total_seats",
                "unit_price",
                "contract_start",
                "contract_expiry",
                "notice_deadline",
                "auto_renewal",
                "true_down_rights",
                "measurement_method",
                "contract_event_type",
                "contract_group_id",
            }
        }
        for row in deduped
    ]


def get_contract_history(
    vendor: Optional[str] = None,
    version: Optional[int] = None,
    sku: Optional[str] = None,
    seat_type: Optional[str] = None,
) -> list[dict]:
    """
    Return all order forms regardless of contract_status.

    Optional vendor filter narrows to a single active vendor. Optional sku and
    seat_type filters are retained for existing callers that inspect a single
    contract chain.
    """

    connection, table_version = _connection("vendor_overview", version)
    try:
        filters = ["(? IS NULL OR vendor = ?)"]
        params: list[object] = [vendor, vendor]
        if sku is not None:
            filters.append("sku = ?")
            params.append(sku)
        if seat_type is not None:
            filters.append("seat_type = ?")
            params.append(seat_type)
        where_clause = " AND ".join(filters)
        query = f"""
            SELECT
                of_id,
                vendor,
                sku,
                seat_type,
                contracted_seats,
                effective_total_seats,
                unit_price,
                contract_start,
                contract_expiry,
                contract_status,
                contract_event_type,
                predecessor_of_id,
                seat_delta,
                contract_group_id
            FROM vendor_overview_v{table_version}
            WHERE {where_clause}
            ORDER BY vendor, sku, seat_type, contract_start ASC
        """
        rows = [_normalize_contract_row(row) for row in connection.execute(query, params).fetchall()]
    finally:
        connection.close()

    rows.sort(
        key=lambda row: (
            _text_sort_value(row.get("vendor")),
            _text_sort_value(row.get("sku")),
            _text_sort_value(row.get("seat_type")),
            _to_date(row["contract_start"]) or date.min,
        )
    )

    if not rows:
        raise DataNotReadyError("No contract history found.")
    return [
        {
            key: value
            for key, value in row.items()
            if key
            in {
                "of_id",
                "vendor",
                "sku",
                "seat_type",
                "contracted_seats",
                "effective_total_seats",
                "unit_price",
                "contract_start",
                "contract_expiry",
                "contract_status",
                "contract_event_type",
                "predecessor_of_id",
                "seat_delta",
                "contract_group_id",
            }
        }
        for row in rows
    ]
