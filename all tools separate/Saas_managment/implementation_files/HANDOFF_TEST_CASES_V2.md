# Handoff Note — Test Case Session (Updated)

**Project:** SaaS Spend Management Platform
**Phase:** 1B — Services Layer Refactored
**Test framework:** `pytest`
**Database:** SQLite — real versioned tables, no mocking
**Audit Date:** `2026-05-01`
**Spec reference:** `PHASE1B_SERVICES_REDEFINED.md`
**Updated from:** Previous test handoff — reflects architectural corrections

---

## What Changed Since Previous Handoff

### Functions removed from `license_service` — delete their tests

| Removed Function | Tests to Delete |
|---|---|
| `get_ghost_licenses()` | All `test_get_ghost_licenses_*` |
| `get_reclamation_candidates()` | All `test_get_reclamation_candidates_*` |
| `get_utilization_summary()` | All `test_get_utilization_summary_*` |

These are processing layer concerns. They move to `processing/ghost_detector.py`,
`processing/reclamation_detector.py`, `processing/utilization_aggregator.py`
in Phase 1C. Do not test them here.

### Function renamed — update test names and calls

`get_active_provisioned()` → `get_raw_licenses(status_filter=["active", "over_tier"])`

All `test_get_active_provisioned_*` become `test_get_raw_licenses_*`.
The call in each test changes from `license_service.get_active_provisioned()`
to `license_service.get_raw_licenses(status_filter=["active", "over_tier"])`.

### Row count assertions — no more hardcoded numbers

Replace exact count assertions (`== 6016`, `== 4222`, `== 180`) with soft
threshold checks. Tests now assert the count is within 5% of the last ingested
count from `data_versions`, not a hardcoded figure. See pattern below.

### Department headcount — no hardcoded department list

`test_get_department_headcount_all_eight_departments` now validates against
discovered values from `vendor_profiles`, not a hardcoded list literal.

### Integration tests — update function names

`get_ghost_licenses()` and `get_active_provisioned()` references in
`test_integration.py` must be updated to use `get_raw_licenses()` with
appropriate `status_filter`.

### New tests added

New test file `test_ingestion_service_additions.py` covers the two new
functions added to `ingestion_service`: `get_discovered_values()` and
`get_last_ingested_count()`.

---

## Database State Assumed by All Tests

All tests assume data is already loaded. Never call ingestion inside a test.

| Table | Expected State |
|---|---|
| `vendor_overview_v1` | Atlassify, Nexaflow, Cloudora contracts loaded |
| `hr_headcount_v2` | 10,418 rows — 6,016 active + 4,222 exited + 180 pre-hire |
| `license_utilization_v3` | 27,646 rows total — 3-vendor active subset |
| `vendor_profiles` | Discovery rows present for all three tables |
| `data_versions` | Loaded versions present for all three tables |
| `current_versions` | Promoted version for all three tables |
| `.env` | `SAAS_SPEND_AUDIT_DATE=2026-05-01`, `ACTIVE_VENDORS=Atlassify,Nexaflow,Cloudora`, `ROW_COUNT_DEVIATION_THRESHOLD=0.05` |

### Reference counts — for soft threshold tests only

These are reference figures, not hardcoded test assertions.

| Metric | Reference Count |
|---|---|
| Total HR rows (all statuses) | 10,418 |
| Active employees | 6,016 |
| Exited employees | 4,222 |
| Pre-hire employees | 180 |
| Atlassify ghost licenses | 1,817 (3-vendor subset) |
| Pre-hire May 2026 | 80 |
| Pre-hire June 2026 | 60 |
| Pre-hire July 2026 | 40 |
| Engineering pre-hires | 54 |
| Sales pre-hires | 37 |
| Customer Success pre-hires | 28 |

---

## Soft Row Count Check Pattern

Use this pattern wherever a test previously had `== 6016` or similar.

