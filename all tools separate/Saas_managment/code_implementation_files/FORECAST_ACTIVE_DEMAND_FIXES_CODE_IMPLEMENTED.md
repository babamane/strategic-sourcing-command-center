# Forecast Active Demand Fixes Code Implemented

**Project:** SaaS Spend Management Platform  
**Status:** Implemented and verified against the local SQLite-backed dataset  
**Audit date:** `2026-05-01`

## Summary

This change set replaces the old procurement-momentum view with an observed
active-demand history, extends the demand forecaster to produce a continuous
forward-looking active line, updates renewal pressure to read projected state at
the notice deadline, and adds a unified active-demand series endpoint for chart
consumers.

The frontend or dashboard no longer needs to stitch baseline history onto the
forecast by hand. The processing layer now exposes both the historical view and
the joined historical-plus-forecast series directly.

## Main Files Changed

- [processing/active_demand_processor.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/active_demand_processor.py)
- [processing/license_demand_forecaster.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/license_demand_forecaster.py)
- [processing/renewal_pressure_forecaster.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/renewal_pressure_forecaster.py)
- [schemas/proc_forecast_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_forecast_results.py)
- [schemas/proc_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_results.py)
- [api/routers/forecast.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/api/routers/forecast.py)
- [api/schemas/responses.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/api/schemas/responses.py)
- [processing_main.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing_main.py)
- [processing_smoke_test.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing_smoke_test.py)
- [tests/test_proc_demand_forecast.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_proc_demand_forecast.py)
- [tests/test_api_forecast.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_api_forecast.py)
- [tests/test_api_renewal.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_api_renewal.py)

Related compatibility updates to keep the full suite green:

- [forecasting_dashboard.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/forecasting_dashboard.py)
- [mcp_server/tools.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/mcp_server/tools.py)
- [tests/test_mcp_tools.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_mcp_tools.py)
- [api/pipeline_state.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/api/pipeline_state.py)
- [pipeline/checks.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/pipeline/checks.py)
- [processing/utilization_aggregator.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/utilization_aggregator.py)
- [tests/test_proc_renewal_pressure.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_proc_renewal_pressure.py)
- [.env](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/.env)

## Fix 1: Active Demand History

Removed the old procurement momentum processor and its result type.

Deleted:

- `get_procurement_momentum_forecast()`
- Holt smoothing helpers used only by momentum forecasting
- `ProcurementMomentumForecast`

Added:

- `ActiveDemandHistory`
- `get_active_demand_history(ctx, vendor=None)`

Implemented behavior:

- Builds a complete month range from the first `effective_license_date` through
  the audit month.
- Computes per-series historical monthly counts at
  `vendor + sku + seat_type + month`.
- Tracks:
  - `productive_active`
  - `vendor_billed`
  - `ghost_count`
  - `contracted_capacity`
  - `over_capacity`
- Uses `ctx.contract_history` to compute historical contracted capacity with
  max-seat selection across overlapping OFs for the same
  `vendor + sku + seat_type + month`.

## Fix 2: Demand Forecast Now Returns Projected Active State

`LicenseDemandForecast` now keeps the original incremental demand fields and
adds the absolute projected line fields that consumers were missing:

- `baseline_active`
- `projected_active`
- `contracted_capacity`
- `projected_over_capacity`
- `exit_licenses_applied`

Implemented behavior:

- Computes productive baseline license count per series at the audit date.
- Tracks cumulative expected new licenses over the forecast horizon.
- Produces `projected_active = baseline_active + cumulative_new` in V1.
- Computes `contracted_capacity` for each forecast month using shared pure
  contract-history logic.
- Produces `projected_over_capacity` as the positive difference between
  projected active demand and contracted capacity.

Shared pure helper added in the forecaster:

```python
_contracted_capacity_for_month(ctx, month, vendor, sku, seat_type) -> int
```

## Fix 3: Renewal Pressure Uses Projected Active at Deadline

`get_renewal_pressure()` no longer sums demand increments before the notice
deadline.

It now:

- finds the latest demand-forecast month at or before the notice deadline
- reads `projected_active` directly from that row
- uses that projected state as `hires_before_deadline`
- keeps the field name unchanged for API compatibility

`growth_score` now measures the increase from current provisioned load to the
projected active load at deadline.

## Fix 4: Unified Active Demand Series

Added:

- `ActiveDemandPoint`
- `get_active_demand_series(ctx, vendor=None)`
- `GET /forecast/active-demand-series`

Implemented behavior:

- Converts historical `ActiveDemandHistory` rows into `ActiveDemandPoint`
  records with `is_forecast=False`
- Converts forecast `LicenseDemandForecast` rows into `ActiveDemandPoint`
  records with `is_forecast=True`
- excludes the forecast row for the audit month
- returns a single sorted series spanning:
  - observed months from first activation through audit month
  - forecast months after the audit month through the configured horizon

This endpoint is the chart-ready continuous active-demand line. Consumers can
switch from solid to dashed rendering using `is_forecast` without performing
their own join logic.

## API Changes

Removed:

- old procurement momentum forecast route/response

Added:

- `GET /forecast/active-demand`
- `GET /forecast/active-demand-series`

Updated:

- `GET /forecast/demand` now includes the new forecast fields on every row

## Dashboard and MCP Alignment

Updated supporting consumers so the deleted momentum processor does not break
the repo:

- `forecasting_dashboard.py` now reads active-demand history instead of the old
  momentum forecast
- `mcp_server/tools.py` now exposes active-demand history instead of procurement
  momentum
- MCP tool tests were updated accordingly

## Processor Boundary Notes

The new composition layer lives in
[processing/active_demand_processor.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/active_demand_processor.py).

It intentionally composes:

- `get_active_demand_history()`
- `get_license_demand_forecast()`

This is the one allowed inter-processor composition for the joined series. No
new service or DB imports were added to forecasting processors.

Boundary check result:

```powershell
Get-ChildItem processing -Recurse -File | Select-String -Pattern "from services\\.|import services\\.|from db\\.|import db\\."
```

Result: no new service or DB imports were introduced outside the existing
context-building boundary.

## Verification

Processor and API gates:

```powershell
py -3 -m pytest tests/test_proc_demand_forecast.py -v
py -3 -m pytest tests/test_api_forecast.py -v
py -3 -m pytest tests/test_api_renewal.py -v
```

Repo-wide verification:

```powershell
py -3 -m pytest tests/ -q
py -3 processing_smoke_test.py
```

Final results:

- `204 passed`
- smoke test completed successfully

Smoke output:

- trueup: `27` rows
- breakdown: `20` rows
- ghost: `3` rows
- reclamation: `2321` rows
- utilization: `27` rows
- active_demand_history: `2403` rows
- active_demand_series: `3024` rows
- demand_forecast: `216` rows
- renewal_pressure: `27` rows

## Suite Stabilization Notes

To keep the full test suite green after the forecasting refactor:

- restored row-count/schema checks in `pipeline/checks.py`
- added a backward-compatible `_runs.clear()` hook in `api/pipeline_state.py`
  for older pipeline API tests
- normalized `.env` `ACTIVE_VENDORS` back to the repo baseline ordering
- made utilization summary rates use a non-underflowing denominator
- updated the renewal processor unit test fixture to the extended
  `LicenseDemandForecast` shape
