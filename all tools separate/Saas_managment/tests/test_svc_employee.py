from datetime import date

import pytest

from exceptions import DataNotReadyError
from services import employee_service
from services.ingestion_service import get_discovered_values


ACTIVE_EMPLOYEE_KEYS = {
    "employee_id",
    "email",
    "department",
    "sub_team",
    "job_level",
    "region",
    "is_active",
    "hire_date",
}

EXITED_EMPLOYEE_KEYS = {
    "employee_id",
    "email",
    "department",
    "sub_team",
    "job_level",
    "region",
    "is_active",
    "exit_date",
    "exit_type",
}

FUTURE_HIRE_KEYS = {
    "employee_id",
    "email",
    "department",
    "sub_team",
    "job_level",
    "region",
    "hire_date",
    "employee_status",
}

EMPLOYEE_BY_EMAIL_KEYS = {
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
}


def test_get_active_employees_exact_count(default_version):
    assert len(employee_service.get_active_employees(version=default_version)) == 6016


def test_get_active_employees_all_active(default_version):
    rows = employee_service.get_active_employees(version=default_version)
    assert all(row["is_active"] is True for row in rows)


def test_get_active_employees_no_pii(default_version):
    rows = employee_service.get_active_employees(version=default_version)
    assert all("full_name" not in row for row in rows)


def test_get_active_employees_columns_exact(default_version):
    rows = employee_service.get_active_employees(version=default_version)
    assert rows and set(rows[0].keys()) == ACTIVE_EMPLOYEE_KEYS


def test_get_active_employees_department_values(default_version):
    rows = employee_service.get_active_employees(version=default_version)
    known_departments = set(get_discovered_values("hr_headcount", "department"))
    assert known_departments
    assert {row["department"] for row in rows}.issubset(known_departments)


def test_get_active_employees_job_level_values(default_version):
    rows = employee_service.get_active_employees(version=default_version)
    known_job_levels = set(get_discovered_values("hr_headcount", "job_level"))
    assert known_job_levels
    assert {row["job_level"] for row in rows}.issubset(known_job_levels)


def test_get_active_employees_region_values(default_version):
    rows = employee_service.get_active_employees(version=default_version)
    known_regions = set(get_discovered_values("hr_headcount", "region"))
    assert known_regions
    assert {row["region"] for row in rows}.issubset(known_regions)


def test_get_exited_employees_exact_count(default_version):
    assert len(employee_service.get_exited_employees(version=default_version)) == 4222


def test_get_exited_employees_all_inactive(default_version):
    rows = employee_service.get_exited_employees(version=default_version)
    assert all(row["is_active"] is False for row in rows)


def test_get_exited_employees_exit_date_not_null(default_version):
    rows = employee_service.get_exited_employees(version=default_version)
    assert all(row["exit_date"] is not None for row in rows)


def test_get_exited_employees_exit_type_values(default_version):
    rows = employee_service.get_exited_employees(version=default_version)
    allowed = set(get_discovered_values("hr_headcount", "exit_type"))
    assert allowed
    assert {row["exit_type"] for row in rows if row["exit_type"] is not None}.issubset(allowed)


def test_get_exited_employees_no_pii(default_version):
    rows = employee_service.get_exited_employees(version=default_version)
    assert all("full_name" not in row for row in rows)


def test_get_future_hires_exact_count(default_version):
    assert len(employee_service.get_future_hires(version=default_version)) == 180


def test_get_future_hires_status_all_prehire(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    assert all(row["employee_status"] == "pre-hire" for row in rows)


def test_get_future_hires_all_inactive(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    assert all(row["hire_date"] > date(2026, 5, 1) for row in rows)


def test_get_future_hires_dates_within_window(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    assert all(row["hire_date"] <= date(2026, 7, 31) for row in rows)


def test_get_future_hires_no_exit_date(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    assert all("exit_date" not in row for row in rows)


def test_get_future_hires_may_count(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    may_rows = [row for row in rows if row["hire_date"].month == 5]
    assert len(may_rows) == 80


def test_get_future_hires_june_count(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    june_rows = [row for row in rows if row["hire_date"].month == 6]
    assert len(june_rows) == 60


def test_get_future_hires_july_count(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    july_rows = [row for row in rows if row["hire_date"].month == 7]
    assert len(july_rows) == 40


def test_get_future_hires_department_engineering(default_version):
    rows = employee_service.get_future_hires(department="Engineering", version=default_version)
    assert len(rows) == 54


def test_get_future_hires_department_sales(default_version):
    rows = employee_service.get_future_hires(department="Sales", version=default_version)
    assert len(rows) == 37


def test_get_future_hires_combined_filter(default_version):
    rows = employee_service.get_future_hires(
        department="Engineering",
        before_date=date(2026, 5, 31),
        version=default_version,
    )
    assert all(row["department"] == "Engineering" for row in rows)
    assert all(row["hire_date"] <= date(2026, 5, 31) for row in rows)


def test_get_future_hires_columns_exact(default_version):
    rows = employee_service.get_future_hires(version=default_version)
    assert rows and set(rows[0].keys()) == FUTURE_HIRE_KEYS


def test_get_active_employees_sub_team_values(default_version):
    rows = employee_service.get_active_employees(version=default_version)

    assert any(row.get("sub_team") for row in rows)


def test_get_future_hires_sub_team_key(default_version):
    rows = employee_service.get_future_hires(version=default_version)

    assert rows and all("sub_team" in row for row in rows)


def test_get_employee_by_email_found(default_version):
    row = employee_service.get_employee_by_email("derek.gardner@company.com", version=default_version)
    assert row["employee_id"] == "EMP-00001"


def test_get_employee_by_email_not_found(default_version):
    with pytest.raises(DataNotReadyError):
        employee_service.get_employee_by_email("nonexistent@x.com", version=default_version)


def test_get_employee_by_email_no_pii(default_version):
    row = employee_service.get_employee_by_email("derek.gardner@company.com", version=default_version)
    assert "full_name" not in row and "sub_team" not in row


def test_get_employee_by_email_columns_exact(default_version):
    row = employee_service.get_employee_by_email("derek.gardner@company.com", version=default_version)
    assert set(row.keys()) == EMPLOYEE_BY_EMAIL_KEYS


def test_get_employee_by_email_returns_dict_not_list(default_version):
    row = employee_service.get_employee_by_email("derek.gardner@company.com", version=default_version)
    assert isinstance(row, dict)


def test_get_department_headcount_returns_dict(default_version):
    assert isinstance(employee_service.get_department_headcount(version=default_version), dict)


def test_get_department_headcount_keys_from_discovery(default_version):
    result = employee_service.get_department_headcount(version=default_version)
    assert set(result.keys()) == set(get_discovered_values("hr_headcount", "department"))


def test_get_department_headcount_total_equals_active(default_version):
    result = employee_service.get_department_headcount(version=default_version)
    assert sum(result.values()) == 6016


def test_get_department_headcount_values_are_ints(default_version):
    result = employee_service.get_department_headcount(version=default_version)
    assert all(isinstance(value, int) and value >= 0 for value in result.values())
