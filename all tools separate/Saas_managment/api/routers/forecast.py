"""Forecast REST endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas.responses import (
    ActiveDemandHistoryResponse,
    ActiveDemandPointResponse,
    LicenseDemandForecastResponse,
)
from processing.active_demand_processor import get_active_demand_history, get_active_demand_series
from processing.license_demand_forecaster import get_license_demand_forecast

router = APIRouter()


@router.get("/forecast/demand", response_model=list[LicenseDemandForecastResponse])
async def forecast_demand(
    request: Request,
    department: str | None = None,
    months: int = 8,
) -> list[LicenseDemandForecastResponse]:
    ctx = request.state.ctx
    rows = get_license_demand_forecast(ctx, vendor=None, department=department, forecast_months=months)
    return [LicenseDemandForecastResponse.model_validate(r) for r in rows]


@router.get("/forecast/active-demand", response_model=list[ActiveDemandHistoryResponse])
async def forecast_active_demand(request: Request) -> list[ActiveDemandHistoryResponse]:
    ctx = request.state.ctx
    rows = get_active_demand_history(ctx, vendor=None)
    return [ActiveDemandHistoryResponse.model_validate(r) for r in rows]


@router.get("/forecast/active-demand-series", response_model=list[ActiveDemandPointResponse])
async def forecast_active_demand_series(request: Request) -> list[ActiveDemandPointResponse]:
    ctx = request.state.ctx
    rows = get_active_demand_series(ctx, vendor=None)
    return [ActiveDemandPointResponse.model_validate(r) for r in rows]
