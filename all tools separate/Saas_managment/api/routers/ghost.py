"""Ghost license REST endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas.responses import GhostDetailResponse, GhostSummaryResponse
from processing.ghost_detector import get_ghost_detail, get_ghost_summary

router = APIRouter()


@router.get("/ghost/summary", response_model=list[GhostSummaryResponse])
async def ghost_summary(request: Request) -> list[GhostSummaryResponse]:
    ctx = request.state.ctx
    return [GhostSummaryResponse.model_validate(r) for r in get_ghost_summary(ctx)]


@router.get("/ghost/detail", response_model=list[GhostDetailResponse])
async def ghost_detail(request: Request, department: str | None = None) -> list[GhostDetailResponse]:
    ctx = request.state.ctx
    return [GhostDetailResponse.model_validate(r) for r in get_ghost_detail(ctx, vendor=None, department=department)]
