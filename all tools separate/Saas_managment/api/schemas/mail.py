"""Request and response schemas for Phase 1E mail endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ChurnMailRequest(BaseModel):
    vendor: str
    department: Optional[str] = None
    confirmed: bool = False


class ChurnMailResponse(BaseModel):
    preview: bool
    recipient: str
    subject: str
    body_preview: Optional[str] = None
    candidate_count: int
    dollar_impact: float
    sent: Optional[bool] = None
    recommendation_id: Optional[str] = None
    error: Optional[str] = None
