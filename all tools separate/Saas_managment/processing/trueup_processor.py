"""True-up and shelfware exposure processor."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime
from typing import Optional

from processing.context_builder import ProcessingContext
from schemas.proc_results import TrueUpResult


def _as_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _days_until(audit_date: str, value: object) -> int:
    target = _as_date(value)
    if target is None:
        return 0
    return (target - date.fromisoformat(audit_date)).days


def _vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    if vendor is None:
        return set(ctx.active_vendors)
    return {vendor} if vendor in set(ctx.active_vendors) else set()


def _urgency(days: int) -> str:
    if days < 0:
        return "expired"
    if days <= 30:
        return "critical"
    if days <= 60:
        return "high"
    if days <= 90:
        return "medium"
    return "ok"


def get_trueup_exposure(ctx: ProcessingContext, vendor: Optional[str] = None) -> list[TrueUpResult]:
    """Return true-up exposure per vendor, SKU, and seat type."""

    allowed = _vendors(ctx, vendor)
    if not allowed:
        return []

    counts: Counter[tuple[str, str, str]] = Counter()
    for row in ctx.licenses:
        if row.get("vendor") in allowed and row.get("license_status") in {"active", "over_tier"}:
            counts[(row["vendor"], row["sku"], row["seat_type"])] += 1

    entitlements = {
        (row["vendor"], row["sku"], row["seat_type"]): row
        for row in ctx.entitlement
        if row.get("vendor") in allowed
    }
    keys = sorted(set(counts) | set(entitlements))
    total_provisioned = sum(counts.values())
    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[TrueUpResult] = []

    for key in keys:
        entitlement = entitlements.get(key, {})
        provisioned = int(counts.get(key, 0))
        effective = int(entitlement.get("effective_total_seats") or 0)
        unit_price = float(entitlement.get("unit_price") or 0.0)
        exposure = max(0, provisioned - effective)
        shelfware = max(0, effective - provisioned)
        days_until_notice = _days_until(ctx.audit_date, entitlement.get("notice_deadline"))
        results.append(
            TrueUpResult(
                vendor=key[0],
                sku=key[1],
                seat_type=key[2],
                effective_total_seats=effective,
                active_provisioned_seats=provisioned,
                exposure_seats=exposure,
                shelfware_seats=shelfware,
                unit_price=unit_price,
                exposure_amount_monthly=round(exposure * unit_price, 2),
                shelfware_amount_monthly=round(shelfware * unit_price, 2),
                exposure_amount_annual=round(exposure * unit_price * 12, 2),
                shelfware_amount_annual=round(shelfware * unit_price * 12, 2),
                portfolio_ratio=round(provisioned / total_provisioned, 6) if total_provisioned else 0.0,
                notice_deadline=_as_date(entitlement.get("notice_deadline")).isoformat()
                if entitlement.get("notice_deadline")
                else "",
                days_until_notice_deadline=days_until_notice,
                auto_renewal=bool(entitlement.get("auto_renewal", False)),
                true_down_rights=bool(entitlement.get("true_down_rights", False)),
                measurement_method=str(entitlement.get("measurement_method") or ""),
                renewal_urgency=_urgency(days_until_notice),
                computed_at=computed_at,
            )
        )

    return results