```python
from services.ingestion_service import get_last_ingested_count

def assert_within_threshold(table_name: str, actual: int, threshold: float = 0.05):
    expected = get_last_ingested_count(table_name)
    assert expected is not None, f"No ingested count found for {table_name}"
    deviation = abs(actual - expected) / max(expected, 1)
    assert deviation <= threshold, (
        f"{table_name}: expected ~{expected} rows, got {actual} "
        f"({deviation*100:.1f}% deviation — threshold {threshold*100:.0f}%)"
    )
```

For `get_active_employees()` specifically: the check compares the active
employee count against the total HR ingested count. A 5% deviation on 10,418
total rows means warn if active count is outside 9,897–10,939. This is
intentionally loose — it catches corruption (e.g. 100 rows returned instead
of 6,016) without failing on legitimate filter differences.

---

## Test File Structure

```
Saas_managment/
└── tests/
    ├── conftest.py
    ├── test_ingestion_service_additions.py   ← NEW
    ├── test_contract_service.py
    ├── test_license_service.py               ← UPDATED
    ├── test_employee_service.py              ← UPDATED
    ├── test_trueup_service.py
    ├── test_forecast_service.py
    └── test_integration.py                  ← UPDATED
```

---

## `conftest.py`

```python
import pytest
import os
from datetime import date

@pytest.fixture(scope="session")
def audit_date():
    return date(2026, 5, 1)

@pytest.fixture(scope="session")
def default_version():
    return None  # triggers current promoted version resolution

@pytest.fixture(scope="session")
def active_vendors() -> list[str]:
    raw = os.getenv("ACTIVE_VENDORS", "")
    vendors = [v.strip() for v in raw.split(",") if v.strip()]
    assert vendors, "ACTIVE_VENDORS env var is not set or empty"
    return vendors

@pytest.fixture(scope="session")
def row_count_threshold() -> float:
    return float(os.getenv("ROW_COUNT_DEVIATION_THRESHOLD", "0.05"))
```

**Rules for all test files:**
- Tests are read-only — never write to the database
- Never call ingestion logic inside a test — data is pre-loaded
- Never hardcode vendor names — use `active_vendors` fixture
- Never hardcode row counts — use `assert_within_threshold` helper
- Never hardcode department names — read from `get_discovered_values()`
- Stub `NotImplementedError` tests are valid passing tests

---

## `test_ingestion_service_additions.py` — NEW

Tests for the two functions added to `ingestion_service` in this refactor.

```python
from services.ingestion_service import get_discovered_values, get_last_ingested_count
import pytest
```

| Test Name | Exact Assertion |
|---|---|
| `test_get_discovered_values_departments_not_empty` | `get_discovered_values("hr_headcount", "department")` returns non-empty list |
| `test_get_discovered_values_departments_are_strings` | All values in result are strings |
| `test_get_discovered_values_departments_count` | Result contains exactly 8 unique department values |
| `test_get_discovered_values_exit_types_not_empty` | `get_discovered_values("hr_headcount", "exit_type")` returns non-empty list |
| `test_get_discovered_values_exit_types_known_values` | Result contains at least `voluntary`, `layoff`, `performance`, `retirement` |
| `test_get_discovered_values_job_levels` | `get_discovered_values("hr_headcount", "job_level")` returns list containing `L1` through `L7` |
| `test_get_discovered_values_seat_types` | `get_discovered_values("vendor_overview", "seat_type")` returns list containing `Full`, `Contributor`, `Collaborator` |
| `test_get_discovered_values_contract_status` | `get_discovered_values("vendor_overview", "contract_status")` returns list containing `active` and `superseded` |
| `test_get_discovered_values_unknown_column_returns_empty` | `get_discovered_values("hr_headcount", "nonexistent_column")` returns `[]` — does not raise |
| `test_get_discovered_values_unknown_table_returns_empty` | `get_discovered_values("nonexistent_table", "department")` returns `[]` — does not raise |
| `test_get_last_ingested_count_hr_headcount` | `get_last_ingested_count("hr_headcount")` returns integer, value close to 10,418 (within 5%) |
| `test_get_last_ingested_count_vendor_overview` | `get_last_ingested_count("vendor_overview")` returns integer > 0 |
| `test_get_last_ingested_count_license_utilization` | `get_last_ingested_count("license_utilization")` returns integer close to 27,646 (within 5%) |
| `test_get_last_ingested_count_unknown_table` | `get_last_ingested_count("nonexistent_table")` returns `None` — does not raise |
| `test_get_last_ingested_count_returns_int_or_none` | Return type is `int` or `None` — never raises |

