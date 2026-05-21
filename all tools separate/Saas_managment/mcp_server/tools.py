"""FastMCP tool definitions for the SaaS spend assistant."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from mcp_server.actions import dispatch_jira, dispatch_slack
from mcp_server.server import mcp
from db.recommendations_table import insert_recommendation
from processing.breakdown_enricher import get_trueup_breakdown as proc_get_trueup_breakdown
from processing.active_demand_processor import get_active_demand_series as proc_get_active_demand_series
from processing.context_builder import build_context
from processing.ghost_detector import get_ghost_detail as proc_get_ghost_detail
from processing.ghost_detector import get_ghost_summary as proc_get_ghost_summary
from processing.license_demand_forecaster import (
    get_license_demand_forecast as proc_get_license_demand_forecast,
)
from processing.reclamation_detector import get_reclamation_candidates as proc_get_reclamation_candidates
from processing.renewal_pressure_forecaster import get_renewal_pressure as proc_get_renewal_pressure
from processing.trueup_processor import get_trueup_exposure as proc_get_trueup_exposure
from processing.utilization_aggregator import get_utilization_summary as proc_get_utilization_summary


@mcp.tool()
def get_trueup_exposure(vendor: Optional[str] = None) -> list[dict[str, Any]]:
    """Shows which vendors are over-provisioned beyond contract and the annual cost of that exposure.
    Omit vendor to see all vendors."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_trueup_exposure(ctx, vendor=vendor)]


