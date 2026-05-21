"""Portfolio export service for newly onboarded vendor contracts."""

from __future__ import annotations

import csv
import logging
import os
import traceback
from datetime import date, datetime
from pathlib import Path
from random import randint

from db.connection import open_database_connection

logger = logging.getLogger(__name__)


# ── Configurable defaults ──────────────────────────────────────────────────

DEFAULT_OWNER        = "IT"
DEFAULT_CRITICALITY  = "Medium"
DEFAULT_STAGE        = "Execution"
DEFAULT_APPROVAL     = "Pending"

RENEWAL_FLAG_WARNING  = "Warning"    # days < 90
RENEWAL_FLAG_PLANNING = "Planning"   # 90 <= days <= 180
RENEWAL_FLAG_OK       = "OK"         # > 180

BUDGET_STATUS_NEAR    = "Near Limit"  # spend_pct > 0.85
BUDGET_STATUS_HEALTHY = "Healthy"

MAX_DAYS_IN_STAGE_MIN = 5
MAX_DAYS_IN_STAGE_MAX = 20

# Vendors excluded from portfolio export (case-insensitive).
# These are existing/legacy vendors whose portfolios are managed externally.
EXCLUDED_VENDORS = frozenset({
    "atlassify", "veloxa", "prismly", "nexaflow", "databridge", "cloudora",
})


# ── External schema columns (exact order) ──────────────────────────────────

PORTFOLIO_COLUMNS = [
    "Contract_ID", "License_Type", "Vendor", "Start_Date", "End_Date",
    "Owner", "Criticality", "Days_to_Renewal", "Renewal_Flag",
    "Total_Users", "Active_Users", "Avg_Utilization_Pct",
    "Total_Annual_Budget_USD", "Total_Actual_Spend_USD",
    "Spend%", "Budget_Status", "Total_True_Up_USD",
    "Stages", "Approval_Status", "Max_Days_in_Stage",
]


# ── Date helpers ───────────────────────────────────────────────────────────

def _parse_to_date(date_str: str) -> date:
    """Parse a date string in various formats to a date object.

    Tries YYYY-MM-DD, DD-MM-YYYY, MM-DD-YYYY in order.
    Raises ValueError if none match.
    """
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def _reformat_date(date_str: str) -> str:
    """
    Accepts YYYY-MM-DD, DD-MM-YYYY, or MM-DD-YYYY.
    Returns DD-MM-YYYY.
    Returns original string unchanged if parsing fails — logs a warning.
    """
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            return parsed.strftime("%d-%m-%Y")
        except ValueError:
            continue
    logger.warning("Could not parse date '%s' — returning unchanged", date_str)
    return date_str


# ── Row transformation ─────────────────────────────────────────────────────

def _transform_row(
    contract_row: dict,
    next_contract_id: int,
    audit_date: str,          # always from SAAS_SPEND_AUDIT_DATE in .env
) -> dict:
    # Usage fields (Active_Users, Avg_Utilization_Pct, Total_Actual_Spend_USD,
    # Spend%, Total_True_Up_USD) are set to zero at initial onboarding.
    # These will be populated by external systems once usage data accumulates.

    # Days to renewal
    notice_deadline = contract_row.get("notice_deadline")
    if not notice_deadline or str(notice_deadline).strip() in ("", "None", "nan"):
        fallback = str(contract_row.get("contract_expiry", audit_date)).strip()
        days_to_renewal = (_parse_to_date(fallback) - _parse_to_date(audit_date)).days
    else:
        days_to_renewal = (_parse_to_date(str(notice_deadline).strip()) - _parse_to_date(audit_date)).days

    # Renewal flag
    if days_to_renewal < 90:
        renewal_flag = RENEWAL_FLAG_WARNING
    elif days_to_renewal <= 180:
        renewal_flag = RENEWAL_FLAG_PLANNING
    else:
        renewal_flag = RENEWAL_FLAG_OK

    contracted_seats = int(contract_row["contracted_seats"])
    unit_price = float(contract_row["unit_price"])
    total_annual_budget = round(contracted_seats * unit_price * 12, 2)

    return {
        "Contract_ID": f"C-{next_contract_id}",
        "License_Type": contract_row["sku"],
        "Vendor": contract_row["vendor"],
        "Start_Date": _reformat_date(audit_date),
        "End_Date": _reformat_date(str(contract_row["contract_expiry"])),
        "Owner": DEFAULT_OWNER,
        "Criticality": DEFAULT_CRITICALITY,
        "Days_to_Renewal": days_to_renewal,
        "Renewal_Flag": renewal_flag,
        "Total_Users": contracted_seats,
        "Active_Users": 0,
        "Avg_Utilization_Pct": 0.0,
        "Total_Annual_Budget_USD": total_annual_budget,
        "Total_Actual_Spend_USD": 0.0,
        "Spend%": 0.0,
        "Budget_Status": BUDGET_STATUS_HEALTHY,
        "Total_True_Up_USD": 0.0,
        "Stages": DEFAULT_STAGE,
        "Approval_Status": DEFAULT_APPROVAL,
        "Max_Days_in_Stage": randint(MAX_DAYS_IN_STAGE_MIN, MAX_DAYS_IN_STAGE_MAX),
    }


# ── Main public function ───────────────────────────────────────────────────

