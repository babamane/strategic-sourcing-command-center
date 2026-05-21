"""True-up exposure and breakdown REST endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas.responses import TrueUpBreakdownResponse, TrueUpExposureResponse
from processing.breakdown_enricher import get_trueup_breakdown
from processing.trueup_processor import get_trueup_exposure

router = APIRouter()


@router.get("/trueup/exposure", response_model=list[TrueUpExposureResponse])
async def trueup_exposure(request: Request) -> list[TrueUpExposureResponse]:
    ctx = request.state.ctx
    return [TrueUpExposureResponse.model_validate(r) for r in get_trueup_exposure(ctx)]


@router.get("/trueup/breakdown", response_model=list[TrueUpBreakdownResponse])
async def trueup_breakdown(
    request: Request,
    sku: str | None = None,
    seat_type: str | None = None,
) -> list[TrueUpBreakdownResponse]:
    ctx = request.state.ctx
    rows = get_trueup_breakdown(ctx, vendor=None, sku=sku, seat_type=seat_type)
    return [TrueUpBreakdownResponse.model_validate(r) for r in rows]
