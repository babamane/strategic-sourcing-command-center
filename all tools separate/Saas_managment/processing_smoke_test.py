"""Concise smoke test for the Phase 1C processing layer."""

from __future__ import annotations

import logging

from processing.active_demand_processor import get_active_demand_history, get_active_demand_series
from processing.breakdown_enricher import get_trueup_breakdown
from processing.context_builder import build_context
from processing.ghost_detector import get_ghost_summary
from processing.license_demand_forecaster import get_license_demand_forecast
from processing.reclamation_detector import get_reclamation_candidates
from processing.renewal_pressure_forecaster import get_renewal_pressure
from processing.trueup_processor import get_trueup_exposure
from processing.utilization_aggregator import get_utilization_summary


def _assert_rows(label: str, rows: list[object]) -> None:
    assert rows, f"{label} returned no rows"
    assert all(hasattr(row, "computed_at") for row in rows), f"{label} rows missing computed_at"
    print(f"{label}: {len(rows)} rows")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    ctx = build_context()
    _assert_rows("trueup", get_trueup_exposure(ctx))
    _assert_rows("breakdown", get_trueup_breakdown(ctx))
    _assert_rows("ghost", get_ghost_summary(ctx))
    _assert_rows("reclamation", get_reclamation_candidates(ctx))
    _assert_rows("utilization", get_utilization_summary(ctx))
    _assert_rows("active_demand_history", get_active_demand_history(ctx))
    active_demand_series = get_active_demand_series(ctx)
    _assert_rows("active_demand_series", active_demand_series)
    assert any(not row.is_forecast for row in active_demand_series), "active_demand_series missing historical rows"
    assert any(row.is_forecast for row in active_demand_series), "active_demand_series missing forecast rows"
    _assert_rows("demand_forecast", get_license_demand_forecast(ctx))
    _assert_rows("renewal_pressure", get_renewal_pressure(ctx))
    print("Phase 1C processing smoke checks complete.")


if __name__ == "__main__":
    main()
