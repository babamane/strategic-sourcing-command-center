"""Tests for services.portfolio_export_service."""

from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Helper: build a mock DB connection with a vendor_overview table ────────

def _build_mock_db(rows: list[dict], version: int = 1):
    """Return a patched open_database_connection that yields an in-memory DB."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE current_versions (
            table_name TEXT PRIMARY KEY,
            current_version INTEGER NOT NULL,
            promoted_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO current_versions VALUES (?, ?, ?)",
        ("vendor_overview", version, "2026-05-01T00:00:00"),
    )

    table_name = f"vendor_overview_v{version}"
    if rows:
        columns = list(rows[0].keys())
        col_defs = ", ".join(f"{c} TEXT" for c in columns)
        conn.execute(f"CREATE TABLE [{table_name}] ({col_defs})")
        placeholders = ", ".join("?" for _ in columns)
        for row in rows:
            conn.execute(
                f"INSERT INTO [{table_name}] ({', '.join(columns)}) VALUES ({placeholders})",
                [str(row[c]) if row[c] is not None else None for c in columns],
            )
    else:
        conn.execute(
            f"CREATE TABLE [{table_name}] "
            "(of_id TEXT, vendor TEXT, sku TEXT, seat_type TEXT, "
            "contracted_seats TEXT, unit_price TEXT, contract_start TEXT, "
            "contract_expiry TEXT, notice_deadline TEXT, contract_status TEXT, "
            "contract_event_type TEXT)"
        )
    conn.commit()
    return conn


def _make_contract_row(
    of_id="V4-OF-006",
    vendor="OpenAI",
    sku="Codex",
    seat_type="Full",
    contracted_seats="200",
    unit_price="10.77",
    contract_start="01-05-2026",
    contract_expiry="01-05-2027",
    notice_deadline="02-12-2026",
    contract_status="active",
    contract_event_type="new",
):
    return {
        "of_id": of_id,
        "vendor": vendor,
        "sku": sku,
        "seat_type": seat_type,
        "contracted_seats": contracted_seats,
        "unit_price": unit_price,
        "contract_start": contract_start,
        "contract_expiry": contract_expiry,
        "notice_deadline": notice_deadline,
        "contract_status": contract_status,
        "contract_event_type": contract_event_type,
    }


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_export_path(tmp_path):
    return str(tmp_path / "test_portfolio.csv")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure portfolio env vars are cleared before each test."""
    monkeypatch.delenv("PORTFOLIO_EXPORT_PATH", raising=False)
    monkeypatch.delenv("SAAS_SPEND_AUDIT_DATE", raising=False)


# ── Tests ──────────────────────────────────────────────────────────────────


