"""Phase 1E write trigger REST endpoints."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from api.schemas.triggers import TriggerRequest, TriggerResponse
from db.recommendations_table import insert_recommendation
from mcp_server.actions import dispatch_csv, dispatch_jira, dispatch_slack
from processing.context_builder import build_context
from processing.ghost_detector import get_ghost_detail
from processing.reclamation_detector import get_reclamation_candidates
from processing.renewal_pressure_forecaster import get_renewal_pressure

router = APIRouter(prefix="/triggers", tags=["triggers"])


def _reclamation_rows(req: TriggerRequest):
    ctx = build_context(vendor=req.vendor)
    return get_reclamation_candidates(
        ctx,
        vendor=req.vendor,
        department=req.department,
        min_score=0.3,  # match what the UI actually shows
    )


def _trigger_response(
    req: TriggerRequest,
    count: int,
    dollar_impact: float,
    message: str,
    dispatch: dict | None = None,
    recommendation_id: str | None = None,
) -> TriggerResponse:
    return TriggerResponse(
        preview=not req.confirmed,
        vendor=req.vendor,
        department=req.department,
        count=count,
        dollar_impact=round(float(dollar_impact), 2),
        message=message,
        status="dispatched" if req.confirmed else None,
        integration=dispatch.get("integration") if dispatch else None,
        ticket_id=dispatch.get("ticket_id") if dispatch else None,
        recommendation_id=recommendation_id,
        db_status="pending" if recommendation_id else None,
    )


@router.post("/ghost-ticket", response_model=TriggerResponse)
def ghost_ticket(req: TriggerRequest) -> TriggerResponse:
    ctx = build_context(vendor=req.vendor)
    rows = get_ghost_detail(ctx, vendor=req.vendor, department=req.department)
    dollar_impact = sum(row.annual_cost for row in rows)
    count = len(rows)
    if not req.confirmed:
        return _trigger_response(
            req,
            count,
            dollar_impact,
            f"Found {count} ghost licenses worth ${dollar_impact:,.0f}/yr. Confirm to create a Jira ticket.",
        )

    payload = {
        "vendor": req.vendor,
        "action_type": "ghost_ticket",
        "seat_delta": -count,
        "dollar_impact": dollar_impact,
        "affected_records": [asdict(row) for row in rows],
        "recommended_action": "deprovision_review",
    }
    dispatch = dispatch_jira(payload)
    rec_id = insert_recommendation(payload)
    return _trigger_response(req, count, dollar_impact, dispatch.get("message", "Dispatched."), dispatch, rec_id)


@router.post("/reclamation", response_model=TriggerResponse)
def reclamation(req: TriggerRequest) -> TriggerResponse:
    rows = _reclamation_rows(req)
    dollar_impact = sum(row.annual_cost for row in rows)
    count = len(rows)
    if not req.confirmed:
        return _trigger_response(
            req,
            count,
            dollar_impact,
            f"Found {count} reclamation candidates worth ${dollar_impact:,.0f}/yr. Confirm to export CSV.",
        )

    payload = {
        "vendor": req.vendor,
        "action_type": "reclamation",
        "seat_delta": -count,
        "dollar_impact": dollar_impact,
        "affected_records": [asdict(row) for row in rows],
        "recommended_action": "reclaim",
    }
    dispatch = dispatch_csv(payload)
    rec_id = insert_recommendation(payload)
    return _trigger_response(req, count, dollar_impact, dispatch.get("path", "CSV exported."), dispatch, rec_id)


@router.post("/rightsizing", response_model=TriggerResponse)
def rightsizing(req: TriggerRequest) -> TriggerResponse:
    rows = _reclamation_rows(req)
    dollar_impact = sum(row.annual_cost for row in rows)
    count = len(rows)
    if not req.confirmed:
        return _trigger_response(
            req,
            count,
            dollar_impact,
            f"Found {count} rightsizing candidates worth ${dollar_impact:,.0f}/yr. Confirm to notify Slack.",
        )

    payload = {
        "vendor": req.vendor,
        "action_type": "rightsizing",
        "seat_delta": -count,
        "dollar_impact": dollar_impact,
        "affected_records": [asdict(row) for row in rows],
        "recommended_action": "rightsize",
    }
    dispatch = dispatch_slack(payload)
    rec_id = insert_recommendation(payload)
    return _trigger_response(req, count, dollar_impact, dispatch.get("message_ts", "Dispatched."), dispatch, rec_id)


@router.post("/renewal-alert", response_model=TriggerResponse)
def renewal_alert(req: TriggerRequest) -> TriggerResponse:
    ctx = build_context(vendor=req.vendor)
    rows = get_renewal_pressure(ctx, vendor=req.vendor)
    expired_rows = [r for r in rows if r.renewal_urgency == "expired"]
    critical_rows = [
        r
        for r in rows
        if r.pressure_classification == "critical" and r.renewal_urgency != "expired"
    ]
    total_exposure = sum(r.exposure_seats for r in rows)
    count = len(expired_rows) + len(critical_rows)
    dollar_impact = float(total_exposure)

    if not req.confirmed:
        return _trigger_response(
            req,
            count,
            dollar_impact,
            (
                f"{len(expired_rows)} expired and {len(critical_rows)} critical "
                f"contracts for {req.vendor}. {total_exposure} seats over entitlement. "
                "Confirm to send Slack alert."
            ),
        )

    payload = {
        "vendor": req.vendor,
        "action_type": "renewal_alert",
        "seat_delta": int(total_exposure),
        "dollar_impact": dollar_impact,
        "affected_records": [],
        "recommended_action": "alert",
        "expired_count": len(expired_rows),
        "critical_count": len(critical_rows),
        "total_exposure": total_exposure,
    }
    dispatch = dispatch_slack(payload)
    rec_id = insert_recommendation(payload)
    return _trigger_response(
        req,
        count,
        dollar_impact,
        dispatch.get("message", "Slack alert dispatched."),
        dispatch,
        rec_id,
    )


@router.post("/reclamation-review", response_model=TriggerResponse)
def reclamation_review(req: TriggerRequest) -> TriggerResponse:
    rows = _reclamation_rows(req)
    count = len(rows)
    dollar_impact = sum(row.annual_cost for row in rows)

    if not req.confirmed:
        return _trigger_response(
            req,
            count,
            dollar_impact,
            (
                f"Found {count} reclamation candidates worth "
                f"${dollar_impact:,.0f}/yr. Confirm to create Jira review ticket."
            ),
        )

    affected = [asdict(row) for row in rows[:50]]
    payload = {
        "vendor": req.vendor,
        "action_type": "reclamation_review",
        "seat_delta": -count,
        "dollar_impact": dollar_impact,
        "affected_records": affected,
        "recommended_action": "reclamation_review",
        "candidate_count": count,
        "department": req.department,
    }
    dispatch = dispatch_jira(payload)
    rec_id = insert_recommendation(payload)
    return _trigger_response(
        req,
        count,
        dollar_impact,
        dispatch.get("message", "Jira review ticket created."),
        dispatch,
        rec_id,
    )
