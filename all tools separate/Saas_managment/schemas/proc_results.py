"""Typed output shapes for Phase 1C processing results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrueUpResult:
    vendor: str
    sku: str
    seat_type: str
    effective_total_seats: int
    active_provisioned_seats: int
    exposure_seats: int
    shelfware_seats: int
    unit_price: float
    exposure_amount_monthly: float
    shelfware_amount_monthly: float
    exposure_amount_annual: float
    shelfware_amount_annual: float
    portfolio_ratio: float
    notice_deadline: str
    days_until_notice_deadline: int
    auto_renewal: bool
    true_down_rights: bool
    measurement_method: str
    renewal_urgency: str
    computed_at: str


@dataclass(frozen=True)
class TrueUpBreakdownResult:
    vendor: str
    sku: str
    seat_type: str
    total_provisioned: int
    effective_total_seats: int
    exposure_seats: int
    by_department: list[dict]
    by_job_level: list[dict]
    top_departments: list[dict]
    computed_at: str


@dataclass(frozen=True)
class GhostSummaryResult:
    vendor: str
    ghost_license_count: int
    total_cost_at_risk_monthly: float
    total_cost_at_risk_annual: float
    avg_days_orphaned: float
    max_days_orphaned: int
    by_department: list[dict]
    computed_at: str


@dataclass(frozen=True)
class GhostDetailResult:
    license_id: str
    vendor: str
    sku: str
    seat_type: str
    employee_id: str
    email: str
    department: str
    job_level: str
    exit_date: str
    exit_type: str
    days_orphaned: int
    monthly_cost: float
    cost_at_risk: float
    annual_cost: float
    days_since_last_active: float
    computed_at: str


@dataclass(frozen=True)
class ReclamationResult:
    license_id: str
    vendor: str
    sku: str
    seat_type: str
    employee_id: str
    email: str
    department: str
    job_level: str
    license_status: str
    usage_tier: str
    days_since_last_active: float
    seat_tier_match: str
    monthly_cost: float
    annual_cost: float
    reclamation_score: float
    reclamation_candidate_flag: bool
    computed_at: str


@dataclass(frozen=True)
class UtilizationResult:
    vendor: str
    sku: str
    seat_type: str
    total_licenses: int
    by_usage_tier: dict[str, int]
    active_rate: float
    waste_rate: float
    total_monthly_cost: float
    computed_at: str


@dataclass(frozen=True)
class DemandForecastResult:
    vendor: str
    sku: str
    seat_type: str
    department: str
    incoming_hires: int
    provisioning_rate: float
    expected_new_licenses: int
    low_confidence: bool
    exit_model_applied: bool
    hire_window_start: str
    hire_window_end: str
    computed_at: str


@dataclass(frozen=True)
class RenewalPressureResult:
    vendor: str
    sku: str
    seat_type: str
    of_id: str
    contract_expiry: str
    notice_deadline: str
    days_until_notice_deadline: int
    renewal_urgency: str
    auto_renewal: bool
    true_down_rights: bool
    current_provisioned: int
    effective_total_seats: int
    exposure_seats: int
    hires_before_deadline: int  # Projected active licenses at the latest forecast month before notice deadline.
    hires_by_department: list[dict]
    urgency_score: float
    growth_score: float
    exposure_score: float
    pressure_score: float
    pressure_classification: str
    exit_model_applied: bool
    computed_at: str
