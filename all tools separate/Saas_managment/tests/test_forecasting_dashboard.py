from datetime import date

import forecasting_dashboard as dashboard
import pandas as pd


def _active_contract_rows(ctx, month: str, vendor: str | None = None) -> list[dict]:
    month_start = date.fromisoformat(f"{month}-01")
    return [
        row
        for row in ctx.contract_history
        if (vendor is None or row["vendor"] == vendor)
        and row["contract_start"] <= month_start < row["contract_expiry"]
    ]


def test_capacity_all_returns_nonzero():
    ctx = dashboard.ctx

    assert dashboard._capacity_for_month(ctx, "2026-05", "All", "All", "All") > 0


def test_capacity_vendor_level_sums_skus():
    ctx = dashboard.ctx
    month = "2026-05"
    vendor = "Atlassify"
    skus = sorted({row["sku"] for row in _active_contract_rows(ctx, month, vendor)})

    total = dashboard._capacity_for_month(ctx, month, vendor, "All", "All")
    per_sku_total = sum(dashboard._capacity_for_month(ctx, month, vendor, sku, "All") for sku in skus)

    assert total == per_sku_total


def test_capacity_exact_grain_matches_contract():
    ctx = dashboard.ctx
    month = "2026-05"
    vendor = "Atlassify"
    sku = "Project Suite"
    seat_type = "Full"
    expected = max(
        row["effective_total_seats"]
        for row in _active_contract_rows(ctx, month, vendor)
        if row["sku"] == sku and row["seat_type"] == seat_type
    )

    assert dashboard._capacity_for_month(ctx, month, vendor, sku, seat_type) == expected


def test_forecast_lines_use_productive_active_baseline_plus_cumulative_demand():
    momentum_df = pd.DataFrame()
    demand_df = pd.DataFrame(
        [
            {"forecast_month": "2026-05", "expected_new_licenses": 2.77, "pipeline_data_available": True},
            {"forecast_month": "2026-06", "expected_new_licenses": 2.06, "pipeline_data_available": True},
            {"forecast_month": "2026-07", "expected_new_licenses": 1.40, "pipeline_data_available": True},
            {"forecast_month": "2026-08", "expected_new_licenses": 0.0, "pipeline_data_available": False},
        ]
    )
    hire_counts_df = pd.DataFrame(
        [
            {"month": "2026-05", "monthly_hires": 80},
            {"month": "2026-06", "monthly_hires": 60},
            {"month": "2026-07", "monthly_hires": 40},
        ]
    )

    result = dashboard._aggregate_forecast_lines(
        momentum_df,
        demand_df,
        hire_counts_df,
        productive_active_baseline=209,
    )

    assert list(result["monthly_expected_new_licenses"]) == [2.77, 2.06, 1.40, 0.0]
    assert list(result["monthly_hires"]) == [80, 60, 40, 0]
    assert list(result["cumulative_expected_new_licenses"]) == [2.77, 4.83, 6.23, 6.23]
    assert list(result["productive_active_demand_forecast"]) == [211.77, 213.83, 215.23, 215.23]


def test_year_filter_limits_month_rows():
    df = pd.DataFrame([{"month": "2025-12", "value": 1}, {"month": "2026-01", "value": 2}])

    result = dashboard._filter_frame_year(df, "month", "2026")

    assert result.to_dict("records") == [{"month": "2026-01", "value": 2}]


def test_forecast_extends_to_contract_expiry_with_capacity_and_trueup_flag():
    ctx = dashboard.ctx
    forecast_df = pd.DataFrame(
        [
            {
                "month": "2026-05",
                "monthly_hires": 80,
                "monthly_expected_new_licenses": 2.77,
                "pipeline_data_available": True,
            }
        ]
    )

    result = dashboard._extend_forecast_to_month(
        forecast_df,
        ctx,
        "2026-07",
        "Atlassify",
        "Project Suite",
        "Full",
        productive_active_baseline=209,
    )

    assert list(result["month"]) == ["2026-05", "2026-06", "2026-07"]
    assert list(result["productive_active_demand_forecast"]) == [211.77, 211.77, 211.77]
    assert all(result["contracted_capacity"] > 0)
    assert list(result["projected_true_up"]) == [True, True, True]


def test_combined_license_lines_adds_forecast_after_history():
    historical_df = pd.DataFrame(
        [
            {
                "month": "2026-05",
                "productive_active": 209,
                "contracted_capacity": 155,
            }
        ]
    )
    forecast_df = pd.DataFrame(
        [
            {
                "month": "2026-06",
                "procurement_momentum_forecast": 214.5,
                "confidence_lower": 210.0,
                "confidence_upper": 219.0,
                "productive_active_demand_forecast": 211.77,
                "contracted_capacity": 155,
                "projected_over_capacity_seats": 56.77,
                "projected_true_up": True,
            }
        ]
    )

    result = dashboard._combined_license_lines(historical_df, forecast_df)

    assert list(result["month"]) == ["2026-05", "2026-06"]
    assert result.loc[result["month"] == "2026-06", "projected_true_up"].iloc[0] == True
    assert result.loc[result["month"] == "2026-06", "procurement_momentum_forecast"].iloc[0] == 214.5