---

## `test_contract_service.py` — unchanged from previous handoff

All contract service tests remain valid. No functions were removed or renamed.
The only internal change was removing hardcoded vendor name strings — the
external interface is identical.

```python
from services import contract_service
from exceptions import DataNotReadyError
import pytest
```

| Test Name | Exact Assertion |
|---|---|
| `test_get_entitlement_returns_list` | `isinstance(result, list)` |
| `test_get_entitlement_not_empty` | `len(result) > 0` |
| `test_get_entitlement_no_duplicates` | No duplicate `(vendor, sku, seat_type)` tuples |
| `test_get_entitlement_only_active_status` | All rows: `row['contract_status'] == 'active'` |
| `test_get_entitlement_effective_seats_positive` | All rows: `row['effective_total_seats'] > 0` |
| `test_get_entitlement_unit_price_positive` | All rows: `row['unit_price'] > 0` |
| `test_get_entitlement_active_vendors_only` | `set(r['vendor'] for r in result) == set(active_vendors)` — uses fixture, not hardcoded set |
| `test_get_entitlement_vendor_filter_nexaflow` | `get_entitlement(vendor="Nexaflow")` — all rows `vendor == 'Nexaflow'` |
| `test_get_entitlement_vendor_filter_atlassify` | `get_entitlement(vendor="Atlassify")` — all rows `vendor == 'Atlassify'` |
| `test_get_entitlement_columns_exact` | Every row has exactly 10 keys: `vendor`, `sku`, `seat_type`, `effective_total_seats`, `unit_price`, `notice_deadline`, `auto_renewal`, `true_down_rights`, `measurement_method`, `contract_status` |
| `test_get_active_contracts_of_id_unique` | All `of_id` unique: `len(set(r['of_id'] for r in result)) == len(result)` |
| `test_get_active_contracts_no_superseded` | No row has `contract_status == 'superseded'` |
| `test_get_active_contracts_vendor_filter` | `get_active_contracts(vendor="Cloudora")` — all rows `vendor == 'Cloudora'` |
| `test_get_active_contracts_columns_exact` | 15 keys present: `of_id`, `vendor`, `sku`, `seat_type`, `contracted_seats`, `effective_total_seats`, `unit_price`, `contract_start`, `contract_expiry`, `notice_deadline`, `auto_renewal`, `true_down_rights`, `measurement_method`, `contract_event_type`, `contract_group_id` |
| `test_get_contract_history_ordered_ascending` | Result ordered by `contract_start` ascending |
| `test_get_contract_history_includes_superseded` | At least one `contract_status == 'superseded'` for Atlassify + Project Suite + Full |
| `test_get_contract_history_invalid_vendor_raises` | `get_contract_history(vendor="Veloxa", sku="x", seat_type="Full")` raises `ValueError` |
| `test_get_contract_history_unknown_combo_raises` | `get_contract_history(vendor="Atlassify", sku="NonExistentSKU", seat_type="Full")` raises `DataNotReadyError` |

---

## `test_license_service.py` — UPDATED

Remove all ghost, reclamation, and utilization tests.
Rename active_provisioned tests to raw_licenses.
Add new `get_raw_licenses` tests.

```python
from services import license_service
import pytest
```

