from dataclasses import replace

from processing.context_builder import build_context
from schemas.proc_forecast_results import LicenseDemandForecast
import processing.renewal_pressure_forecaster as renewal_pressure_forecaster
from processing.renewal_pressure_forecaster import get_renewal_pressure


def test_renewal_pressure_scores_contracts():
    ctx = build_context()
    rows = get_renewal_pressure(ctx)

    assert rows
    assert all(row.computed_at for row in rows)
    assert all(0 <= row.pressure_score <= 1 for row in rows)
    assert all(row.hires_by_department == [] for row in rows)
    assert all(row.growth_score in {0.0, 0.2, 0.4} for row in rows)
    assert rows == sorted(rows, key=lambda row: row.pressure_score, reverse=True)
    assert {row.vendor for row in get_renewal_pressure(ctx, vendor="Nexaflow")} == {"Nexaflow"}
    assert get_renewal_pressure(ctx, vendor="NotAVendor") == []


def test_expired_contracts_are_critical():
    ctx = build_context()
    rows = [row for row in get_renewal_pressure(ctx) if row.renewal_urgency == "expired"]

    assert rows
    assert all(row.pressure_classification == "critical" for row in rows)


def test_growth_score_uses_demand_forecast(monkeypatch):
    ctx = build_context()
    key = ("Atlassify", "Project Suite", "Collaborator")
    contracts = [
        {
            **contract,
            "notice_deadline": "2026-07-31" if (contract["vendor"], contract["sku"], contract["seat_type"]) == key else contract.get("notice_deadline"),
        }
        for contract in ctx.active_contracts
    ]
    ctx = replace(ctx, active_contracts=contracts)
    current = sum(
        1
        for row in ctx.licenses
        if (row["vendor"], row["sku"], row["seat_type"]) == key
        and row.get("license_status") in {"active", "over_tier"}
    )
    demand_row = LicenseDemandForecast(
        vendor=key[0],
        sku=key[1],
        seat_type=key[2],
        forecast_month="2026-06",
        expected_new_licenses=round(current * 0.06, 2),
        baseline_active=current,
        projected_active=round(current * 1.06, 2),
        contracted_capacity=current,
        projected_over_capacity=round(max(0.0, current * 0.06), 2),
        exit_licenses_applied=0.0,
        pipeline_data_available=True,
        by_department=[],
        rate_grain_applied="dept_level",
        exit_model_applied=False,
        computed_at="2026-05-14T00:00:00+00:00",
    )
    monkeypatch.setattr(
        renewal_pressure_forecaster,
        "get_license_demand_forecast",
        lambda ctx, forecast_months=8: [demand_row],
    )

    rows = [
        row
        for row in get_renewal_pressure(ctx, vendor="Atlassify")
        if (row.vendor, row.sku, row.seat_type) == key
    ]

    assert rows
    assert rows[0].growth_score > 0.0
