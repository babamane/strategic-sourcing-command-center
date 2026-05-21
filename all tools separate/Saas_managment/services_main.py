"""Entry point for the SaaS Spend Phase 1B services scaffold."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime

from services import contract_service, employee_service, forecast_service, license_service, trueup_service


def configure_logging() -> None:
    """Set up readable INFO-level logs."""

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _json_default(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _summarize_payload(payload: object) -> object:
    if isinstance(payload, list):
        return {
            "count": len(payload),
            "sample": payload[0] if payload else None,
        }
    return payload


def _print_section(title: str, payload: object, as_json: bool, full: bool) -> None:
    print(f"\n== {title} ==")
    if not full:
        payload = _summarize_payload(payload)
    if as_json:
        print(json.dumps(payload, indent=2, default=_json_default))
    else:
        print(payload)


def main() -> None:
    """Run a small manual demo of the Phase 1B services."""

    configure_logging()

    parser = argparse.ArgumentParser(description="Manual runner for Phase 1B services.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Pretty-print example outputs as JSON instead of Python reprs.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Print the full raw payloads instead of summarized demo output.",
    )
    parser.add_argument(
        "--vendor",
        default=None,
        help="Optional vendor filter for vendor-scoped services.",
    )
    parser.add_argument(
        "--email",
        default="derek.gardner@company.com",
        help="Employee email to inspect in the demo output.",
    )
    args = parser.parse_args()

    logging.info("Running Phase 1B service demo...")

    _print_section(
        "contract_service.get_entitlement",
        contract_service.get_entitlement(vendor=args.vendor),
        args.json,
        args.full,
    )
    _print_section(
        "contract_service.get_active_contracts",
        contract_service.get_active_contracts(vendor=args.vendor),
        args.json,
        args.full,
    )

    entitlement_rows = contract_service.get_entitlement(vendor=args.vendor)
    if entitlement_rows:
        sample_contract = entitlement_rows[0]
        _print_section(
            "contract_service.get_contract_history",
            contract_service.get_contract_history(
                vendor=sample_contract["vendor"],
                sku=sample_contract["sku"],
                seat_type=sample_contract["seat_type"],
            ),
            args.json,
            args.full,
        )

    _print_section(
        "license_service.get_raw_licenses",
        license_service.get_raw_licenses(vendor=args.vendor),
        args.json,
        args.full,
    )

    _print_section(
        "employee_service.get_active_employees",
        employee_service.get_active_employees(),
        args.json,
        args.full,
    )
    _print_section(
        "employee_service.get_exited_employees",
        employee_service.get_exited_employees(),
        args.json,
        args.full,
    )
    _print_section(
        "employee_service.get_future_hires",
        employee_service.get_future_hires(),
        args.json,
        args.full,
    )
    _print_section(
        "employee_service.get_employee_by_email",
        employee_service.get_employee_by_email(args.email),
        args.json,
        args.full,
    )
    _print_section(
        "employee_service.get_department_headcount",
        employee_service.get_department_headcount(),
        args.json,
        args.full,
    )

    _print_section(
        "trueup_service.compute_snapshot",
        "Not implemented in Phase 1B",
        args.json,
        args.full,
    )
    _print_section(
        "forecast_service.get_pressure_summary",
        "Not implemented in Phase 1B",
        args.json,
        args.full,
    )

    logging.info("Phase 1B service demo complete.")


if __name__ == "__main__":
    main()
