"""Ghost license detector."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from typing import Optional

from processing.context_builder import ProcessingContext
from schemas.proc_results import GhostDetailResult, GhostSummaryResult


def _allowed_vendors(ctx: ProcessingContext, vendor: Optional[str]) -> set[str]:
    return set(ctx.active_vendors) if vendor is None else ({vendor} if vendor in ctx.active_vendors else set())


def _float(value: object) -> float:
    return float(value or 0.0)


def _as_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def get_ghost_summary(ctx: ProcessingContext, vendor: Optional[str] = None) -> list[GhostSummaryResult]:
    """Return ghost license rollups by vendor."""

    allowed = _allowed_vendors(ctx, vendor)
    if not allowed:
        return []
    ghosts_by_vendor: dict[str, list[dict]] = defaultdict(list)
    future_ids = {row.get("employee_id") for row in ctx.future_hires}
    for row in ctx.licenses:
        if row.get("vendor") in allowed and row.get("license_status") == "ghost":
            if row.get("employee_id") in future_ids:
                continue
            ghosts_by_vendor[row["vendor"]].append(row)

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[GhostSummaryResult] = []
    for vendor_name, rows in sorted(ghosts_by_vendor.items()):
        by_department = Counter(str(row.get("department") or "Unknown") for row in rows)
        dept_costs: dict[str, float] = defaultdict(float)
        for row in rows:
            dept_costs[str(row.get("department") or "Unknown")] += _float(row.get("cost_at_risk"))
        days = [_float(row.get("days_since_last_active")) for row in rows]
        annual = sum(_float(row.get("cost_at_risk")) for row in rows)
        monthly = annual / 12
        results.append(
            GhostSummaryResult(
                vendor=vendor_name,
                ghost_license_count=len(rows),
                total_cost_at_risk_monthly=round(monthly, 2),
                total_cost_at_risk_annual=round(annual, 2),
                avg_days_orphaned=round(sum(days) / len(days), 2) if days else 0.0,
                max_days_orphaned=int(max(days)) if days else 0,
                by_department=[
                    {
                        "department": key,
                        "ghost_count": int(value),
                        "monthly_cost": round(dept_costs[key], 2),
                    }
                    for key, value in by_department.most_common()
                ],
                computed_at=computed_at,
            )
        )
    return results


def get_ghost_detail(
    ctx: ProcessingContext,
    vendor: Optional[str] = None,
    department: Optional[str] = None,
) -> list[GhostDetailResult]:
    """Return license-level ghost details."""

    allowed = _allowed_vendors(ctx, vendor)
    if not allowed:
        return []
    future_ids = {row.get("employee_id") for row in ctx.future_hires}
    exited = {row.get("employee_id"): row for row in ctx.exited_employees}
    audit = date.fromisoformat(ctx.audit_date)
    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[GhostDetailResult] = []
    for row in ctx.licenses:
        if row.get("vendor") not in allowed or row.get("license_status") != "ghost":
            continue
        if department is not None and row.get("department") != department:
            continue
        if row.get("employee_id") in future_ids:
            continue
        exit_row = exited.get(row.get("employee_id"), {})
        exit_date = _as_date(exit_row.get("exit_date"))
        days_orphaned = (audit - exit_date).days if exit_date else int(_float(row.get("days_since_last_active")))
        results.append(
            GhostDetailResult(
                license_id=str(row.get("license_id") or ""),
                vendor=str(row.get("vendor") or ""),
                sku=str(row.get("sku") or ""),
                seat_type=str(row.get("seat_type") or ""),
                employee_id=str(row.get("employee_id") or ""),
                email=str(row.get("assigned_email") or ""),
                department=str(row.get("department") or ""),
                job_level=str(row.get("job_level") or ""),
                exit_date=exit_date.isoformat() if exit_date else "",
                exit_type=str(exit_row.get("exit_type") or ""),
                days_orphaned=days_orphaned,
                monthly_cost=_float(row.get("monthly_cost")),
                cost_at_risk=_float(row.get("cost_at_risk")),
                annual_cost=_float(row.get("annual_cost")),
                days_since_last_active=_float(row.get("days_since_last_active")),
                computed_at=computed_at,
            )
        )
    return sorted(results, key=lambda row: row.cost_at_risk, reverse=True)


def get_ghost_details(ctx: ProcessingContext, vendor: Optional[str] = None) -> list[GhostDetailResult]:
    """Backward-compatible plural alias for get_ghost_detail."""

    return get_ghost_detail(ctx, vendor=vendor)
