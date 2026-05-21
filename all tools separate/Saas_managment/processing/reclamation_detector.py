"""License reclamation candidate detector."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from processing.context_builder import ProcessingContext
from schemas.proc_results import ReclamationResult


def _allowed_vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    return set(ctx.active_vendors) if vendor is None else ({vendor} if vendor in ctx.active_vendors else set())


def _float(value: object) -> float:
    return float(value or 0.0)


def _score(row: dict) -> float:
    """Score active licenses for rightsizing on a 0.45–1.0 scale.

 0.45 is the floor for any license with a utilization risk signal; bonuses add up to 1.0.
    """
    tier = str(row.get("usage_tier") or "").lower()
    days = _float(row.get("days_since_last_active"))
    flagged = bool(row.get("reclamation_candidate"))

    has_signal = tier in {"dormant", "inactive"} or days > 30 or flagged
    if not has_signal:
        return 0.0

    score = 0.45
    if tier in {"dormant", "inactive"}:
        score += 0.15
    if days > 60:
        score += 0.15
    elif days > 30:
        score += 0.05
    if row.get("seat_tier_match") == "over_tier":
        score += 0.10
    if flagged:
        score += 0.05
    return min(1.0, round(score, 3))


def get_reclamation_candidates(
    ctx: ProcessingContext,
    vendor: Optional[str] = None,
    department: Optional[str] = None,
    min_score: float = 0.3,
) -> list[ReclamationResult]:
    """Return ranked reclamation candidates for active licenses with low utilization.

    Ghost licenses are excluded — use the ghost detector for deprovision workflows.
    """

    allowed = _allowed_vendors(ctx, vendor)
    if not allowed:
        return []
    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[ReclamationResult] = []
    for row in ctx.licenses:
        if row.get("vendor") not in allowed:
            continue
        if row.get("license_status") not in {"active", "over_tier"}:
            continue
        if department is not None and row.get("department") != department:
            continue
        score = _score(row)
        if score < min_score:
            continue
        results.append(
            ReclamationResult(
                license_id=str(row.get("license_id") or ""),
                vendor=str(row.get("vendor") or ""),
                sku=str(row.get("sku") or ""),
                seat_type=str(row.get("seat_type") or ""),
                employee_id=str(row.get("employee_id") or ""),
                email=str(row.get("assigned_email") or ""),
                department=str(row.get("department") or ""),
                job_level=str(row.get("job_level") or ""),
                license_status=str(row.get("license_status") or ""),
                usage_tier=str(row.get("usage_tier") or ""),
                days_since_last_active=_float(row.get("days_since_last_active")),
                seat_tier_match=str(row.get("seat_tier_match") or ""),
                monthly_cost=_float(row.get("monthly_cost")),
                annual_cost=_float(row.get("annual_cost")),
                reclamation_score=score,
                reclamation_candidate_flag=bool(row.get("reclamation_candidate")),
                computed_at=computed_at,
            )
        )
    return sorted(results, key=lambda row: (row.reclamation_score, row.monthly_cost), reverse=True)
