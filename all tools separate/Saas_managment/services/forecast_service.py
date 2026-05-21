"""Phase 1B forecast service stub."""

from __future__ import annotations

from typing import Optional


def get_renewal_pressure(
    vendor: Optional[str] = None,
    version: Optional[int] = None,
) -> list[dict]:
    raise NotImplementedError("forecast_service.get_renewal_pressure is implemented in Phase 1C")


def get_pressure_summary(
    vendor: Optional[str] = None,
    version: Optional[int] = None,
) -> dict:
    raise NotImplementedError("forecast_service.get_pressure_summary is implemented in Phase 1C")


def get_headcount_driven_demand(
    vendor: str,
    sku: str,
    seat_type: str,
    version: Optional[int] = None,
) -> list[dict]:
    raise NotImplementedError("forecast_service.get_headcount_driven_demand is implemented in Phase 1C")

