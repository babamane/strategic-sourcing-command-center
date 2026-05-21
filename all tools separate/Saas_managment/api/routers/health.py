"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    ctx = request.state.ctx
    return HealthResponse(audit_date=ctx.audit_date, active_vendors=list(ctx.active_vendors), fetched_at=ctx.fetched_at)
