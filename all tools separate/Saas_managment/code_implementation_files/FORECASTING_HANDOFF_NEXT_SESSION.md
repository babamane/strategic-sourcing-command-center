# Forecasting Handoff - Next Session

## Current State

Forecasting processors and dashboard are passing the current regression suite.

Verification from this session:

- `py -3 -m pytest` passed before the latest chart extension work with 140 tests.
- `py -3 processing_smoke_test.py` passed with unchanged core row counts:
  - `procurement_momentum: 27`
  - `demand_forecast: 216`
  - `renewal_pressure: 27`

Run both again at the start of the next session after pulling this state forward.

## Processor Review Notes

Focused review covered only the forecasting processors:

- `processing/license_demand_forecaster.py`
- `processing/renewal_pressure_forecaster.py`

No zero-drop issue was found inside the processors. The issue was in dashboard aggregation: monthly expected new licenses were being displayed as productive active demand.

Important behavior to preserve:

- Monthly hires are direct HR future-hire rows, not forecasted hires.
- `expected_new_licenses = known_hires * historical_provisioning_rate`.
- Productive active demand forecast should be baseline productive active seats plus cumulative expected new licenses.
- Department rows with hires can legitimately show `0` expected licenses when the historical provisioning rate for that vendor/SKU/seat type at that department/sub-team fallback grain is zero.

Known caveat:

- Current DB has `sub_team` populated for active/exited employees, but pre-hire rows have blank `sub_team`. Demand forecasting falls back to department-level rates for those pre-hire rows.
- `renewal_pressure_forecaster` still calls `get_license_demand_forecast(ctx, forecast_months=8)`. That is unchanged. If renewal scoring must look all the way to every contract notice deadline, expand that deliberately with tests.

## Dashboard Changes Made

File: `forecasting_dashboard.py`

The dashboard now separates:

- `monthly_hires`
- `monthly_expected_new_licenses`
- `cumulative_expected_new_licenses`
- `productive_active_demand_forecast`

The license decomposition chart now combines:

- historical license decomposition through audit month
- forecasted productive active demand after audit month
- contracted capacity through the relevant contract expiry window
- projected over-capacity seats and `projected_true_up`

Example verified for `Atlassify / Project Suite / Full`:

- baseline productive active: `209`
- contracted capacity: `155`
- projected true-up is already true from `2026-05`

## Follow-Up Areas

1. Decide whether projected true-up should compare against:
   - `effective_total_seats` from current capacity aggregation, or
   - another entitlement/contract metric if business semantics differ.

2. Decide whether forecast demand should remain flat after known pre-hire pipeline ends or whether a separate hiring forecast model should extend beyond known pre-hires.

3. Consider making dashboard test imports cleaner. Current tests import `forecasting_dashboard.py`, which runs Streamlit code in bare mode and emits warnings. Tests pass, but a later refactor could split pure helpers into a dashboard utility module.

4. If next phase includes visual QA, run the Streamlit dashboard and inspect:
   - All filters
   - Exact vendor/SKU/seat filters
   - Year filter
   - Forecast line continuation to contract expiry
   - Projected true-up month metric
