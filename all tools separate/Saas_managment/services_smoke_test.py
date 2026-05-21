"""Concise manual smoke test for Phase 1B services."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime

from services import contract_service, employee_service, license_service


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _json_default(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _print(label: str, payload: object) -> None:
    print(f"{label}: {json.dumps(payload, default=_json_default)}")


def main() -> None:
    configure_logging()
    logging.info("Running Phase 1B smoke checks...")

    entitlement = contract_service.get_entitlement()
    active_contracts = contract_service.get_active_contracts()
    history = contract_service.get_contract_history("Atlassify", "Project Suite", "Full")
    raw_licenses = license_service.get_raw_licenses()
    active_employees = employee_service.get_active_employees()
    exited_employees = employee_service.get_exited_employees()
    future_hires = employee_service.get_future_hires()
    employee = employee_service.get_employee_by_email("derek.gardner@company.com")
    dept_headcount = employee_service.get_department_headcount()

    _print("entitlement_count", len(entitlement))
    _print("entitlement_sample", entitlement[0] if entitlement else None)
    _print("active_contract_count", len(active_contracts))
    _print("active_contract_sample", active_contracts[0] if active_contracts else None)
    _print("history_count", len(history))
    _print("history_sample", history[0] if history else None)
    _print("raw_licenses_count", len(raw_licenses))
    _print("raw_license_sample", raw_licenses[0] if raw_licenses else None)
    _print("active_employees_count", len(active_employees))
    _print("exited_employees_count", len(exited_employees))
    _print("future_hires_count", len(future_hires))
    _print("employee_sample", employee)
    _print("dept_headcount_total", sum(dept_headcount.values()))
    _print("dept_headcount", dept_headcount)

    logging.info("Phase 1B smoke checks complete.")


if __name__ == "__main__":
    main()
