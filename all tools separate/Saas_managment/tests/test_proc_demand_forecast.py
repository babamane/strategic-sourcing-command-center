from dataclasses import replace

from processing.active_demand_processor import get_active_demand_history, get_active_demand_series
from processing.context_builder import build_context
from processing.license_demand_forecaster import get_license_demand_forecast
from schemas.proc_forecast_results import ActiveDemandHistory


def test_active_demand_history_returns_rows():
    ctx = build_context()
    rows = get_active_demand_history(ctx)

    assert rows
    assert all(isinstance(row, ActiveDemandHistory) for row in rows)
    assert all(row.productive_active >= 0 for row in rows)
    assert all(row.ghost_count >= 0 for row in rows)
    assert all(row.vendor_billed >= row.productive_active for row in rows)


def test_active_demand_history_vendor_filter():
    ctx = build_context()
    rows = get_active_demand_history(ctx, vendor="Cloudora")

    assert rows
    assert {row.vendor for row in rows} == {"Cloudora"}


def test_active_demand_history_over_capacity_flag():
    ctx = build_context()
    rows = get_active_demand_history(ctx)

    assert rows
    assert all(row.over_capacity == (row.productive_active > row.contracted_capacity) for row in rows)
    assert any(not row.over_capacity for row in rows)


def test_active_demand_history_month_range_complete():
    ctx = build_context()
    rows = get_active_demand_history(ctx, vendor="Atlassify")

    assert rows
    first_series = [row for row in rows if (row.vendor, row.sku, row.seat_type) == (rows[0].vendor, rows[0].sku, rows[0].seat_type)]
    months = [row.month for row in first_series]
    assert months
    assert months == sorted(months)

    year, month = map(int, months[0].split("-"))
    for current_month in months[1:]:
        month += 1
        if month == 13:
            year += 1
            month = 1
        assert current_month == f"{year:04d}-{month:02d}"


def test_active_demand_series_no_gap_at_audit_date():
    ctx = build_context()
    rows = get_active_demand_series(ctx, vendor="Atlassify")

    assert rows
    audit_month = ctx.audit_date[:7]
    series_rows = [row for row in rows if (row.vendor, row.sku, row.seat_type) == (rows[0].vendor, rows[0].sku, rows[0].seat_type)]
    months = [row.month for row in series_rows]
    assert len(months) == len(set(months))
    assert max(row.month for row in series_rows if not row.is_forecast) == audit_month
    assert min(row.month for row in series_rows if row.is_forecast) == "2026-06"


def test_active_demand_series_historical_rows_not_forecast():
    ctx = build_context()
    rows = get_active_demand_series(ctx)
    audit_month = ctx.audit_date[:7]

    assert rows
    assert all(not row.is_forecast for row in rows if row.month <= audit_month)


def test_active_demand_series_forecast_rows_flagged():
    ctx = build_context()
    rows = get_active_demand_series(ctx)
    audit_month = ctx.audit_date[:7]

    assert rows
    assert all(row.is_forecast for row in rows if row.month > audit_month)


def test_active_demand_series_projected_active_continuous():
    ctx = build_context()
    rows = get_active_demand_series(ctx, vendor="Atlassify")
    audit_month = ctx.audit_date[:7]
    next_month = "2026-06"
    target_key = next(
        (row.vendor, row.sku, row.seat_type)
        for row in rows
        if row.month == next_month and row.is_forecast
    )
    series_rows = [row for row in rows if (row.vendor, row.sku, row.seat_type) == target_key]
    last_historical = max((row for row in series_rows if not row.is_forecast), key=lambda row: row.month)
    first_forecast = min((row for row in series_rows if row.is_forecast), key=lambda row: row.month)

    assert last_historical.month == audit_month
    assert first_forecast.month == next_month
    assert last_historical.projected_active == first_forecast.projected_active


def test_demand_forecast_uses_future_hires():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx)

    assert rows
    assert all(row.computed_at for row in rows)
    assert any(row.expected_new_licenses > 0 for row in rows)
    assert all(row.exit_model_applied is False for row in rows)
    assert {row.vendor for row in get_license_demand_forecast(ctx, vendor="Cloudora")} == {"Cloudora"}
    assert get_license_demand_forecast(ctx, vendor="NotAVendor") == []


def test_demand_forecast_zero_aug_dec_and_metadata():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx, forecast_months=8)

    assert rows
    assert {row.forecast_month for row in rows} == {
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
        "2026-10",
        "2026-11",
        "2026-12",
    }
    assert all(row.expected_new_licenses == 0 for row in rows if row.forecast_month >= "2026-08")
    assert any(row.by_department for row in rows if row.forecast_month <= "2026-07")
    assert all(row.rate_grain_applied in {"dept_level", "dept_only", "portfolio"} for row in rows)


def test_by_department_uses_sub_team_grain_internally():
    ctx = build_context()
    license_row = next(
        row
        for row in ctx.licenses
        if row.get("vendor") == "Atlassify"
        and row.get("department") == "Engineering"
        and row.get("license_status") in {"active", "over_tier"}
    )
    employee = next(
        row
        for row in ctx.active_employees
        if row.get("employee_id") == license_row.get("employee_id") and row.get("sub_team")
    )
    ctx = replace(
        ctx,
        future_hires=[
            {
                "employee_id": "TEST-PREHIRE-001",
                "email": "test.prehire@example.com",
                "department": "Engineering",
                "sub_team": employee["sub_team"],
                "job_level": "L1",
                "region": employee.get("region"),
                "hire_date": "2026-05-15",
                "employee_status": "pre-hire",
            }
        ],
    )

    rows = [
        row
        for row in get_license_demand_forecast(ctx, vendor="Atlassify", forecast_months=3)
        if row.sku == license_row["sku"]
        and row.seat_type == license_row["seat_type"]
        and row.forecast_month == "2026-05"
    ]

    assert len(rows) == 1
    engineering = [entry for entry in rows[0].by_department if entry["department"] == "Engineering"]
    assert len(engineering) == 1
    assert engineering[0]["expected_licenses"] > 0


def test_by_department_no_job_level_key():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx, forecast_months=8)

    assert all("job_level" not in entry for row in rows for entry in row.by_department)


def test_by_department_no_rate_key():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx, forecast_months=8)

    assert all("rate" not in entry for row in rows for entry in row.by_department)


def test_demand_forecast_pipeline_data_available_flag():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx, forecast_months=8)

    assert rows
    assert all(row.pipeline_data_available for row in rows if row.forecast_month in {"2026-05", "2026-06", "2026-07"})
    assert all(not row.pipeline_data_available for row in rows if row.forecast_month >= "2026-08")


def test_forecast_month_override_bounds():
    ctx = build_context()

    assert get_license_demand_forecast(ctx, forecast_months=3)

    import pytest

    with pytest.raises(ValueError):
        get_license_demand_forecast(ctx, forecast_months=2)
    with pytest.raises(ValueError):
        get_license_demand_forecast(ctx, forecast_months=25)


def test_demand_forecast_has_baseline_active():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx)

    assert rows
    assert any(row.baseline_active > 0 for row in rows)


def test_demand_forecast_projected_active_gte_baseline():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx)

    assert rows
    assert all(row.projected_active >= row.baseline_active for row in rows)


def test_demand_forecast_contracted_capacity_present():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx)

    assert rows
    assert all(row.contracted_capacity >= 0 for row in rows)


def test_demand_forecast_projected_over_capacity_non_negative():
    ctx = build_context()
    rows = get_license_demand_forecast(ctx)

    assert rows
    assert all(row.projected_over_capacity >= 0.0 for row in rows)
