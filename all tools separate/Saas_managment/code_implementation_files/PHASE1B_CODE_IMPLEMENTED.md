# Phase 1B Code Implemented

**Project:** SaaS Spend Management Platform  
**Phase:** 1B - Services Layer  
**Status:** Implemented and verified with live SQLite-backed tests

## What Was Built

Phase 1B introduced the service layer on top of the Phase 1A ingestion layer.
The implementation is intentionally split so each module can be triggered and
tested independently.

### Entry points

- [ingestion_main.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/ingestion_main.py)
- [services_main.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services_main.py)

### New schema package

- [schemas/__init__.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/__init__.py)
- [schemas/vendor_contract.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/vendor_contract.py)
- [schemas/employee.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/employee.py)
- [schemas/license_record.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/schemas/license_record.py)

### Service modules

- [services/__init__.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/__init__.py)
- [services/contract_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/contract_service.py)
- [services/license_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/license_service.py)
- [services/employee_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/employee_service.py)
- [services/trueup_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/trueup_service.py)
- [services/forecast_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/forecast_service.py)

### Config and environment updates

- [config/vendor_rules.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/config/vendor_rules.py)
- [.env](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/.env)

## Service Behavior

### `contract_service`

Implemented functions:

- `get_entitlement(vendor=None, version=None) -> list[dict]`
- `get_active_contracts(vendor=None, version=None) -> list[dict]`
- `get_contract_history(vendor, sku, seat_type, version=None) -> list[dict]`

Behavior highlights:

- Filters to `ACTIVE_VENDORS` by default.
- Supports optional vendor filtering.
- Resolves the promoted version when `version is None`.
- Returns plain dictionaries only.
- Deduplicates entitlement rows to the `vendor + sku + seat_type` grain.
- Keeps `get_active_contracts()` unique by `of_id`.
- Raises `DataNotReadyError` when the requested history is missing.

### `license_service`

Implemented functions:

- `get_active_provisioned(vendor=None, version=None) -> list[dict]`
- `get_ghost_licenses(vendor=None, version=None) -> list[dict]`
- `get_reclamation_candidates(vendor=None, version=None) -> list[dict]`
- `get_utilization_summary(vendor=None, version=None) -> dict`

Behavior highlights:

- Filters to the three active vendors by default.
- Returns billable licenses only for `active` and `over_tier`.
- Returns ghost licenses ordered by `cost_at_risk` descending.
- Returns reclamation candidates ordered by `cost_at_risk`, then `monthly_cost`.
- Returns nested utilization counts with all five usage tiers present.

### `employee_service`

Implemented functions:

- `get_active_employees(version=None) -> list[dict]`
- `get_exited_employees(version=None) -> list[dict]`
- `get_future_hires(department=None, before_date=None, version=None) -> list[dict]`
- `get_employee_by_email(email, version=None) -> dict`
- `get_department_headcount(version=None) -> dict`

Behavior highlights:

- No vendor filtering is applied here.
- Bulk employee functions exclude `full_name` and `sub_team`.
- `get_exited_employees()` uses `employee_status = 'exited'` to avoid the pre-hire rows that also have `is_active = 0`.
- `get_future_hires()` returns the pre-hire population and supports department and date-window filters.
- `get_department_headcount()` always returns all eight known departments, including zero counts.

### Stubs for later phases

- [services/trueup_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/trueup_service.py)
- [services/forecast_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/forecast_service.py)

These are intentionally stubbed and raise `NotImplementedError` so Phase 1C can
build the processing layer without ambiguous behavior.

## Data and Runtime Notes

- `ACTIVE_VENDORS` is set to `["Atlassify", "Nexaflow", "Cloudora"]`.
- `SAAS_SPEND_AUDIT_DATE=2026-05-01` is present in `.env`.
- The live database currently resolves to:
  - `vendor_overview_v1`
  - `hr_headcount_v2`
  - `license_utilization_v3`

## Verification

The Phase 1B service layer was verified with live database tests.

Final test result:

- `87 passed`
- `1 warning`

The warning was a local pytest cache directory permission quirk in the Windows workspace, not a service failure.

## Handoff Notes for Phase 1C

Phase 1C should treat the service layer as the stable interface.

Recommended dependencies from this phase:

- `contract_service` for entitlement and contract lineage data
- `license_service` for billable licenses, ghosts, reclamation, and utilization summaries
- `employee_service` for active, exited, future-hire, and department headcount lookups

Phase 1C can now focus on processing/true-up logic without reworking the data access layer.

## Phase 1B Redefinition Update

The service layer has been updated to match `PHASE1B_SERVICES_REDEFINED.md`.

### Refactored files

- [services/ingestion_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/ingestion_service.py)
- [services/license_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/license_service.py)
- [services/employee_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/employee_service.py)
- [services/contract_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services/contract_service.py)
- [services_main.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services_main.py)
- [services_smoke_test.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/services_smoke_test.py)
- [tests/conftest.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/conftest.py)
- [tests/test_ingestion_service_additions.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_ingestion_service_additions.py)
- [tests/test_contract_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_contract_service.py)
- [tests/test_license_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_license_service.py)
- [tests/test_employee_service.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_employee_service.py)
- [tests/test_integration.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_integration.py)

### Summary of changes applied

- Added `get_discovered_values()` and `get_last_ingested_count()` to the ingestion helper layer.
- Replaced the old license service surface with `get_raw_licenses()` and removed the derived ghost, reclamation, and utilization functions.
- Switched contract and license services to read `ACTIVE_VENDORS` from `.env` at module load.
- Replaced hardcoded employee department and exit-type constants with discovery-backed lookups.
- Added soft row-count warning helpers that read the latest ingested count from `data_versions`.
- Updated the manual runner, smoke test, and test suite to call the redefined services.

### Runtime config updated

- [`.env`](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/.env) now includes `ACTIVE_VENDORS=Atlassify,Nexaflow,Cloudora` and `ROW_COUNT_DEVIATION_THRESHOLD=0.05`.
- `ACTIVE_VENDORS` is now read from `.env` at module load instead of `config/vendor_rules.py`.

### Behavioral boundary now enforced

- Service layer returns raw rows only.
- Ghost, reclamation, and utilization derivations remain deferred to the Phase 1C processing layer.
- Discovery-backed categorical values now come from `vendor_profiles`.

### Latest verification

- `101 passed`
- `1 warning`

The warning is the same Windows pytest cache permission quirk observed during the earlier phase1b verification.
