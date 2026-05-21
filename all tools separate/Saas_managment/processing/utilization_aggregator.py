"""License utilization rollups."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Optional

from processing.context_builder import ProcessingContext
from schemas.proc_results import UtilizationResult

USAGE_TIERS = ("power", "moderate", "underutilized", "dormant", "inactive","active","over-tier")


def _allowed_vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    return set(ctx.active_vendors) if vendor is None else ({vendor} if vendor in ctx.active_vendors else set())


def get_utilization_summary(ctx: ProcessingContext, vendor: Optional[str] = None) -> list[UtilizationResult]:
    """Return utilization summary per vendor, SKU, and seat type."""

    allowed = _allowed_vendors(ctx, vendor)
    if not allowed:
        return []

    entitlement_index: dict[tuple[str, str, str], int] = {}
    for e in ctx.entitlement:
        if e.get("contract_status") == "active":
            key = (e["vendor"], e["sku"], e["seat_type"])
            entitlement_index[key] = int(e.get("effective_total_seats") or 0)

    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in ctx.licenses:
        if row.get("vendor") in allowed:
            groups[(row["vendor"], row["sku"], row["seat_type"])].append(row)

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[UtilizationResult] = []
    for key, rows in sorted(groups.items()):
        contracted = entitlement_index.get(key, 0)
        total = contracted
        counts = Counter(str(row.get("usage_tier") or "") for row in rows)
        by_usage_tier = {tier: int(counts.get(tier, 0)) for tier in USAGE_TIERS}
        active = by_usage_tier["power"] + by_usage_tier["moderate"] + by_usage_tier["active"] + by_usage_tier["over-tier"] + by_usage_tier["underutilized"]
        waste = by_usage_tier["dormant"] + by_usage_tier["inactive"]
        monthly = sum(float(row.get("monthly_cost") or 0.0) for row in rows)
        results.append(
            UtilizationResult(
                vendor=key[0],
                sku=key[1],
                seat_type=key[2],
                total_licenses=total,
                by_usage_tier=by_usage_tier,
                active_rate=round(active / total, 6) if total else 0.0,
                waste_rate=round(waste / total, 6) if total else 0.0,
                total_monthly_cost=round(monthly, 2),
                computed_at=computed_at,
            )
        )
    return results