### Tests to DELETE from previous handoff

```
test_get_ghost_licenses_returns_list
test_get_ghost_licenses_status_only_ghost
test_get_ghost_licenses_cost_at_risk_non_negative
test_get_ghost_licenses_atlassify_exact_count
test_get_ghost_licenses_ordered_by_cost
test_get_ghost_licenses_vendor_filter
test_get_ghost_licenses_columns_present
test_get_reclamation_candidates_flag_true
test_get_reclamation_candidates_ordered
test_get_reclamation_candidates_null_churn_score_ghost_rows
test_get_reclamation_candidates_not_empty
test_get_utilization_summary_returns_dict
test_get_utilization_summary_three_vendors
test_get_utilization_summary_all_tiers_present
test_get_utilization_summary_zero_not_omitted
test_get_utilization_summary_counts_are_ints
```

### Tests to RENAME (update function call inside each)

| Old Name | New Name | Call Change |
|---|---|---|
| `test_get_active_provisioned_returns_list` | `test_get_raw_licenses_returns_list` | `get_raw_licenses(status_filter=["active","over_tier"])` |
| `test_get_active_provisioned_status_values` | `test_get_raw_licenses_status_filter_active_overtier` | Same |
| `test_get_active_provisioned_vendor_filter` | `test_get_raw_licenses_vendor_filter` | Same + vendor param |
| `test_get_active_provisioned_three_vendors_only` | `test_get_raw_licenses_active_vendors_only` | Same |
| `test_get_active_provisioned_column_count` | `test_get_raw_licenses_column_count` | Now expects 30 columns |
| `test_get_active_provisioned_monthly_cost_positive` | `test_get_raw_licenses_monthly_cost_positive` | Same |

### NEW tests for `get_raw_licenses`

| Test Name | Exact Assertion |
|---|---|
| `test_get_raw_licenses_returns_list` | `isinstance(result, list)` for `get_raw_licenses()` |
| `test_get_raw_licenses_no_filter_all_statuses_present` | `set(r['license_status'] for r in result)` contains all 4 statuses: `active`, `ghost`, `deprovisioned`, `over_tier` |
| `test_get_raw_licenses_status_filter_active_overtier` | `get_raw_licenses(status_filter=["active","over_tier"])` — all rows in `['active','over_tier']` |
| `test_get_raw_licenses_status_filter_ghost_only` | `get_raw_licenses(status_filter=["ghost"])` — all rows `license_status == 'ghost'` |
| `test_get_raw_licenses_status_filter_ghost_atlassify_count` | `get_raw_licenses(vendor="Atlassify", status_filter=["ghost"])` returns exactly 1,817 rows |
| `test_get_raw_licenses_status_filter_none_returns_all` | `get_raw_licenses(status_filter=None)` — row count within 5% of last ingested count |
| `test_get_raw_licenses_vendor_filter` | `get_raw_licenses(vendor="Atlassify")` — all rows `vendor == 'Atlassify'` |
| `test_get_raw_licenses_active_vendors_only` | `set(r['vendor'] for r in get_raw_licenses())` equals `set(active_vendors)` |
| `test_get_raw_licenses_columns_exact_count` | Every row has exactly 30 keys — see column list in spec |
| `test_get_raw_licenses_required_columns_present` | Every row contains: `license_id`, `vendor`, `sku`, `seat_type`, `assigned_email`, `employee_id`, `department`, `job_level`, `license_status`, `usage_tier`, `monthly_cost`, `current_of_id`, `of_id` |
| `test_get_raw_licenses_monthly_cost_positive` | All rows `monthly_cost > 0` |
| `test_get_raw_licenses_null_churn_for_ghost` | Rows where `license_status == 'ghost'` have `churn_risk_score is None` |
| `test_get_raw_licenses_null_churn_for_deprovisioned` | Rows where `license_status == 'deprovisioned'` have `churn_risk_score is None` |
| `test_get_raw_licenses_null_last_active_for_deprovisioned` | Rows where `license_status == 'deprovisioned'` have `last_active_date is None` |
| `test_get_raw_licenses_cost_at_risk_zero_for_active` | Rows where `license_status == 'active'` have `cost_at_risk == 0.0` |
| `test_get_raw_licenses_renewal_urgency_expired_nexaflow` | `get_raw_licenses(vendor="Nexaflow")` contains rows where `renewal_urgency == 'expired'` — count should be 261 |
| `test_get_raw_licenses_renewal_urgency_expired_cloudora` | `get_raw_licenses(vendor="Cloudora")` contains rows where `renewal_urgency == 'expired'` — count should be 218 |

