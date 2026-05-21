"""Forecasting processors for active demand and hire-driven demand."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from typing import Optional

from processing.context_builder import ProcessingContext
from schemas.proc_forecast_results import LicenseDemandForecast


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


def _forecast_months(audit_date: str, forecast_months: int) -> list[str]:
    _validate_forecast_months(forecast_months)
    audit = date.fromisoformat(audit_date)
    first_month = _month_key(audit)
    return [_add_months(first_month, offset) for offset in range(forecast_months)]


def _validate_forecast_months(forecast_months: int) -> None:
    if forecast_months < 3 or forecast_months > 24:
        raise ValueError("forecast_months must be between 3 and 24")


def _allowed_vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    if vendor is None:
        return set(ctx.active_vendors)
    if vendor in set(ctx.active_vendors):
        return {vendor}
    return {vendor}


def _series_key(row: dict) -> tuple[str, str, str]:
    return (str(row.get("vendor") or ""), str(row.get("sku") or ""), str(row.get("seat_type") or ""))


def _month_start(month: str) -> date:
    return date.fromisoformat(f"{month}-01")


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
        current_capacity = int(contract.get("effective_total_seats") or 0)
        capacities[key] = max(capacities.get(key, 0), current_capacity)
    return sum(capacities.values())


def _build_headcount_rates(
    ctx: ProcessingContext,
    allowed: set[str],
) -> tuple[dict, dict, dict, dict]:
    emp_sub_team: dict[str, str] = {}
    for row in ctx.active_employees:
        eid = str(row.get("employee_id") or "")
        sub_team = str(row.get("sub_team") or "")
        if eid and sub_team:
            emp_sub_team[eid] = sub_team
    for row in ctx.exited_employees:
        eid = str(row.get("employee_id") or "")
        sub_team = str(row.get("sub_team") or "")
        if eid and sub_team:
            emp_sub_team[eid] = sub_team

    cohort_headcount: Counter = Counter()
    department_headcount: Counter = Counter()
    portfolio_headcount = 0
    for row in ctx.active_employees:
        department = str(row.get("department") or "")
        sub_team = str(row.get("sub_team") or "")
        cohort_headcount[(department, sub_team)] += 1
        department_headcount[department] += 1
        portfolio_headcount += 1

    series_provisioned: Counter = Counter()
    department_provisioned: Counter = Counter()
    portfolio_provisioned: Counter = Counter()

    for row in ctx.licenses:
        if row.get("vendor") not in allowed or row.get("license_status") not in {"active", "over_tier"}:
            continue
        vendor_name, sku, seat_type = _series_key(row)
        department = str(row.get("department") or "")
        employee_id = str(row.get("employee_id") or "")
        sub_team = emp_sub_team.get(employee_id, "")
        series_provisioned[(vendor_name, sku, seat_type, department, sub_team)] += 1
        department_provisioned[(vendor_name, sku, seat_type, department)] += 1
        portfolio_provisioned[(vendor_name, sku, seat_type)] += 1

    return {
        "cohort_headcount": cohort_headcount,
        "department_headcount": department_headcount,
        "portfolio_headcount": portfolio_headcount,
        "series_provisioned": series_provisioned,
        "department_provisioned": department_provisioned,
        "portfolio_provisioned": portfolio_provisioned,
        "emp_sub_team": emp_sub_team,
    }, {}, {}, {}


def _rate_for(
    rate_data: dict,
    vendor: str,
    sku: str,
    seat_type: str,
    department: str,
    sub_team: str,
) -> tuple[float, str]:
    cohort_count = rate_data["cohort_headcount"].get((department, sub_team), 0)
    provisioned = rate_data["series_provisioned"].get((vendor, sku, seat_type, department, sub_team), 0)
    if cohort_count:
        return provisioned / cohort_count, "dept_level"

    department_count = rate_data["department_headcount"].get(department, 0)
    department_provisioned = rate_data["department_provisioned"].get((vendor, sku, seat_type, department), 0)
    if department_count:
        return department_provisioned / department_count, "dept_only"

    portfolio_count = rate_data["portfolio_headcount"]
    portfolio_provisioned = rate_data["portfolio_provisioned"].get((vendor, sku, seat_type), 0)
    if portfolio_count:
        return portfolio_provisioned / portfolio_count, "portfolio"
    return 0.0, "portfolio"


def get_license_demand_forecast(
    ctx: ProcessingContext,
    vendor: Optional[str] = None,
    department: Optional[str] = None,
    forecast_months: int = 8,
    before_date: Optional[str] = None,
) -> list[LicenseDemandForecast]:
    """
    Forecast hire-driven license demand per vendor+SKU+seat_type+month.

    Months with no confirmed hires are returned with zero expected demand.
    `before_date` is retained as a compatibility filter for callers that need
    to narrow the hire pipeline to a renewal window.
    """

    months = _forecast_months(ctx.audit_date, forecast_months)
    allowed = _allowed_vendors(ctx, vendor)
    if vendor is not None and vendor not in ctx.active_vendors:
        return []

    end_date = _as_date(before_date) if before_date else None
    hires_by_month: dict[str, list[dict]] = defaultdict(list)
    pipeline_months: set[str] = set()
    for hire in ctx.future_hires:
        hire_date = _as_date(hire.get("hire_date"))
        if hire_date is None:
            continue
        pipeline_months.add(_month_key(hire_date))
        if end_date is not None and hire_date > end_date:
            continue
        if department is not None and hire.get("department") != department:
            continue
        hire_month = _month_key(hire_date)
        if hire_month in months:
            hires_by_month[hire_month].append(hire)

    active_series = sorted(
        {
            _series_key(row)
            for row in ctx.licenses
            if row.get("vendor") in allowed and row.get("license_status") in {"active", "over_tier"}
        }
    )
    if not active_series:
        return []

    baseline_per_series: dict[tuple[str, str, str], int] = {}
    for key in active_series:
        vendor_name, sku, seat_type = key
        baseline_per_series[key] = sum(
            1
            for row in ctx.licenses
            if row.get("vendor") == vendor_name
            and row.get("sku") == sku
            and row.get("seat_type") == seat_type
            and row.get("license_status") not in ("ghost", "deprovisioned")
        )

    cumulative_new: defaultdict[tuple[str, str, str], float] = defaultdict(float)
    rate_data, _, _, _ = _build_headcount_rates(ctx, allowed)
    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[LicenseDemandForecast] = []

    for vendor_name, sku, seat_type in active_series:
        for forecast_month in months:
            grain_order = {"dept_level": 0, "dept_only": 1, "portfolio": 2}
            applied_grain = "dept_level"
            total_expected = 0.0
            dept_accumulator: dict[str, dict] = {}
            hire_counts_by_dept_sub: Counter = Counter(
                (
                    str(hire.get("department") or ""),
                    str(hire.get("sub_team") or ""),
                )
                for hire in hires_by_month.get(forecast_month, [])
            )
            for (dept, sub_team), hire_count in sorted(hire_counts_by_dept_sub.items()):
                rate, grain = _rate_for(rate_data, vendor_name, sku, seat_type, dept, sub_team)
                expected = hire_count * rate
                total_expected += expected
                if grain_order[grain] > grain_order[applied_grain]:
                    applied_grain = grain
                if dept not in dept_accumulator:
                    dept_accumulator[dept] = {"department": dept, "hires": 0, "expected_licenses": 0.0}
                dept_accumulator[dept]["hires"] += int(hire_count)
                dept_accumulator[dept]["expected_licenses"] += expected

            cumulative_new[(vendor_name, sku, seat_type)] += total_expected
            baseline = baseline_per_series.get((vendor_name, sku, seat_type), 0)
            projected = round(baseline + cumulative_new[(vendor_name, sku, seat_type)], 2)
            contracted_capacity = _contracted_capacity_for_month(ctx, forecast_month, vendor_name, sku, seat_type)

            by_department = [
                {
                    "department": dept,
                    "hires": data["hires"],
                    "expected_licenses": round(data["expected_licenses"], 2),
                }
                for dept, data in sorted(dept_accumulator.items())
            ]
            results.append(
                LicenseDemandForecast(
                    vendor=vendor_name,
                    sku=sku,
                    seat_type=seat_type,
                    forecast_month=forecast_month,
                    expected_new_licenses=round(total_expected, 2),
                    baseline_active=baseline,
                    projected_active=projected,
                    contracted_capacity=contracted_capacity,
                    projected_over_capacity=round(max(0.0, projected - contracted_capacity), 2),
                    exit_licenses_applied=0.0,
                    pipeline_data_available=forecast_month in pipeline_months,
                    by_department=by_department,
                    rate_grain_applied=applied_grain,
                    exit_model_applied=False,
                    computed_at=computed_at,
                )
            )
    return results
