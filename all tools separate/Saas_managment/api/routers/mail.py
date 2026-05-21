"""Phase 1E mail REST endpoints."""

from __future__ import annotations

from dataclasses import asdict
import smtplib

from fastapi import APIRouter

from api.schemas.mail import ChurnMailRequest, ChurnMailResponse
from db.recommendations_table import insert_recommendation
from processing.context_builder import build_context
from processing.reclamation_detector import get_reclamation_candidates
from services.mail_service import send_churn_notification

router = APIRouter(prefix="/mail", tags=["mail"])


@router.post("/churn-notification", response_model=ChurnMailResponse)
def churn_notification(req: ChurnMailRequest) -> ChurnMailResponse:
    ctx = build_context(vendor=req.vendor)
    candidates = get_reclamation_candidates(ctx, vendor=req.vendor, department=req.department)
    candidate_dicts = [asdict(row) for row in candidates]
    dollar_impact = sum(row.annual_cost for row in candidates)

    try:
        result = send_churn_notification(
            vendor=req.vendor,
            department=req.department,
            candidates=candidate_dicts,
            dollar_impact=dollar_impact,
            preview_only=not req.confirmed,
        )
    except (KeyError, smtplib.SMTPException) as exc:
        return ChurnMailResponse(
            preview=False,
            recipient="",
            subject="",
            candidate_count=0,
            dollar_impact=0,
            sent=False,
            error=str(exc),
        )

    rec_id = None
    if req.confirmed and result.get("sent"):
        rec_id = insert_recommendation(
            {
                "vendor": req.vendor,
                "action_type": "churn_mail",
                "seat_delta": -len(candidate_dicts),
                "dollar_impact": dollar_impact,
                "affected_records": candidate_dicts,
                "recommended_action": "notify_churn",
            }
        )

    return ChurnMailResponse(
        preview=result["preview"],
        recipient=result["recipient"],
        subject=result["subject"],
        body_preview=result.get("body_preview"),
        candidate_count=result["candidate_count"],
        dollar_impact=result["dollar_impact"],
        sent=result.get("sent"),
        recommendation_id=rec_id,
    )