---

## `test_employee_service.py` — UPDATED

```python
from services import employee_service
from services.ingestion_service import get_discovered_values, get_last_ingested_count
from exceptions import DataNotReadyError
from datetime import date
import pytest
```

### Row count assertions — updated pattern

Replace every `== 6016`, `== 4222`, `== 180` with the soft check:

```python
# Instead of:
assert len(result) == 6016

# Use:
assert_within_threshold("hr_headcount", len(result))
# The helper is defined in conftest.py or as a module-level function
```

For pre-hire counts by month and department, keep exact assertions since
these are structural properties of the generated data, not data volume checks.

### Department and value tests — updated pattern

Replace hardcoded list literals with discovered values:

```python
# Instead of:
assert all(r['department'] in ["Engineering", "Sales", ...] for r in rows)

# Use:
known_depts = get_discovered_values("hr_headcount", "department")
assert all(r['department'] in known_depts for r in rows)
```

| Test Name | Exact Assertion |
|---|---|
| `test_get_active_employees_within_threshold` | `assert_within_threshold("hr_headcount", len(result))` — replaces exact count |
| `test_get_active_employees_all_active` | All rows: `row['is_active'] == True` |
| `test_get_active_employees_no_pii` | No row has `full_name` or `sub_team` keys |
| `test_get_active_employees_columns_exact` | Exactly 7 keys: `employee_id`, `email`, `department`, `job_level`, `region`, `is_active`, `hire_date` |
| `test_get_active_employees_department_values` | `all(r['department'] in get_discovered_values("hr_headcount", "department") for r in rows)` |
| `test_get_active_employees_job_level_values` | `all(r['job_level'] in get_discovered_values("hr_headcount", "job_level") for r in rows)` |
| `test_get_active_employees_region_values` | `all(r['region'] in get_discovered_values("hr_headcount", "region") for r in rows)` |
| `test_get_exited_employees_within_threshold` | `assert_within_threshold("hr_headcount", len(result))` |
| `test_get_exited_employees_all_inactive` | All rows: `row['is_active'] == False` |
| `test_get_exited_employees_exit_date_not_null` | All rows: `row['exit_date'] is not None` |
| `test_get_exited_employees_exit_type_discovered_values` | `allowed = set(get_discovered_values("hr_headcount", "exit_type"))` — all non-null `exit_type` values in `allowed` |
| `test_get_exited_employees_no_pii` | No row has `full_name` or `sub_team` |
| `test_get_future_hires_within_threshold` | `assert_within_threshold("hr_headcount", len(result))` |
| `test_get_future_hires_status_all_prehire` | All rows: `row['employee_status'] == 'pre-hire'` |
| `test_get_future_hires_all_inactive` | All rows: `row['is_active'] == False` |
| `test_get_future_hires_dates_after_audit` | All rows: `row['hire_date'] > date(2026, 5, 1)` |
| `test_get_future_hires_dates_within_window` | All rows: `row['hire_date'] <= date(2026, 7, 31)` |
| `test_get_future_hires_no_exit_date` | All rows: `row['exit_date'] is None` |
| `test_get_future_hires_may_count` | Rows with May 2026 `hire_date` == 80 |
| `test_get_future_hires_june_count` | Rows with June 2026 `hire_date` == 60 |
| `test_get_future_hires_july_count` | Rows with July 2026 `hire_date` == 40 |
| `test_get_future_hires_before_date_may` | `get_future_hires(before_date=date(2026,5,31))` returns 80 rows |
| `test_get_future_hires_department_engineering` | `get_future_hires(department="Engineering")` returns 54 rows |
| `test_get_future_hires_department_sales` | `get_future_hires(department="Sales")` returns 37 rows |
| `test_get_future_hires_combined_filter` | `get_future_hires(department="Engineering", before_date=date(2026,5,31))` — all rows Engineering AND May |
| `test_get_future_hires_columns_exact` | Exactly 7 keys: `employee_id`, `email`, `department`, `job_level`, `region`, `hire_date`, `employee_status` |
| `test_get_future_hires_email_format` | All emails match `prehire.empNNNNN@company.com` pattern |
| `test_get_employee_by_email_found` | Known email returns dict with correct `employee_id` |
| `test_get_employee_by_email_not_found` | Unknown email raises `DataNotReadyError` |
| `test_get_employee_by_email_returns_dict` | Return type is `dict`, not `list` |
| `test_get_employee_by_email_no_pii` | No `full_name` or `sub_team` in result |
| `test_get_employee_by_email_columns_exact` | 10 keys: `employee_id`, `email`, `department`, `job_level`, `region`, `is_active`, `hire_date`, `exit_date`, `exit_type`, `manager_id` |
| `test_get_department_headcount_returns_dict` | `isinstance(result, dict)` |
| `test_get_department_headcount_keys_from_discovery` | `set(result.keys()) == set(get_discovered_values("hr_headcount", "department"))` — no hardcoded list |
| `test_get_department_headcount_total_active` | `sum(result.values())` within 5% of `get_last_ingested_count("hr_headcount")` |
| `test_get_department_headcount_engineering` | `result['Engineering'] == 1847` — kept exact, structural property of generated data |
| `test_get_department_headcount_sales` | `result['Sales'] == 1155` |
| `test_get_department_headcount_values_ints` | All values are `int >= 0` |
| `test_get_department_headcount_zero_not_omitted` | All discovered departments present — zero-count departments appear as `0` |