def write_new_contracts_to_portfolio(
    new_of_ids: list[str],
    version=None,
) -> int:
    """
    Called after pipeline promotion for newly onboarded vendor contracts.

    Reads SAAS_SPEND_AUDIT_DATE and PORTFOLIO_EXPORT_PATH from environment.
    Fetches promoted contract rows by of_id from the database.
    Transforms each row to the external portfolio schema.
    Appends to PORTFOLIO_EXPORT_PATH CSV.

    Returns count of rows written.
    Returns 0 silently if PORTFOLIO_EXPORT_PATH is not set.
    Returns 0 silently if new_of_ids is empty.
    Creates the CSV with header row if it does not yet exist.
    Never writes duplicate rows — deduplicates by vendor + sku + start_date.
    All errors are non-fatal — the pipeline continues regardless.
    """
    try:
        # ── Step 1 — read env vars ─────────────────────────────────────
        export_path = os.getenv("PORTFOLIO_EXPORT_PATH", "").strip()
        if not export_path:
            logger.warning("PORTFOLIO_EXPORT_PATH not set — skipping portfolio export")
            return 0

        audit_date = os.getenv("SAAS_SPEND_AUDIT_DATE", "").strip()
        if not audit_date:
            logger.warning("SAAS_SPEND_AUDIT_DATE not set — skipping portfolio export")
            return 0

        if not new_of_ids:
            return 0

        # Check that the target directory exists (never create directories)
        export_dir = Path(export_path).parent
        if not export_dir.exists():
            logger.error(
                "Portfolio export directory does not exist: %s — skipping export",
                export_dir,
            )
            return 0

        # ── Step 2 — read existing CSV ─────────────────────────────────
        file_exists = Path(export_path).exists()
        existing_rows: list[dict] = []
        next_id = 1000
        existing_keys: set[tuple[str, str, str]] = set()

        if file_exists:
            try:
                with open(export_path, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    existing_rows = list(reader)
            except Exception as exc:
                logger.error(
                    "Cannot parse existing CSV at %s: %s — skipping export",
                    export_path, exc,
                )
                return 0

            # Find max numeric suffix from Contract_ID column values
            max_id = 0
            for row in existing_rows:
                cid = row.get("Contract_ID", "")
                if cid.startswith("C-"):
                    try:
                        num = int(cid[2:])
                        if num > max_id:
                            max_id = num
                    except ValueError:
                        continue
            if max_id > 0:
                next_id = max_id + 1

            # Build dedup key set
            existing_keys = {
                (
                    row.get("Vendor", "").lower(),
                    row.get("License_Type", "").lower(),
                    row.get("Start_Date", ""),
                )
                for row in existing_rows
            }

        # ── Step 3 — fetch contract rows from DB ──────────────────────
        import sqlite3

        conn = open_database_connection()
        try:
            # Resolve version (same pattern as contract_service.py)
            if version is not None:
                resolved_version = version
            else:
                row = conn.execute(
                    "SELECT current_version FROM current_versions WHERE table_name = ?",
                    ("vendor_overview",),
                ).fetchone()
                if row is None:
                    logger.warning(
                        "No promoted vendor_overview version — skipping portfolio export"
                    )
                    return 0
                resolved_version = int(row[0])

            resolved_table = f"vendor_overview_v{resolved_version}"

            placeholders = ",".join("?" for _ in new_of_ids)
            conn.row_factory = sqlite3.Row
            fetched_rows = [
                dict(r)
                for r in conn.execute(
                    f"SELECT * FROM [{resolved_table}]"
                    f" WHERE of_id IN ({placeholders})"
                    f" AND contract_status = 'active'",
                    new_of_ids,
                ).fetchall()
            ]
        finally:
            conn.close()

        # ── Step 4 — transform and deduplicate ────────────────────────
        new_rows: list[dict] = []

        for contract_row in fetched_rows:
            vendor_name = str(contract_row.get("vendor", "")).strip()

            # Skip excluded vendors (case-insensitive)
            if vendor_name.lower() in EXCLUDED_VENDORS:
                logger.debug(
                    "Skipping excluded vendor %s (of_id=%s)",
                    vendor_name,
                    contract_row.get("of_id"),
                )
                continue

            # Validate required fields
            if (
                contract_row.get("unit_price") is None
                or str(contract_row.get("unit_price", "")).strip() in ("", "None", "nan")
            ):
                logger.warning(
                    "Skipping contract row of_id=%s: missing unit_price",
                    contract_row.get("of_id"),
                )
                continue

            if (
                contract_row.get("contracted_seats") is None
                or str(contract_row.get("contracted_seats", "")).strip() in ("", "None", "nan")
            ):
                logger.warning(
                    "Skipping contract row of_id=%s: missing contracted_seats",
                    contract_row.get("of_id"),
                )
                continue

            dedup_key = (
                vendor_name.lower(),
                str(contract_row.get("sku", "")).lower(),
                _reformat_date(audit_date),
            )
            if dedup_key in existing_keys:
                logger.debug("Skipping duplicate: %s", dedup_key)
                continue

            transformed = _transform_row(contract_row, next_id, audit_date)
            new_rows.append(transformed)
            existing_keys.add(dedup_key)
            next_id += 1

        if not new_rows:
            logger.info("Portfolio export: no new rows to write")
            return 0

        # ── Step 5 — write ─────────────────────────────────────────────
        mode = "a" if file_exists else "w"
        with open(export_path, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=PORTFOLIO_COLUMNS, extrasaction="ignore",
            )
            if mode == "w":
                writer.writeheader()
            writer.writerows(new_rows)

        # ── Step 6 — return ────────────────────────────────────────────
        logger.info(
            "Portfolio export: %d rows written to %s", len(new_rows), export_path,
        )
        return len(new_rows)

    except Exception:
        logger.error(
            "Portfolio export failed with unexpected error:\n%s",
            traceback.format_exc(),
        )
        return 0
