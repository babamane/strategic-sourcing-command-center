"""Typed output shapes for forecasting processors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveDemandHistory:
    vendor: str
    sku: str
    seat_type: str
    month: str
    productive_active: int
    vendor_billed: int
    ghost_count: int
    contracted_capacity: int
    over_capacity: bool
    computed_at: str


@dataclass(frozen=True)
class ActiveDemandPoint:
    vendor: str
    sku: str
    seat_type: str
    month: str
    is_forecast: bool
    productive_active: int
    vendor_billed: int
    ghost_count: int
    projected_active: float
    contracted_capacity: int
    projected_over_capacity: float
    pipeline_data_available: bool
    computed_at: str


@dataclass(frozen=True)
class LicenseDemandForecast:
    vendor: str
    sku: str
    seat_type: str
    forecast_month: str
    expected_new_licenses: float
    baseline_active: int
    projected_active: float
    contracted_capacity: int
    projected_over_capacity: float
    exit_licenses_applied: float
    pipeline_data_available: bool
    by_department: list[dict]
    rate_grain_applied: str
    exit_model_applied: bool
    computed_at: str


@dataclass(frozen=True)
class ForecastUnavailableResult:
    vendor: str
    sku: str
    seat_type: str
    reason: str
    model_version: str
    computed_at: str