def test_creates_file_with_header_when_missing(monkeypatch, tmp_export_path):
    """CSV is created with correct headers when the file doesn't exist."""
    from services.portfolio_export_service import PORTFOLIO_COLUMNS

    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    row = _make_contract_row()
    conn = _build_mock_db([row])
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 1
    assert Path(tmp_export_path).exists()

    with open(tmp_export_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert list(reader.fieldnames) == PORTFOLIO_COLUMNS
        data_rows = list(reader)
        assert len(data_rows) == 1


def test_appends_to_existing_file_no_duplicate_header(monkeypatch, tmp_export_path):
    """Appending to an existing CSV does not duplicate the header row."""
    from services.portfolio_export_service import PORTFOLIO_COLUMNS

    # Create existing file with one row
    with open(tmp_export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PORTFOLIO_COLUMNS)
        writer.writeheader()
        writer.writerow({
            "Contract_ID": "C-1000", "License_Type": "GPT-4", "Vendor": "SomeVendor",
            "Start_Date": "01-01-2026", "End_Date": "01-01-2027", "Owner": "IT",
            "Criticality": "Medium", "Days_to_Renewal": "100", "Renewal_Flag": "Planning",
            "Total_Users": "50", "Active_Users": "0", "Avg_Utilization_Pct": "0.0",
            "Total_Annual_Budget_USD": "6000.0", "Total_Actual_Spend_USD": "0.0",
            "Spend%": "0.0", "Budget_Status": "Healthy", "Total_True_Up_USD": "0.0",
            "Stages": "Execution", "Approval_Status": "Pending", "Max_Days_in_Stage": "10",
        })

    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    row = _make_contract_row()
    conn = _build_mock_db([row])
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 1

    with open(tmp_export_path, newline="", encoding="utf-8") as f:
        lines = f.readlines()
    # One header + two data rows = 3 lines
    assert len(lines) == 3
    # Header appears only once
    assert lines[0].startswith("Contract_ID,")

    with open(tmp_export_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data_rows = list(reader)
    assert len(data_rows) == 2
    assert data_rows[1]["Contract_ID"] == "C-1001"


def test_skips_duplicate_by_vendor_sku_start_date(monkeypatch, tmp_export_path):
    """Duplicate rows (same vendor+sku+start_date) are not written."""
    from services.portfolio_export_service import PORTFOLIO_COLUMNS

    # Existing row with matching dedup key
    with open(tmp_export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PORTFOLIO_COLUMNS)
        writer.writeheader()
        writer.writerow({
            "Contract_ID": "C-1000", "License_Type": "Codex", "Vendor": "OpenAI",
            "Start_Date": "01-05-2026", "End_Date": "01-05-2027", "Owner": "IT",
            "Criticality": "Medium", "Days_to_Renewal": "215", "Renewal_Flag": "OK",
            "Total_Users": "200", "Active_Users": "0", "Avg_Utilization_Pct": "0.0",
            "Total_Annual_Budget_USD": "25848.0", "Total_Actual_Spend_USD": "0.0",
            "Spend%": "0.0", "Budget_Status": "Healthy", "Total_True_Up_USD": "0.0",
            "Stages": "Execution", "Approval_Status": "Pending", "Max_Days_in_Stage": "10",
        })

    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    row = _make_contract_row()
    conn = _build_mock_db([row])
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 0


def test_returns_zero_when_path_not_set(monkeypatch, tmp_export_path):
    """Returns 0 silently when PORTFOLIO_EXPORT_PATH is empty."""
    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", "")
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 0
    assert not Path(tmp_export_path).exists()


def test_returns_zero_when_audit_date_not_set(monkeypatch, tmp_export_path):
    """Returns 0 silently when SAAS_SPEND_AUDIT_DATE is empty."""
    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "")

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 0


def test_field_mapping_openai_codex(monkeypatch, tmp_export_path):
    """Full field mapping verification for an OpenAI Codex contract row."""
    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    row = _make_contract_row(
        of_id="V4-OF-006",
        vendor="OpenAI",
        sku="Codex",
        seat_type="Full",
        contracted_seats="200",
        unit_price="10.77",
        contract_start="01-05-2026",
        contract_expiry="01-05-2027",
        notice_deadline="02-12-2026",
        contract_status="active",
        contract_event_type="new",
    )
    conn = _build_mock_db([row])
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 1

    with open(tmp_export_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data_rows = list(reader)
    assert len(data_rows) == 1
    row_data = data_rows[0]

    assert row_data["Vendor"] == "OpenAI"
    assert row_data["License_Type"] == "Codex"
    assert row_data["Start_Date"] == "01-05-2026"       # audit date, not contract_start
    assert row_data["End_Date"] == "01-05-2027"
    assert int(row_data["Total_Users"]) == 200
    assert float(row_data["Total_Annual_Budget_USD"]) == 25848.0  # 200 * 10.77 * 12
    assert int(row_data["Active_Users"]) == 0
    assert float(row_data["Avg_Utilization_Pct"]) == 0.0
    assert float(row_data["Total_Actual_Spend_USD"]) == 0.0
    assert float(row_data["Spend%"]) == 0.0
    assert float(row_data["Total_True_Up_USD"]) == 0.0
    assert row_data["Budget_Status"] == "Healthy"
    assert int(row_data["Days_to_Renewal"]) == 215  # date(2026,12,2) - date(2026,5,1)
    assert row_data["Renewal_Flag"] == "OK"          # 215 > 180
    assert row_data["Owner"] == "IT"
    assert row_data["Criticality"] == "Medium"
    assert row_data["Stages"] == "Execution"
    assert row_data["Approval_Status"] == "Pending"
    assert 5 <= int(row_data["Max_Days_in_Stage"]) <= 20


def test_skips_row_with_missing_unit_price(monkeypatch, tmp_export_path):
    """Rows with missing unit_price are skipped gracefully."""
    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    row = _make_contract_row(unit_price=None)
    conn = _build_mock_db([row])
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 0


def test_skips_row_with_missing_contracted_seats(monkeypatch, tmp_export_path):
    """Rows with missing contracted_seats are skipped gracefully."""
    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    row = _make_contract_row(contracted_seats=None)
    conn = _build_mock_db([row])
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 0


def test_handles_missing_directory_gracefully(monkeypatch):
    """Returns 0 when export path directory does not exist."""
    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", "/nonexistent/dir/file.csv")
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    assert result == 0


def test_contract_id_increments_from_existing_max(monkeypatch, tmp_export_path):
    """New Contract_IDs increment from the max existing ID, not sequentially."""
    from services.portfolio_export_service import PORTFOLIO_COLUMNS

    # Create existing file with non-sequential IDs: C-1000, C-1001, C-1004
    with open(tmp_export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PORTFOLIO_COLUMNS)
        writer.writeheader()
        for cid in ("C-1000", "C-1001", "C-1004"):
            writer.writerow({
                "Contract_ID": cid, "License_Type": f"SKU-{cid}", "Vendor": f"Vendor-{cid}",
                "Start_Date": "01-01-2026", "End_Date": "01-01-2027", "Owner": "IT",
                "Criticality": "Medium", "Days_to_Renewal": "100", "Renewal_Flag": "Planning",
                "Total_Users": "50", "Active_Users": "0", "Avg_Utilization_Pct": "0.0",
                "Total_Annual_Budget_USD": "6000.0", "Total_Actual_Spend_USD": "0.0",
                "Spend%": "0.0", "Budget_Status": "Healthy", "Total_True_Up_USD": "0.0",
                "Stages": "Execution", "Approval_Status": "Pending", "Max_Days_in_Stage": "10",
            })

    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    rows = [
        _make_contract_row(of_id="V4-OF-010", vendor="NewVendorA", sku="PlanA"),
        _make_contract_row(of_id="V4-OF-011", vendor="NewVendorB", sku="PlanB"),
    ]
    conn = _build_mock_db(rows)
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(new_of_ids=["V4-OF-010", "V4-OF-011"])
    assert result == 2

    with open(tmp_export_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data_rows = list(reader)
    assert len(data_rows) == 5  # 3 existing + 2 new
    new_ids = [r["Contract_ID"] for r in data_rows[3:]]
    assert new_ids == ["C-1005", "C-1006"]


def test_pipeline_continues_when_export_path_directory_missing(monkeypatch):
    """Runner-level try/except ensures pipeline continues even on unexpected failure."""
    from services.portfolio_export_service import write_new_contracts_to_portfolio

    # Simulate the runner-level safety net
    caught = False
    try:
        # Force an unexpected exception inside the function
        with patch(
            "services.portfolio_export_service.os.getenv",
            side_effect=RuntimeError("Simulated unexpected failure"),
        ):
            write_new_contracts_to_portfolio(new_of_ids=["V4-OF-006"])
    except Exception:
        caught = True

    # The function itself catches all exceptions, so nothing should propagate
    assert not caught


def test_excludes_legacy_vendors_case_insensitive(monkeypatch, tmp_export_path):
    """Vendors in the EXCLUDED_VENDORS set are skipped regardless of case."""
    monkeypatch.setenv("PORTFOLIO_EXPORT_PATH", tmp_export_path)
    monkeypatch.setenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    rows = [
        _make_contract_row(of_id="V1-OF-001", vendor="Atlassify", sku="Jira"),
        _make_contract_row(of_id="V2-OF-001", vendor="NEXAFLOW", sku="Flow"),
        _make_contract_row(of_id="V3-OF-001", vendor="cloudora", sku="Cloud"),
        _make_contract_row(of_id="V4-OF-006", vendor="OpenAI", sku="Codex"),
    ]
    conn = _build_mock_db(rows)
    monkeypatch.setattr(
        "services.portfolio_export_service.open_database_connection",
        lambda: conn,
    )

    from services.portfolio_export_service import write_new_contracts_to_portfolio

    result = write_new_contracts_to_portfolio(
        new_of_ids=["V1-OF-001", "V2-OF-001", "V3-OF-001", "V4-OF-006"],
    )
    # Only OpenAI should be written; Atlassify, NEXAFLOW, cloudora are excluded
    assert result == 1

    with open(tmp_export_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data_rows = list(reader)
    assert len(data_rows) == 1
    assert data_rows[0]["Vendor"] == "OpenAI"
