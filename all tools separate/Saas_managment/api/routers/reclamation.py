"""Reclamation candidates REST endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas.responses import ReclamationResponse
from processing.reclamation_detector import get_reclamation_candidates

router = APIRouter()


@router.get("/reclamation", response_model=list[ReclamationResponse])
async def reclamation(
    request: Request,
    department: str | None = None,
    min_score: float = 0.45,
) -> list[ReclamationResponse]:
    ctx = request.state.ctx
    rows = get_reclamation_candidates(ctx, vendor=None, department=department, min_score=min_score)
    return [ReclamationResponse.model_validate(r) for r in rows]
