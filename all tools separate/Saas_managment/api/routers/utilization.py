"""Utilization REST endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas.responses import UtilizationResponse
from processing.utilization_aggregator import get_utilization_summary

router = APIRouter()


@router.get("/utilization", response_model=list[UtilizationResponse])
async def utilization(request: Request) -> list[UtilizationResponse]:
    ctx = request.state.ctx
    return [UtilizationResponse.model_validate(r) for r in get_utilization_summary(ctx)]
