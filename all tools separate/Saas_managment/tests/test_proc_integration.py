from processing.breakdown_enricher import get_trueup_breakdown
from processing.context_builder import build_context
from processing.ghost_detector import get_ghost_details, get_ghost_summary
from processing.license_demand_forecaster import get_license_demand_forecast
from processing.renewal_pressure_forecaster import get_renewal_pressure
from processing.trueup_processor import get_trueup_exposure


def test_trueup_then_breakdown_nexaflow():
    ctx = build_context()
    exposure = [row for row in get_trueup_exposure(ctx, vendor="Nexaflow") if row.exposure_seats > 0]
    top = max(exposure, key=lambda row: row.exposure_seats)
    breakdown = get_trueup_breakdown(ctx, vendor=top.vendor, sku=top.sku, seat_type=top.seat_type)

    assert breakdown
    assert breakdown[0].by_department


def test_demand_forecast_uses_prehire_pipeline():
    ctx = build_context()

    assert any(row.expected_new_licenses > 0 for row in get_license_demand_forecast(ctx))


def test_renewal_pressure_expired_contracts_critical():
    ctx = build_context()
    expired = [row for row in get_renewal_pressure(ctx) if row.vendor in {"Nexaflow", "Cloudora"} and row.renewal_urgency == "expired"]

    assert expired
    assert all(row.pressure_classification == "critical" for row in expired)


def test_ghost_detector_excludes_prehire():
    ctx = build_context()
    future_ids = {row["employee_id"] for row in ctx.future_hires}

    assert not ({row.employee_id for row in get_ghost_details(ctx)} & future_ids)


def test_ghost_summary_count_matches_details():
    ctx = build_context()

    assert sum(row.ghost_license_count for row in get_ghost_summary(ctx)) == len(get_ghost_details(ctx))