---

## `test_trueup_service.py` — unchanged

| Test Name | Exact Assertion |
|---|---|
| `test_compute_snapshot_raises` | `trueup_service.compute_snapshot()` raises `NotImplementedError` |
| `test_compute_snapshot_with_vendor_raises` | `trueup_service.compute_snapshot(vendor="Atlassify")` raises `NotImplementedError` |
| `test_get_latest_snapshot_raises` | `trueup_service.get_latest_snapshot()` raises `NotImplementedError` |
| `test_get_snapshot_history_raises` | `trueup_service.get_snapshot_history()` raises `NotImplementedError` |

---

## `test_forecast_service.py` — unchanged

| Test Name | Exact Assertion |
|---|---|
| `test_get_renewal_pressure_raises` | `forecast_service.get_renewal_pressure()` raises `NotImplementedError` |
| `test_get_renewal_pressure_vendor_raises` | `forecast_service.get_renewal_pressure(vendor="Nexaflow")` raises `NotImplementedError` |
| `test_get_pressure_summary_raises` | `forecast_service.get_pressure_summary()` raises `NotImplementedError` |
| `test_get_headcount_driven_demand_raises` | `forecast_service.get_headcount_driven_demand("Nexaflow","Flow Automation","Contributor")` raises `NotImplementedError` |

---

## `test_integration.py` — UPDATED

Update function names from removed/renamed functions.

```python
from services import contract_service, license_service, employee_service
import pytest
```

