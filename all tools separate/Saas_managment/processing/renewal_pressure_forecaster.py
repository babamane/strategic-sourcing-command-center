"""Renewal pressure scoring processor."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime
from typing import Optional

from processing.context_builder import ProcessingContext
from processing.license_demand_forecaster import get_license_demand_forecast, _month_key
from schemas.proc_results import RenewalPressureResult


def _as_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _allowed_vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    return set(ctx.active_vendors) if vendor is None else ({vendor} if vendor in ctx.active_vendors else set())


def _urgency(days: int) -> tuple[str, float]:
    if days < 0:
        return "expired", 1.0
    if days <= 30:
        return "critical", 0.9
    if days <= 60:
        return "high", 0.7
    if days <= 90:
        return "medium", 0.5
    return "ok", 0.2


def _classification(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.5:
        return "at-risk"
    return "ok"


def get_renewal_pressure(ctx: ProcessingContext, vendor: Optional[str] = None) -> list[RenewalPressureResult]:
    """Return renewal pressure score per active contract."""

    allowed = _allowed_vendors(ctx, vendor)
    if not allowed:
        return []
    audit = date.fromisoformat(ctx.audit_date)
    provisioned = Counter()
    for row in ctx.licenses:
        if row.get("vendor") in allowed and row.get("license_status") in {"active", "over_tier"}:
            provisioned[(row["vendor"], row["sku"], row["seat_type"])] += 1

    entitlement = {
        (row["vendor"], row["sku"], row["seat_type"]): int(row.get("effective_total_seats") or 0)
        for row in ctx.entitlement
        if row.get("vendor") in allowed
    }

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    demand_rows = get_license_demand_forecast(ctx, forecast_months=8)
    results: list[RenewalPressureResult] = []
    for contract in ctx.active_contracts:
        if contract.get("vendor") not in allowed:
            continue
        key = (contract["vendor"], contract["sku"], contract["seat_type"])
        notice_deadline = _as_date(contract.get("notice_deadline"))
        days = (notice_deadline - audit).days if notice_deadline else 0
        urgency_label, urgency_score = _urgency(days)
        current = int(provisioned.get(key, 0))
        effective = int(entitlement.get(key, contract.get("effective_total_seats") or 0))
        exposure = max(0, current - effective)

        deadline_month = _month_key(notice_deadline) if notice_deadline else None
        projected_at_deadline = float(current)
        if deadline_month:
            matching = [
                row for row in demand_rows
                if (row.vendor, row.sku, row.seat_type) == key
                and row.forecast_month <= deadline_month
            ]
            if matching:
                closest = max(matching, key=lambda r: r.forecast_month)
                projected_at_deadline = closest.projected_active

        demand_before_deadline = round(projected_at_deadline, 2)
        growth_ratio = max(0.0, projected_at_deadline - current) / current if current else 0.0
        growth_score = 0.4 if growth_ratio >= 0.10 else 0.2 if growth_ratio >= 0.05 else 0.0
        exposure_score = 0.3 if exposure > 0 else 0.0
        pressure = min(1.0, round(urgency_score + growth_score + exposure_score, 3))
        results.append(
            RenewalPressureResult(
                vendor=contract["vendor"],
                sku=contract["sku"],
                seat_type=contract["seat_type"],
                of_id=str(contract.get("of_id") or ""),
                contract_expiry=_as_date(contract.get("contract_expiry")).isoformat()
                if contract.get("contract_expiry")
                else "",
                notice_deadline=notice_deadline.isoformat() if notice_deadline else "",
                days_until_notice_deadline=days,
                renewal_urgency=urgency_label,
                auto_renewal=bool(contract.get("auto_renewal", False)),
                true_down_rights=bool(contract.get("true_down_rights", False)),
                current_provisioned=current,
                effective_total_seats=effective,
                exposure_seats=exposure,
                hires_before_deadline=round(demand_before_deadline, 2),
                hires_by_department=[],
                urgency_score=urgency_score,
                growth_score=growth_score,
                exposure_score=exposure_score,
                pressure_score=pressure,
                pressure_classification=_classification(pressure),
                exit_model_applied=False,
                computed_at=computed_at,
            )
        )
    return sorted(results, key=lambda row: row.pressure_score, reverse=True)
