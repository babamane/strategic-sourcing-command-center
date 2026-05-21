"""Facade that builds ProcessingContext objects from service-layer data."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from services.contract_service import get_active_contracts, get_contract_history, get_entitlement
from services.employee_service import get_active_employees, get_exited_employees, get_future_hires
from services.ingestion_service import get_discovered_values
from services.license_service import get_raw_licenses

AUDIT_DATE: str = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

def _get_active_vendors() -> list[str]:
    """Resolve active vendors dynamically from environment."""
    return [v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()]

CACHE_TTL_SECONDS = 60


@dataclass(frozen=True)
class ProcessingContext:
    licenses: list[dict]
    entitlement: list[dict]
    active_contracts: list[dict]
    contract_history: list[dict]
    active_employees: list[dict]
    exited_employees: list[dict]
    future_hires: list[dict]
    known_departments: list[str]
    known_job_levels: list[str]
    audit_date: str
    active_vendors: list[str]
    fetched_at: str


_context_cache: dict[tuple[Any, Any], tuple[ProcessingContext, datetime]] = {}


def clear_context_cache() -> None:
    """Clear cached processing contexts after data promotion."""

    _context_cache.clear()


def _build_fresh_context(vendor: Optional[str] = None, version: Optional[int] = None) -> ProcessingContext:
    """Fetch service data once and assemble the processing-layer data contract."""

    from exceptions import DataNotReadyError

    def _safe_call(func, **kwargs):
        try:
            return func(**kwargs)
        except DataNotReadyError:
            return []

    return ProcessingContext(
        licenses=_safe_call(get_raw_licenses, vendor=vendor, version=version, include_effective_license_date=True),
        entitlement=_safe_call(get_entitlement, vendor=vendor, version=version),
        active_contracts=_safe_call(get_active_contracts, vendor=vendor, version=version),
        contract_history=_safe_call(get_contract_history, vendor=vendor, version=version),
        active_employees=_safe_call(get_active_employees, version=version),
        exited_employees=_safe_call(get_exited_employees, version=version),
        future_hires=_safe_call(get_future_hires, version=version),
        known_departments=_safe_call(get_discovered_values, table_name="hr_headcount", column_name="department"),
        known_job_levels=_safe_call(get_discovered_values, table_name="hr_headcount", column_name="job_level"),
        audit_date=AUDIT_DATE,
        active_vendors=_get_active_vendors() if vendor is None else [vendor],
        fetched_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def build_context(vendor: Optional[str] = None, version: Optional[int] = None) -> ProcessingContext:
    """Return a processing context, using a short-lived in-process cache."""

    key = (vendor, version)
    cached, cached_at = _context_cache.get(key, (None, None))
    if cached is not None and cached_at is not None:
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return cached
    ctx = _build_fresh_context(vendor=vendor, version=version)
    _context_cache[key] = (ctx, datetime.now(timezone.utc))
    return ctx