@mcp.tool()
def get_trueup_breakdown(
    vendor: Optional[str] = None,
    sku: Optional[str] = None,
    seat_type: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Breaks down true-up exposure by SKU and seat type for a specific vendor.
    Omit vendor for portfolio-wide rows."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_trueup_breakdown(ctx, vendor=vendor, sku=sku, seat_type=seat_type)]


@mcp.tool()
def get_ghost_summary(vendor: Optional[str] = None) -> list[dict[str, Any]]:
    """Shows licenses still assigned to employees who have left the company, grouped by vendor.
    Omit vendor for all vendors."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_ghost_summary(ctx, vendor=vendor)]


@mcp.tool()
def get_ghost_detail(vendor: Optional[str] = None, department: Optional[str] = None) -> list[dict[str, Any]]:
    """Lists individual ghost license holders for a vendor and optional department.
    Omit vendor for portfolio-level detail."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_ghost_detail(ctx, vendor=vendor, department=department)]


@mcp.tool()
def get_reclamation_candidates(
    vendor: Optional[str] = None,
    department: Optional[str] = None,
    min_score: float = 0.45,
) -> list[dict[str, Any]]:
    """Returns active licenses with low utilization ranked by reclamation score (ghost licenses excluded).
    Omit vendor for all vendors."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_reclamation_candidates(ctx, vendor=vendor, department=department, min_score=min_score)]


@mcp.tool()
def get_utilization_summary(vendor: Optional[str] = None) -> list[dict[str, Any]]:
    """Shows active usage rates, shelfware, and dormant license counts per vendor.
    Omit vendor for portfolio-wide results."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_utilization_summary(ctx, vendor=vendor)]


@mcp.tool()
def get_renewal_pressure(vendor: Optional[str] = None) -> list[dict[str, Any]]:
    """Shows which vendor contracts are approaching notice deadlines or have already expired,
    including the projected active license count at the notice deadline.
    Omit vendor for all vendors."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_renewal_pressure(ctx, vendor=vendor)]


@mcp.tool()
def get_license_demand_forecast(
    vendor: Optional[str] = None,
    department: Optional[str] = None,
    forecast_months: int = 8,
) -> list[dict[str, Any]]:
    """Forecasts how many licenses will be needed over the next N months based on confirmed hires.
    Omit vendor for portfolio-wide results."""

    ctx = build_context(vendor=vendor, version=None)
    return [
        asdict(r)
        for r in proc_get_license_demand_forecast(
            ctx, vendor=vendor, department=department, forecast_months=forecast_months
        )
    ]


@mcp.tool()
def get_active_demand(
    vendor: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Returns the active license demand history and forward projection for the portfolio
    or a specific vendor. Historical months show observed active license counts.
    Forecast months show projected counts based on confirmed incoming hires. Each
    row includes contracted capacity so you can see where demand exceeds contract limits."""

    ctx = build_context(vendor=vendor, version=None)
    return [asdict(r) for r in proc_get_active_demand_series(ctx, vendor=vendor)]


def _vendor_label(vendor: Optional[str], rows: list[Any], vendor_attr: str = "vendor") -> str:
    if vendor:
        return vendor
    vendors = {getattr(r, vendor_attr) for r in rows if getattr(r, vendor_attr, None)}
    if len(vendors) == 1:
        return next(iter(vendors))
    return "portfolio"


@mcp.tool()
def trigger_reclamation_review(
    vendor: Optional[str] = None,
    department: Optional[str] = None,
    min_score: float = 0.7,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Prepares or confirms a Jira review ticket for active licenses with low utilization (ghosts excluded)."""

    ctx = build_context(vendor=vendor, version=None)
    rows = proc_get_reclamation_candidates(ctx, vendor=vendor, department=department, min_score=min_score)
    dollar = round(sum(r.annual_cost for r in rows), 2)
    seat_delta = -len(rows)
    vlabel = _vendor_label(vendor, rows)
    if not confirmed:
        return {
            "preview": True,
            "vendor": vlabel,
            "candidate_count": len(rows),
            "dollar_impact": dollar,
            "seat_delta": seat_delta,
            "message": (
                f"Found {len(rows)} reclamation candidates for {vlabel} "
                f"with score >= {min_score}, worth about ${dollar:,.0f}/yr in annual license cost. "
                "Call again with confirmed=true after the user approves to open a Jira ticket."
            ),
        }
    payload: dict[str, Any] = {
        "vendor": vlabel,
        "action_type": "reclamation",
        "seat_delta": seat_delta,
        "dollar_impact": float(dollar),
        "affected_records": [asdict(r) for r in rows],
        "recommended_action": "reclaim",
    }
    dispatch = dispatch_jira(payload)
    rid = insert_recommendation(payload)
    return {
        "status": "dispatched",
        "integration": "jira",
        **{k: v for k, v in dispatch.items() if k not in {"status"}},
        "recommendation_id": rid,
        "db_status": "pending",
    }


@mcp.tool()
def trigger_renewal_alert(
    vendor: Optional[str] = None,
    days_threshold: int = 30,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Prepares or confirms a Slack alert for contracts close to or past their notice deadline."""

    ctx = build_context(vendor=vendor, version=None)
    rows = [
        r
        for r in proc_get_renewal_pressure(ctx, vendor=vendor)
        if r.days_until_notice_deadline <= days_threshold
    ]
    dollar = round(sum(float(r.pressure_score) for r in rows), 2)
    seat_delta = sum(int(r.exposure_seats or 0) for r in rows)
    vlabel = _vendor_label(vendor, rows)
    if not confirmed:
        return {
            "preview": True,
            "vendor": vlabel,
            "contract_rows": len(rows),
            "dollar_impact": dollar,
            "seat_delta": seat_delta,
            "message": (
                f"Found {len(rows)} renewal-pressure rows for {vlabel} within {days_threshold} days of notice. "
                "Call again with confirmed=true after approval to post to Slack."
            ),
        }
    payload = {
        "vendor": vlabel,
        "action_type": "renewal_alert",
        "seat_delta": seat_delta,
        "dollar_impact": float(dollar),
        "affected_records": [asdict(r) for r in rows],
        "recommended_action": "alert",
    }
    dispatch = dispatch_slack(payload)
    rid = insert_recommendation(payload)
    return {
        "status": "dispatched",
        "integration": "slack",
        **{k: v for k, v in dispatch.items() if k not in {"status"}},
        "recommendation_id": rid,
        "db_status": "pending",
    }


@mcp.tool()
def trigger_ghost_ticket(
    vendor: str,
    department: Optional[str] = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Prepares or confirms a Jira ticket listing ghost licenses for one vendor."""

    ctx = build_context(vendor=vendor, version=None)
    rows = proc_get_ghost_detail(ctx, vendor=vendor, department=department)
    dollar = round(sum(r.annual_cost for r in rows), 2)
    seat_delta = -len(rows)
    if not confirmed:
        return {
            "preview": True,
            "vendor": vendor,
            "department": department,
            "ghost_count": len(rows),
            "dollar_impact": dollar,
            "seat_delta": seat_delta,
            "message": (
                f"Found {len(rows)} ghost licenses"
                + (f" in {department}" if department else "")
                + f" at {vendor} worth about ${dollar:,.0f}/yr. "
                "Call again with confirmed=true to create the Jira ticket."
            ),
        }
    payload = {
        "vendor": vendor,
        "action_type": "ghost_review",
        "seat_delta": seat_delta,
        "dollar_impact": float(dollar),
        "affected_records": [asdict(r) for r in rows],
        "recommended_action": "deprovision_review",
    }
    dispatch = dispatch_jira(payload)
    rid = insert_recommendation(payload)
    return {
        "status": "dispatched",
        "integration": "jira",
        **{k: v for k, v in dispatch.items() if k not in {"status"}},
        "recommendation_id": rid,
        "db_status": "pending",
    }


@mcp.tool()
def send_churn_notification(
    vendor: str,
    department: Optional[str] = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Preview or send a churn notification email for inactive license holders.
    Recipient is configured server-side; use confirmed=False for preview."""

    from services.mail_service import send_churn_notification as _send

    ctx = build_context(vendor=vendor, version=None)
    rows = proc_get_reclamation_candidates(ctx, vendor=vendor, department=department)
    candidates = [asdict(row) for row in rows]
    dollar_impact = sum(row.annual_cost for row in rows)
    result = _send(
        vendor=vendor,
        department=department,
        candidates=candidates,
        dollar_impact=dollar_impact,
        preview_only=not confirmed,
    )
    if confirmed and result.get("sent"):
        rid = insert_recommendation(
            {
                "vendor": vendor,
                "action_type": "churn_mail",
                "seat_delta": -len(candidates),
                "dollar_impact": dollar_impact,
                "affected_records": candidates,
                "recommended_action": "notify_churn",
            }
        )
        result["recommendation_id"] = rid
        result["db_status"] = "pending"
    return result
