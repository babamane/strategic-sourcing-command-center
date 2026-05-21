"""Pydantic schema for vendor contract records."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class VendorContract(BaseModel):
    of_id: str
    vendor: str
    sku: str
    seat_type: str
    contracted_seats: int
    effective_total_seats: int
    unit_price: float
    contract_start: date
    contract_expiry: date
    notice_deadline: date
    auto_renewal: bool
    true_down_rights: bool
    measurement_method: str
    contract_status: str
    contract_event_type: str
    contract_group_id: Optional[str] = None
    predecessor_of_id: Optional[str] = None
    seat_delta: Optional[int] = None

