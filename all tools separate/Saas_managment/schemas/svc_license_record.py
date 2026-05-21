"""Pydantic schema for license utilization records."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class LicenseRecord(BaseModel):
    license_id: str
    of_id: str
    current_of_id: str
    vendor: str
    sku: str
    seat_type: str
    assigned_email: str
    employee_id: str
    department: str
    job_level: str
    license_status: str
    usage_tier: str
    seat_tier_match: str
    monthly_cost: float
    cost_at_risk: float
    reclamation_candidate: bool
    renewal_urgency: str
    days_until_notice: int
    contract_days_remaining: int
    notice_deadline: Optional[date] = None
    auto_renewal: bool = False
    true_down_rights: bool = False
    measurement_method: str = ""
    churn_risk_score: Optional[float] = None
    active_usage_rate: Optional[float] = None
    login_events_30d: Optional[int] = None
    days_since_last_active: Optional[float] = None
    last_active_date: Optional[date] = None
    days_since_provisioned: Optional[int] = None
    license_age_band: Optional[str] = None
    tenure_days: Optional[int] = None
    hire_cohort_year: Optional[int] = None
    hire_cohort_half: Optional[str] = None
    annual_cost: Optional[float] = None
    provisioned_date: Optional[date] = None
    effective_license_date: Optional[date] = None

