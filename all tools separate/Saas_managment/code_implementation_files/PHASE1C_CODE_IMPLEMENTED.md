# Phase 1C Code Implemented

**Project:** SaaS Spend Management Platform  
**Phase:** 1C - Processing Layer  
**Status:** Implemented and verified against the live SQLite-backed dataset  
**Prepared for:** Forecast / ML implementation handoff

## Current Runtime State

The code is intentionally version-agnostic. Callers should pass
`version=None` unless they need to pin a historical table version. The service
layer resolves the latest promoted table versions through `current_versions`.

Latest promoted versions observed during implementation:

- `vendor_overview_v1`
- `hr_headcount_v2`
- `license_utilization_v3`

Do not hardcode these names in forecast code. Use the existing service/context
path so renamed CSVs or newly promoted SQL tables keep working.

## Phase 1B Rename Applied

Schema files now use the service-layer `svc_` prefix:

- [schemas/svc_vendor_contract.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/svc_vendor_contract.py)
- [schemas/svc_employee.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/svc_employee.py)
- [schemas/svc_license_record.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/svc_license_record.py)

Service test files now use the `test_svc_` prefix:

- [tests/test_svc_ingestion.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_svc_ingestion.py)
- [tests/test_svc_contract.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_svc_contract.py)
- [tests/test_svc_license.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_svc_license.py)
- [tests/test_svc_employee.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_svc_employee.py)
- [tests/test_svc_integration.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_svc_integration.py)

## Processing Layer Files

New processing package:

- [processing/context_builder.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/context_builder.py)
- [processing/trueup_processor.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/trueup_processor.py)
- [processing/breakdown_enricher.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/breakdown_enricher.py)
- [processing/ghost_detector.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/ghost_detector.py)
- [processing/reclamation_detector.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/reclamation_detector.py)
- [processing/utilization_aggregator.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/utilization_aggregator.py)
- [processing/license_demand_forecaster.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/license_demand_forecaster.py)
- [processing/renewal_pressure_forecaster.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/renewal_pressure_forecaster.py)

Typed processing outputs:

- [schemas/proc_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_results.py)
- [schemas/proc_forecast_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_forecast_results.py)

Manual entry points:

- [processing_main.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing_main.py)
- [processing_smoke_test.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing_smoke_test.py)

Forecast storage stub:

- [services/forecast_store_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/forecast_store_service.py)

## Architecture Boundary

[processing/context_builder.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/processing/context_builder.py)
is the only file in `processing/` that imports from `services/`.

Processors receive a `ProcessingContext` and do not import from:

- `services`
- `db`
- SQLite directly

Boundary check used:

```powershell
rg "from services\.|import services\.|from db\.|import db\." processing
```

Expected output is only the service imports inside `processing/context_builder.py`.

## Public Processing APIs

Build context once, then pass it to processors:

```python
from processing.context_builder import build_context

ctx = build_context(vendor=None, version=None)
```

Implemented processor functions:

- `get_trueup_exposure(ctx, vendor=None)`
- `get_trueup_breakdown(ctx, vendor=None, sku=None, seat_type=None)`
- `get_ghost_summary(ctx, vendor=None)`
- `get_ghost_detail(ctx, vendor=None, department=None)`
- `get_reclamation_candidates(ctx, vendor=None, department=None, min_score=0.7)`
- `get_utilization_summary(ctx, vendor=None)`
- `get_license_demand_forecast(ctx, vendor=None, department=None, before_date=None)`
- `get_renewal_pressure(ctx, vendor=None)`

Compatibility note: `get_ghost_details(ctx, vendor=None)` exists as a plural
alias for `get_ghost_detail()`.

## Result Types

All public processor functions return dataclass instances from
[schemas/proc_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_results.py).

Implemented result types:

- `TrueUpResult`
- `TrueUpBreakdownResult`
- `GhostSummaryResult`
- `GhostDetailResult`
- `ReclamationResult`
- `UtilizationResult`
- `DemandForecastResult`
- `RenewalPressureResult`

Every result includes `computed_at`.

Forward-looking outputs include `exit_model_applied=False` where relevant.

## Live Data Observations

The current promoted database does not match some older README validation
targets. Tests were written against behavior and current live data invariants
rather than stale hardcoded counts.

Observed processing smoke output:

- true-up rows: `27`
- breakdown rows: `20`
- ghost summary rows: `3`
- reclamation candidates at `min_score=0.45`
- utilization rows: `27`
- demand forecast rows: `87`
- renewal pressure rows: `27`

Observed aggregate checks from the current DB:

- total licenses in active vendor context: `16,649`
- ghost total: `4,287`
- annual true-up exposure: `$216,270.96`
- annual shelfware: `$84,132.24`
- portfolio active usage rate: `0.5132`

If future docs mention different counts, verify the promoted SQL versions first
before changing processor logic.

## Verification

Final verification commands:

```powershell
py -3 -m pytest
py -3 processing_smoke_test.py
```

Final results:

- `118 passed`
- smoke test completed successfully

[pytest.ini](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/pytest.ini)
disables pytest's cache provider because this Windows workspace was producing
permission-denied temporary cache directories during bare repo-level test runs.

## Forecast Step Handoff

The forecast step should build on these existing landing zones.

Use this input path:

```python
from processing.context_builder import build_context

ctx = build_context(vendor=None, version=None)
```

Recommended forecast inputs already available on `ctx`:

- `ctx.licenses`
- `ctx.entitlement`
- `ctx.active_contracts`
- `ctx.active_employees`
- `ctx.exited_employees`
- `ctx.future_hires`
- `ctx.known_departments`
- `ctx.known_job_levels`
- `ctx.audit_date`
- `ctx.active_vendors`

Forecast output types should go in:

- [schemas/proc_forecast_results.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/proc_forecast_results.py)

Stored forecast read APIs should be implemented in:

- [services/forecast_store_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/forecast_store_service.py)

If the forecast step stores model results, keep the service boundary clean:

- model computation belongs outside `services/`
- SQLite readback of stored forecast rows belongs in `forecast_store_service`
- result dataclasses belong in `schemas/proc_forecast_results.py`
- raw service functions should not call processing or forecast code

Suggested next files for forecast implementation:

- `processing/ml_forecast_runner.py` or `forecasting/model_runner.py`
- `schemas/proc_forecast_results.py`
- `services/forecast_store_service.py`
- `tests/test_proc_forecast_results.py`
- `tests/test_forecast_store_service.py`

## Things Not Yet Implemented

- ML model training or inference
- `ml_forecasts` SQLite table DDL
- forecast persistence
- forecast expiration/readback rules
- chatbot tool schemas
- API endpoint wiring

Those remain for the forecast / Phase 1D step.

