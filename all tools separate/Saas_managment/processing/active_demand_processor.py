"""Historical and unified active demand processors.

`get_active_demand_series` is a thin composition layer: it joins the observed
history with the existing demand forecaster output so consumers do not need to
stitch the audit-date boundary themselves.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Optional

from processing.context_builder import ProcessingContext
from processing.license_demand_forecaster import get_license_demand_forecast
from schemas.proc_forecast_results import ActiveDemandHistory, ActiveDemandPoint


def _as_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _parse_month(month: str) -> tuple[int, int]:
    year, month_number = month.split("-", 1)
    return int(year), int(month_number)


def _add_months(month: str, offset: int) -> str:
    year, month_number = _parse_month(month)
    month_index = (year * 12 + month_number - 1) + offset
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def _month_start(month: str) -> date:
    return date.fromisoformat(f"{month}-01")


def _month_end(month: str) -> date:
    return _month_start(_add_months(month, 1)) - timedelta(days=1)


def _allowed_vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    if vendor is None:
        return set(ctx.active_vendors)
    if vendor in set(ctx.active_vendors):
        return {vendor}
    return {vendor}


def _series_key(row: dict) -> tuple[str, str, str]:
    return (str(row.get("vendor") or ""), str(row.get("sku") or ""), str(row.get("seat_type") or ""))


def _contract_matches_month(contract: dict, month: str) -> bool:
    month_start = _month_start(month)
    contract_start = _as_date(contract.get("contract_start"))
    contract_expiry = _as_date(contract.get("contract_expiry"))
    if contract_start is None or contract_expiry is None:
        return False
    return contract_start <= month_start < contract_expiry


def _contracted_capacity_for_month(
    ctx: ProcessingContext,
    month: str,
    vendor: str,
    sku: str,
    seat_type: str,
) -> int:
    capacities: dict[tuple[str, str, str], int] = {}
    for contract in ctx.contract_history:
        contract_vendor = str(contract.get("vendor") or "")
        contract_sku = str(contract.get("sku") or "")
        contract_seat_type = str(contract.get("seat_type") or "")
        if (contract_vendor, contract_sku, contract_seat_type) != (vendor, sku, seat_type):
            continue
        if not _contract_matches_month(contract, month):
            continue
        key = (contract_vendor, contract_sku, contract_seat_type)
        capacities[key] = max(capacities.get(key, 0), int(contract.get("effective_total_seats") or 0))
    return sum(capacities.values())


def get_active_demand_history(
    ctx: ProcessingContext,
    vendor: Optional[str] = None,
) -> list[ActiveDemandHistory]:
    """Return observed active demand history at vendor+SKU+seat_type+month grain."""

    allowed = _allowed_vendors(ctx, vendor)
    effective_dates = [
        _as_date(row.get("effective_license_date"))
        for row in ctx.licenses
        if row.get("vendor") in allowed
    ]
    effective_dates = [value for value in effective_dates if value is not None]
    if not effective_dates:
        return []

    start_month = _month_key(min(effective_dates))
    end_month = _month_key(date.fromisoformat(ctx.audit_date))
    months: list[str] = []
    current = start_month
    while current <= end_month:
        months.append(current)
        current = _add_months(current, 1)

    exit_lookup: dict[str, date] = {}
    for row in ctx.exited_employees:
        employee_id = str(row.get("employee_id") or "")
        exit_date = _as_date(row.get("exit_date"))
        if employee_id and exit_date is not None:
            exit_lookup[employee_id] = exit_date

    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in ctx.licenses:
        key = _series_key(row)
        if key[0] in allowed:
            grouped[key].append(row)

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[ActiveDemandHistory] = []
    for key, rows in sorted(grouped.items()):
        vendor_name, sku, seat_type = key
        for month in months:
            month_end = _month_end(month)
            vendor_billed = 0
            productive_active = 0
            for row in rows:
                effective_license_date = _as_date(row.get("effective_license_date"))
                if effective_license_date is None or effective_license_date > month_end:
                    continue

                license_status = str(row.get("license_status") or "")
                employee_id = str(row.get("employee_id") or "")
                exit_date = exit_lookup.get(employee_id)
                if exit_date is not None and exit_date <= month_end and license_status == "active":
                    license_status = "ghost"

                if license_status != "deprovisioned":
                    vendor_billed += 1
                if license_status not in {"ghost", "deprovisioned"}:
                    productive_active += 1

            contracted_capacity = _contracted_capacity_for_month(ctx, month, vendor_name, sku, seat_type)
            ghost_count = vendor_billed - productive_active
            results.append(
                ActiveDemandHistory(
                    vendor=vendor_name,
                    sku=sku,
                    seat_type=seat_type,
                    month=month,
                    productive_active=productive_active,
                    vendor_billed=vendor_billed,
                    ghost_count=ghost_count,
                    contracted_capacity=contracted_capacity,
                    over_capacity=productive_active > contracted_capacity,
                    computed_at=computed_at,
                )
            )
    return results


def get_active_demand_series(
    ctx: ProcessingContext,
    vendor: Optional[str] = None,
) -> list[ActiveDemandPoint]:
    """Return one continuous active-demand line per series across history and forecast."""

    historical_rows = get_active_demand_history(ctx, vendor)
    historical_points = [
        ActiveDemandPoint(
            vendor=row.vendor,
            sku=row.sku,
            seat_type=row.seat_type,
            month=row.month,
            is_forecast=False,
            productive_active=row.productive_active,
            vendor_billed=row.vendor_billed,
            ghost_count=row.ghost_count,
            projected_active=float(row.productive_active),
            contracted_capacity=row.contracted_capacity,
            projected_over_capacity=round(max(0.0, row.productive_active - row.contracted_capacity), 2),
            pipeline_data_available=False,
            computed_at=row.computed_at,
        )
        for row in historical_rows
    ]

    audit_month = _month_key(date.fromisoformat(ctx.audit_date))
    historical_lookup = {
        (row.vendor, row.sku, row.seat_type): row
        for row in historical_points
        if row.month == audit_month
    }

    demand_rows = get_license_demand_forecast(ctx, vendor=vendor, forecast_months=24)
    forecast_points: list[ActiveDemandPoint] = []
    for row in demand_rows:
        if row.forecast_month == audit_month:
            continue
        previous_observed = historical_lookup.get((row.vendor, row.sku, row.seat_type))
        projected_active = row.projected_active
        if previous_observed is not None and row.forecast_month == _add_months(audit_month, 1):
            projected_active = previous_observed.projected_active
        forecast_points.append(
            ActiveDemandPoint(
                vendor=row.vendor,
                sku=row.sku,
                seat_type=row.seat_type,
                month=row.forecast_month,
                is_forecast=True,
                productive_active=0,
                vendor_billed=0,
                ghost_count=0,
                projected_active=projected_active,
                contracted_capacity=row.contracted_capacity,
                projected_over_capacity=round(max(0.0, projected_active - row.contracted_capacity), 2),
                pipeline_data_available=row.pipeline_data_available,
                computed_at=row.computed_at,
            )
        )

    points = historical_points + forecast_points
    return sorted(points, key=lambda row: (row.vendor, row.sku, row.seat_type, row.month))
