"""Department and job-level breakdowns for true-up exposure."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Optional

from processing.context_builder import ProcessingContext
from schemas.proc_results import TrueUpBreakdownResult


def _allowed_vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    return set(ctx.active_vendors) if vendor is None else ({vendor} if vendor in ctx.active_vendors else set())


def _rank(counter: Counter[str], key_name: str) -> list[dict]:
    return [{key_name: key, "provisioned": int(value)} for key, value in counter.most_common()]


def get_trueup_breakdown(
    ctx: ProcessingContext,
    vendor: Optional[str] = None,
    sku: Optional[str] = None,
    seat_type: Optional[str] = None,
) -> list[TrueUpBreakdownResult]:
    """Return provisioned overage breakdowns by department and job level."""

    allowed = _allowed_vendors(ctx, vendor)
    if not allowed:
        return []

    entitlement = {
        (row["vendor"], row["sku"], row["seat_type"]): int(row.get("effective_total_seats") or 0)
        for row in ctx.entitlement
        if row.get("vendor") in allowed
    }
    grouped: dict[tuple[str, str, str], list[dict]] = {}
    for row in ctx.licenses:
        key = (row.get("vendor"), row.get("sku"), row.get("seat_type"))
        if row.get("vendor") not in allowed or row.get("license_status") not in {"active", "over_tier"}:
            continue
        if sku is not None and row.get("sku") != sku:
            continue
        if seat_type is not None and row.get("seat_type") != seat_type:
            continue
        grouped.setdefault(key, []).append(row)

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[TrueUpBreakdownResult] = []
    for key, rows in sorted(grouped.items()):
        exposure = max(0, len(rows) - entitlement.get(key, 0))
        if exposure <= 0:
            continue
        departments = Counter(str(row.get("department") or "Unknown") for row in rows)
        job_levels = Counter(str(row.get("job_level") or "Unknown") for row in rows)
        job_by_department: dict[str, Counter[str]] = defaultdict(Counter)
        for row in rows:
            job_by_department[str(row.get("department") or "Unknown")][str(row.get("job_level") or "Unknown")] += 1
        by_department = [
            {
                "department": department,
                "provisioned": int(provisioned),
                "exposure_share": round((provisioned / len(rows)) * exposure, 2) if rows else 0.0,
                "by_job_level": _rank(job_by_department[department], "job_level"),
            }
            for department, provisioned in departments.most_common()
        ]
        results.append(
            TrueUpBreakdownResult(
                vendor=key[0],
                sku=key[1],
                seat_type=key[2],
                total_provisioned=len(rows),
                effective_total_seats=entitlement.get(key, 0),
                exposure_seats=exposure,
                by_department=by_department,
                by_job_level=_rank(job_levels, "job_level"),
                top_departments=by_department[:3],
                computed_at=computed_at,
            )
        )
    return results
