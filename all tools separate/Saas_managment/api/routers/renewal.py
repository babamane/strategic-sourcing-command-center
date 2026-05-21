"""Renewal pressure REST endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas.responses import RenewalPressureResponse
from processing.renewal_pressure_forecaster import get_renewal_pressure

router = APIRouter()


@router.get("/renewal-pressure", response_model=list[RenewalPressureResponse])
async def renewal_pressure(request: Request) -> list[RenewalPressureResponse]:
    ctx = request.state.ctx
    return [RenewalPressureResponse.model_validate(r) for r in get_renewal_pressure(ctx)]