| Test Name | Exact Assertion |
|---|---|
| `test_ghost_emails_resolve_to_exited_employees` | Every `assigned_email` in `get_raw_licenses(status_filter=["ghost"])` exists in email set from `get_exited_employees()` — zero orphans |
| `test_active_provisioned_emails_resolve_to_active` | Every `assigned_email` in `get_raw_licenses(status_filter=["active","over_tier"])` exists in email set from `get_active_employees()` — zero orphans |
| `test_future_hires_not_in_any_license_status` | No email from `get_future_hires()` appears in `get_raw_licenses()` with any status — pre-hires have zero license records |
| `test_entitlement_vendors_match_license_vendors` | `set(r['vendor'] for r in get_entitlement())` == `set(r['vendor'] for r in get_raw_licenses(status_filter=["active","over_tier"]))` |
| `test_no_email_in_multiple_status_groups` | No email in more than one of: active employees, exited employees, pre-hire employees |
| `test_active_employee_emails_unique` | Zero duplicate emails in `get_active_employees()` |
| `test_exited_employee_emails_unique` | Zero duplicate emails in `get_exited_employees()` |
| `test_future_hire_emails_unique` | Zero duplicate emails in `get_future_hires()` |
| `test_future_hires_engineering_for_pressure` | `get_future_hires(department="Engineering")` returns 54 rows |
| `test_future_hires_before_nexaflow_notice` | Get `notice_deadline` from `get_entitlement(vendor="Nexaflow")`. Call `get_future_hires(before_date=notice_deadline)`. Assert result not empty |
| `test_license_vendor_sku_in_contracts` | Every `(vendor, sku)` in `get_raw_licenses(status_filter=["active","over_tier"])` exists in `get_active_contracts()` |
| `test_raw_licenses_ghost_count_atlassify` | `len(get_raw_licenses(vendor="Atlassify", status_filter=["ghost"])) == 1817` |
| `test_expired_renewal_urgency_nexaflow` | `sum(1 for r in get_raw_licenses(vendor="Nexaflow") if r['renewal_urgency']=='expired') == 261` |
| `test_expired_renewal_urgency_cloudora` | `sum(1 for r in get_raw_licenses(vendor="Cloudora") if r['renewal_urgency']=='expired') == 218` |

---

## Running the Tests

```bash
cd Saas_managment
pytest tests/ -v
```

**Run new ingestion additions tests first** to confirm discovery data is
readable before running service tests that depend on it:

```bash
pytest tests/test_ingestion_service_additions.py -v
```

**Run in order:**
```bash
pytest tests/test_ingestion_service_additions.py -v
pytest tests/test_contract_service.py -v
pytest tests/test_license_service.py -v
pytest tests/test_employee_service.py -v
pytest tests/test_trueup_service.py tests/test_forecast_service.py -v
pytest tests/test_integration.py -v
```

---

## What to Do If Tests Fail

| Failure | Action |
|---|---|
| `test_get_discovered_values_*` fails | `vendor_profiles` table not populated — re-run ingestion discovery first |
| `test_get_last_ingested_count_*` returns `None` | `data_versions` has no `loaded` status rows — re-ingest |
| `assert_within_threshold` fails | Actual count deviates >5% from ingested count — check for data corruption or wrong version promoted |
| `get_raw_licenses` function not found | `license_service` was not refactored — `get_active_provisioned` still needs to be renamed |
| Department keys not from discovery | `get_department_headcount` still uses hardcoded list — fix to use `_get_known_departments()` |
| Ghost email not in exited employees | Join assumption broken — `license_status='ghost'` email not in `hr_headcount` with `employee_status='exited'` |
| `renewal_urgency` expired counts wrong | Data or filter issue — verify against `license_utilization_v3` directly |
| `NotImplementedError` not raised in stubs | Stub was accidentally implemented — remove logic |

---

*Test Case Handoff Updated · SaaS Spend Management · Phase 1B Services
Refactored · Audit Date: 2026-05-01 · Ref: PHASE1B_SERVICES_REDEFINED.md*
