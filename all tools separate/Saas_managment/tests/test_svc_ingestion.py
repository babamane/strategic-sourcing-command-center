import pytest

from services import employee_service
from services.ingestion_service import get_discovered_values, get_last_ingested_count


def test_get_discovered_values_departments_not_empty():
    values = get_discovered_values("hr_headcount", "department")
    assert values


def test_get_discovered_values_departments_are_strings():
    values = get_discovered_values("hr_headcount", "department")
    assert all(isinstance(value, str) for value in values)


def test_get_discovered_values_departments_count():
    values = get_discovered_values("hr_headcount", "department")
    assert len(set(values)) == 8


def test_get_discovered_values_exit_types_not_empty():
    values = get_discovered_values("hr_headcount", "exit_type")
    assert values


def test_get_discovered_values_exit_types_known_values():
    values = set(get_discovered_values("hr_headcount", "exit_type"))
    assert {"voluntary", "layoff", "performance", "retirement"}.issubset(values)


def test_get_discovered_values_job_levels():
    values = set(get_discovered_values("hr_headcount", "job_level"))
    assert {f"L{i}" for i in range(1, 8)}.issubset(values)


def test_get_discovered_values_seat_types():
    values = set(get_discovered_values("vendor_overview", "seat_type"))
    assert {"Full", "Contributor", "Collaborator"}.issubset(values)


def test_get_discovered_values_contract_status():
    values = set(get_discovered_values("vendor_overview", "contract_status"))
    assert {"active", "superseded"}.issubset(values)


def test_get_discovered_values_unknown_column_returns_empty():
    assert get_discovered_values("hr_headcount", "nonexistent_column") == []


def test_get_discovered_values_unknown_table_returns_empty():
    assert get_discovered_values("nonexistent_table", "department") == []


def test_get_last_ingested_count_hr_headcount():
    assert get_last_ingested_count("hr_headcount") == 10418


def test_get_last_ingested_count_vendor_overview():
    assert get_last_ingested_count("vendor_overview") is not None


def test_get_last_ingested_count_license_utilization():
    assert get_last_ingested_count("license_utilization") == 16649


def test_get_last_ingested_count_unknown_table():
    assert get_last_ingested_count("nonexistent_table") is None


def test_get_last_ingested_count_returns_int_or_none():
    assert isinstance(get_last_ingested_count("hr_headcount"), int)
    assert get_last_ingested_count("nonexistent_table") is None


def test_row_count_check_warns_on_deviation(monkeypatch, caplog):
    monkeypatch.setattr(employee_service, "get_last_ingested_count", lambda table_name: 10418)
    with caplog.at_level("WARNING"):
        employee_service._check_row_count("hr_headcount", 9000)
    assert any("Row count deviation" in record.message for record in caplog.records)
