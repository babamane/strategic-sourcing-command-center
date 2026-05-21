# Forecasting Code Implemented

**Project:** SaaS Spend Management Platform  
**Spec:** `FORECASTING_SPEC_V1.md`  
**Status:** Implemented and verified against the live SQLite-backed dataset  
**Audit date:** `2026-05-01`

## What Was Implemented

Forecasting V1 is implemented in the existing processing layer without making
processors depend on each other. The forecast processor consumes only
`ProcessingContext`, just like the rest of Phase 1C.

Main implementation files:

- [processing/license_demand_forecaster.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/license_demand_forecaster.py)
- [schemas/proc_forecast_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_forecast_results.py)
- [processing/context_builder.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/context_builder.py)
- [services/contract_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/contract_service.py)
- [services/license_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/license_service.py)
- [processing_main.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing_main.py)
- [processing_smoke_test.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing_smoke_test.py)
- [tests/test_proc_demand_forecast.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_proc_demand_forecast.py)

## Forecast A: Procurement Momentum

Public function:

```python
get_procurement_momentum_forecast(ctx, vendor=None, forecast_months=8)
```

Implemented behavior:

- Uses Holt's Linear Smoothing.
- Operates at `vendor + sku + seat_type` grain.
- Uses `effective_license_date` from all license statuses.
- Enforces `MIN_HISTORY_MONTHS = 12`.
- Supports `forecast_months` override from `3` to `24`.
- Returns `ForecastUnavailableResult` instead of raising for missing history.
- Uses `model_version="holt_v1"`.
- Returns confidence lower/upper bands.

Current live output:

- `27` procurement momentum forecast series.
- `Prismly` returns `ForecastUnavailableResult(reason="insufficient_activation_history")`.

## Forecast B: Hire-Driven License Demand

Public function:

```python
get_license_demand_forecast(ctx, vendor=None, department=None, forecast_months=8, before_date=None)
```

Implemented behavior:

- Returns one row per `vendor + sku + seat_type + forecast_month`.
- Default horizon is May-Dec 2026 from the audit date.
- Computes provisioning rates from active employees and active/over-tier licenses.
- Applies rates to confirmed future hires.
- Returns zero demand for Aug-Dec 2026 because the current pre-hire pipeline only covers May-Jul 2026.
- Sets `pipeline_data_available=True` for months where the hire pipeline has
  at least one hire, and `False` for months beyond known pipeline data.
- Supports fallback metadata through `rate_grain_applied`:
  - `dept_level`
  - `dept_only`
  - `portfolio`
- Keeps `exit_model_applied=False` per V1 scope.

Current live output:

- `216` demand forecast rows: `27` active series x `8` months.

## Forecast Result Types

Added to [schemas/proc_forecast_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_forecast_results.py):

- `ProcurementMomentumForecast`
- `LicenseDemandForecast`
- `ForecastUnavailableResult`

## Context and Service Additions

`ProcessingContext` now includes:

```python
contract_history: list[dict]
```

This is populated in [processing/context_builder.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/context_builder.py)
by calling `contract_service.get_contract_history(vendor=vendor, version=version)`.
The function returns all order forms regardless of `contract_status`, including
superseded rows, so forecast consumers can build a contracted-capacity stepwise
line from historical OFs.

`license_service.get_raw_licenses()` now supports:

```python
include_effective_license_date: bool = False
```

Default behavior remains unchanged for service-layer callers and tests. The
context builder opts in with `include_effective_license_date=True` so
forecasting can build activation series without changing the normal service
contract.

## Processor Independence

No processor calls another processor.

`renewal_pressure_forecaster.py` was not changed to call
`get_procurement_momentum_forecast()`, even though the spec mentioned that
integration option. This preserves the Phase 1C guideline that processors are
independent computations over the same `ProcessingContext`.

Boundary check:

```powershell
rg "from services\.|import services\.|from db\.|import db\." processing
```

Expected result remains only service imports inside:

- [processing/context_builder.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/context_builder.py)

## Verification

Final commands:

```powershell
py -3 -m pytest
py -3 processing_smoke_test.py
```

Final results:

- `127 passed`
- smoke test completed successfully

Smoke output:

- trueup: `27` rows
- breakdown: `20` rows
- ghost: `3` rows
- reclamation: `4,366` rows
- utilization: `27` rows
- procurement momentum: `27` rows
- demand forecast: `216` rows
- renewal pressure: `27` rows

## Notes for Next Handoff

Forecasting V1 is on-demand only. No `ml_forecasts` table was created, matching
the V1 storage decision.

Deferred items:

- forecast persistence
- `ml_forecasts` DDL
- API/chatbot schemas
- exit model
- deprovision decay model
- seasonal model
- Prismly/Databridge/Veloxa momentum forecasts until LU data exists
