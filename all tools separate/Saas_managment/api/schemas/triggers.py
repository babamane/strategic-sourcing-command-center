"""Request and response schemas for Phase 1E write triggers."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TriggerRequest(BaseModel):
    vendor: str
    department: Optional[str] = None
    confirmed: bool = False


class TriggerResponse(BaseModel):
    preview: bool
    vendor: str
    department: Optional[str]
    count: int
    dollar_impact: float
    message: str
    status: Optional[str] = None
    integration: Optional[str] = None
    ticket_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    db_status: Optional[str] = None
