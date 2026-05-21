# SaaS Spend Management — Phase 1B: Services Layer Redefined

**Phase:** 1B — Services Layer Refactor
**Depends on:** Phase 1A complete — versioned SQLite tables live,
`db/connection.py` working, `vendor_profiles` populated from discovery run,
`data_versions` populated, `current_versions` promoted
**Audit Date:** `2026-05-01` — read from `.env` as `SAAS_SPEND_AUDIT_DATE`
**Active Vendors:** Read from `.env` as `ACTIVE_VENDORS` — currently
`Atlassify,Nexaflow,Cloudora` — never hardcoded in service files
**Source of truth:** `SAAS_BASE_LAYER_README_V5.md`

---

## Why This Document Exists

Phase 1B was implemented with three architectural violations that must be
corrected before Phase 1C builds the processing layer on top:

**Violation 1 — Ghost and reclamation logic in the service layer.**
`get_ghost_licenses()` and `get_reclamation_candidates()` are derived signals,
not raw data. In real vendor exports, `license_status = 'ghost'` does not exist.
Ghost detection is the result of joining vendor license data against HR exit
records. That join is processing layer work. The service layer exposes raw rows.

**Violation 2 — Aggregation in the service layer.**
`get_utilization_summary()` computes grouped counts from raw rows. Aggregation
is processing layer work. The service layer returns raw rows with the
`usage_tier` column. The processing layer aggregates.

**Violation 3 — Constants hardcoded in service files.**
`KNOWN_DEPARTMENTS`, `ALLOWED_EXIT_TYPES`, `ACTIVE_VENDORS` hardcoded in
service files are wrong. These values must be read from runtime sources:
- Vendor list → `.env` file, read once at module load
- Schema-derived values (departments, exit types, job levels, seat types)
  → `vendor_profiles` SQLite table, read via `ingestion_service` function
- Row count expectations → `data_versions` SQLite table, read via
  `ingestion_service` function

**Hardcoded row count assertions like `len(rows) != 6016` are wrong.**
6,016 is the current count. It changes when new data is ingested. Replace with
a softer threshold check against the last known ingested count from
`data_versions`. This detects data loss or corruption without breaking on
legitimate data updates.

---

## The Correct Architectural Boundary

```
RAW DATA SOURCES               SERVICE LAYER              PROCESSING LAYER
(SQLite versioned tables)      (data access only)         (signal derivation)

vendor_overview_v{N}  ──────→  contract_service     ──→  trueup_processor
                                 · get_entitlement()       ghost_detector
hr_headcount_v{N}     ──────→  employee_service     ──→  reclamation_detector
                                 · get_raw_employees()     utilization_aggregator
license_utilization_v{N} ───→  license_service      ──→  shelfware_detector
                                 · get_raw_licenses()      pressure_forecaster
```

**Service layer rule:** Read raw versioned data. Apply only filters and column
projection. Never join across tables. Never aggregate. Never classify or label.

**Processing layer rule:** Call service functions. Join results. Derive signals.
Return computed output. Never touch `db/` directly.

---

## What Changes in This Refactor

### `services/license_service.py`

| Current Function | Action | Reason |
|---|---|---|
| `get_active_provisioned()` | Keep — rename to `get_raw_licenses(status_filter, vendor, version)` | Correct — raw filtered data access |
| `get_ghost_licenses()` | Remove | Ghost detection is processing layer work |
| `get_reclamation_candidates()` | Remove | Reclamation logic is processing layer work |
| `get_utilization_summary()` | Remove | Aggregation is processing layer work |

Replaced by one general function `get_raw_licenses()` that accepts an optional
`status_filter` list. Processing layer passes whatever statuses it needs.

### `services/employee_service.py`

| Current Pattern | Action |
|---|---|
| `KNOWN_DEPARTMENTS = [...]` hardcoded | Remove — read from `vendor_profiles` via `ingestion_service.get_discovered_values()` |
| `ALLOWED_EXIT_TYPES = {...}` hardcoded | Remove — read from `vendor_profiles` via `ingestion_service.get_discovered_values()` |
| `len(rows) != 6016` hard assertion | Replace with soft threshold check against `data_versions` last ingested count |

### `services/contract_service.py`

| Current Pattern | Action |
|---|---|
| Vendor list from `ACTIVE_VENDORS` in `config/vendor_rules.py` | Move to `.env` as `ACTIVE_VENDORS=Atlassify,Nexaflow,Cloudora` — read via `os.getenv` |
| Any hardcoded seat types or contract status values | Remove — read from `vendor_profiles` via `ingestion_service.get_discovered_values()` |

### `services/ingestion_service.py`

Add two new functions that the service layer calls to read discovery output.
Do not add SQL to service files — these functions are the gateway.

---

## New Functions Required in `ingestion_service.py`

These are added to the existing Phase 1A file. No other changes to that file.

### `get_discovered_values(table_name: str, column_name: str) -> list`

Reads observed categorical values for a column from the `vendor_profiles` table.
Returns a list. Returns an empty list if no discovery has run yet — callers
must handle the empty case gracefully (log a warning, do not raise).

```python
def get_discovered_values(table_name: str, column_name: str) -> list:
    """
    Returns discovered categorical values for a column from vendor_profiles.
    Returns empty list if discovery has not run for this table+column pair.
    Never raises — callers must handle empty list gracefully.
    """
```

**What it reads:** `vendor_profiles` table, filtered by `table_name` and
`column_name`. Returns the `observed_values` JSON field parsed as a list.

**Used by services to replace hardcoded constants:**
```python
# Instead of: KNOWN_DEPARTMENTS = ["Engineering", "Sales", ...]
# Do this:
from services.ingestion_service import get_discovered_values

def _get_known_departments() -> list[str]:
    values = get_discovered_values("hr_headcount", "department")
    if not values:
        LOGGER.warning("No discovered department values found — vendor_profiles may not be populated")
    return values
```

### `get_last_ingested_count(table_name: str) -> int | None`

Reads the row count from the most recent successful ingestion of a table from
`data_versions`. Returns `None` if no successful ingestion exists.

```python
def get_last_ingested_count(table_name: str) -> int | None:
    """
    Returns row count from the most recent loaded version of table_name.
    Returns None if no loaded version exists.
    Never raises.
    """
```

**What it reads:** `data_versions` table, filtered by `table_name` and
`status = 'loaded'`, ordered by `uploaded_at DESC`, takes `row_count` from
the first row.

**Used by services to replace hardcoded row count assertions:**
```python
# Instead of: if len(rows) != 6016: LOGGER.warning(...)
# Do this:
from services.ingestion_service import get_last_ingested_count

def _check_row_count(table_name: str, actual: int, threshold: float = 0.05) -> None:
    expected = get_last_ingested_count(table_name)
    if expected is None:
        LOGGER.warning("No ingested count found for %s — skipping row count check", table_name)
        return
    deviation = abs(actual - expected) / max(expected, 1)
    if deviation > threshold:
        LOGGER.warning(
            "Row count deviation for %s: expected ~%s, got %s (%.1f%% deviation)",
            table_name, expected, actual, deviation * 100
        )
```

The 5% threshold means: if `data_versions` says 6,016 were ingested and the
service returns fewer than 5,715 or more than 6,317, log a warning. This
catches data loss or corruption without breaking on legitimate data updates.

---

## Environment and Config Rules

### `.env` — all operational config lives here

```
SAAS_SPEND_DB_PATH=...
SAAS_SPEND_UPLOADS_DIR=...
SAAS_SPEND_VENDOR_RULES_PATH=...
SAAS_SPEND_AUDIT_DATE=2026-05-01
ACTIVE_VENDORS=Atlassify,Nexaflow,Cloudora
```

**`ACTIVE_VENDORS` is a comma-separated string. Parse it at module load:**
```python
import os
ACTIVE_VENDORS: list[str] = [
    v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()
]
```

When adding Veloxa, Databridge, Prismly: update `.env` only. Zero code changes.

### `config/vendor_rules.py` — discovery output only

This file is written by the ingestion service after a discovery run. Service
files must not import constants from it directly. They call
`ingestion_service.get_discovered_values()` instead. `vendor_rules.py` is
an internal store, not a public interface.

### No hardcoded values anywhere in service files

The following must never appear as literals in any service file:

| Value type | Wrong | Right |
|---|---|---|
| Vendor names | `"Atlassify"` | Read from `ACTIVE_VENDORS` env var |
| Department names | `"Engineering"` | `get_discovered_values("hr_headcount", "department")` |
| Exit type values | `"voluntary"` | `get_discovered_values("hr_headcount", "exit_type")` |
| Job level values | `"L1"` through `"L7"` | `get_discovered_values("hr_headcount", "job_level")` |
| Seat type values | `"Full"` | `get_discovered_values("vendor_overview", "seat_type")` |
| Contract status values | `"active"` | `get_discovered_values("vendor_overview", "contract_status")` |
| Row counts | `6016`, `4222`, `180` | `get_last_ingested_count("hr_headcount")` |
| Threshold percentages | `0.05` | `.env` as `ROW_COUNT_DEVIATION_THRESHOLD=0.05` |

---

## Redefined Service Functions

### `services/ingestion_service.py` additions

Add these two functions to the existing file. No other changes.

#### `get_discovered_values(table_name, column_name) → list`
Described above.

#### `get_last_ingested_count(table_name) → int | None`
Described above.

---

### `services/contract_service.py`

No function removals. The boundary is correct — contract service reads raw
contract data and applies only dedup and filtering. The refactor here is
purely about removing any hardcoded constants.

**Module-level setup (replace any hardcoded vendor references):**
```python
import os
ACTIVE_VENDORS: list[str] = [
    v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()
]
```

#### `get_entitlement(vendor=None, version=None) → list[dict]`

No change to logic. Remove any hardcoded vendor name strings.
The dedup `GROUP BY vendor, sku, seat_type` stays exactly as is.

**Columns returned — unchanged:**
`vendor`, `sku`, `seat_type`, `effective_total_seats`, `unit_price`,
`notice_deadline`, `auto_renewal`, `true_down_rights`, `measurement_method`,
`contract_status`

#### `get_active_contracts(vendor=None, version=None) → list[dict]`

No change to logic. Remove any hardcoded strings.

**Columns returned — unchanged:**
`of_id`, `vendor`, `sku`, `seat_type`, `contracted_seats`,
`effective_total_seats`, `unit_price`, `contract_start`, `contract_expiry`,
`notice_deadline`, `auto_renewal`, `true_down_rights`, `measurement_method`,
`contract_event_type`, `contract_group_id`

#### `get_contract_history(vendor, sku, seat_type, version=None) → list[dict]`

No change to logic. Vendor validation against `ACTIVE_VENDORS` stays but
must read from env, not from a hardcoded list.

**Columns returned — unchanged:**
`of_id`, `vendor`, `sku`, `seat_type`, `contracted_seats`,
`effective_total_seats`, `unit_price`, `contract_start`, `contract_expiry`,
`contract_status`, `contract_event_type`, `predecessor_of_id`, `seat_delta`,
`contract_group_id`

---

### `services/license_service.py` — full refactor

Remove: `get_ghost_licenses()`, `get_reclamation_candidates()`,
`get_utilization_summary()`

Keep and rename: `get_active_provisioned()` → `get_raw_licenses()`

**Module-level setup:**
```python
import os
from services.ingestion_service import get_discovered_values, get_last_ingested_count

ACTIVE_VENDORS: list[str] = [
    v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()
]
```

---

#### `get_raw_licenses(vendor=None, status_filter=None, version=None) → list[dict]`

**Purpose:** Raw license records from the versioned table. The single data
access function for the entire license table. All filtering is by raw column
values only — no interpretation, no joins, no aggregation.

**What the processing layer passes:**
- `status_filter=["active", "over_tier"]` → for true-up provisioned count
- `status_filter=["ghost"]` → for ghost detection input
- `status_filter=None` → for all licenses (utilization aggregation, etc.)
- `status_filter=["active", "over_tier", "ghost"]` → for cost-at-risk roll-up

**Source table:** `license_utilization_v{N}`

**SQL:**
```sql
SELECT
    license_id,
    vendor,
    sku,
    seat_type,
    assigned_email,
    employee_id,
    department,
    job_level,
    provisioned_date,
    last_active_date,
    license_status,
    usage_tier,
    seat_tier_match,
    monthly_cost,
    cost_at_risk,
    annual_cost,
    active_usage_rate,
    login_events_30d,
    days_since_last_active,
    days_since_provisioned,
    contract_days_remaining,
    days_until_notice,
    renewal_urgency,
    notice_deadline,
    auto_renewal,
    true_down_rights,
    measurement_method,
    current_of_id,
    of_id,
    reclamation_candidate,
    churn_risk_score
FROM license_utilization_v{N}
WHERE vendor IN ({ACTIVE_VENDORS placeholders})
  -- if vendor param passed: AND vendor = ?
  -- if status_filter passed: AND license_status IN ({placeholders})
ORDER BY vendor, sku, seat_type, license_id
```

**Columns returned:** All columns listed above. This is the one function that
returns a wide projection because the processing layer needs different subsets
depending on its computation. Column projection happens in the processing layer,
not here.

**Note on `reclamation_candidate` and `churn_risk_score`:** These are
pre-computed columns baked into the dataset. They are returned as raw data
fields. The processing layer may use them as inputs to its own reclamation
logic but does not treat them as authoritative — they are signals, not verdicts.

**Return shape (single row):**
```python
{
    "license_id": "LIC-0000042",
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "assigned_email": "jane.doe@company.com",
    "employee_id": "EMP-00042",
    "department": "Engineering",
    "job_level": "L3",
    "provisioned_date": "2021-03-15",
    "last_active_date": "2026-04-28",
    "license_status": "active",
    "usage_tier": "power",
    "seat_tier_match": "match",
    "monthly_cost": 12.50,
    "cost_at_risk": 0.0,
    "annual_cost": 150.0,
    "active_usage_rate": 0.87,
    "login_events_30d": 18,
    "days_since_last_active": 3.0,
    "days_since_provisioned": 1872,
    "contract_days_remaining": 245,
    "days_until_notice": 153,
    "renewal_urgency": "ok",
    "notice_deadline": "2026-09-30",
    "auto_renewal": True,
    "true_down_rights": False,
    "measurement_method": "peak",
    "current_of_id": "V1-OF-008",
    "of_id": "V1-OF-003",
    "reclamation_candidate": False,
    "churn_risk_score": 0.12
}
```

**Row count check:**
```python
_check_row_count("license_utilization", len(rows))
# Expected ~27,646 total. 3-vendor subset will be proportionally less.
# Threshold: warn if deviation from last ingested count exceeds 5%
```

**Null handling:**
- `last_active_date`, `days_since_last_active` — null for `deprovisioned`
  (4,148 rows). Return as `None`.
- `churn_risk_score` — null for `ghost` (6,828) and `deprovisioned` (4,148).
  Return as `None`.

---

### `services/employee_service.py` — refactor only, no removals

All five functions stay. Changes are:
- Remove `KNOWN_DEPARTMENTS` hardcoded list
- Remove `ALLOWED_EXIT_TYPES` hardcoded set
- Remove hardcoded `len(rows) != 6016` assertions
- Replace all three with runtime-read equivalents

**Module-level setup (replaces hardcoded constants):**
```python
import os
import logging
from services.ingestion_service import get_discovered_values, get_last_ingested_count

LOGGER = logging.getLogger(__name__)

def _get_known_departments() -> list[str]:
    """Read discovered department values from vendor_profiles."""
    values = get_discovered_values("hr_headcount", "department")
    if not values:
        LOGGER.warning(
            "No discovered department values in vendor_profiles — "
            "get_department_headcount will not guarantee all departments present"
        )
    return values

def _get_allowed_exit_types() -> set[str]:
    """Read discovered exit_type values from vendor_profiles."""
    values = get_discovered_values("hr_headcount", "exit_type")
    if not values:
        LOGGER.warning("No discovered exit_type values in vendor_profiles")
    return set(values)

def _check_row_count(
    table_name: str,
    actual: int,
    threshold: float = float(os.getenv("ROW_COUNT_DEVIATION_THRESHOLD", "0.05"))
) -> None:
    """Soft check: warn if actual row count deviates from last ingested count."""
    expected = get_last_ingested_count(table_name)
    if expected is None:
        LOGGER.warning(
            "No ingested count found for %s — skipping row count check", table_name
        )
        return
    deviation = abs(actual - expected) / max(expected, 1)
    if deviation > threshold:
        LOGGER.warning(
            "Row count deviation for %s: expected ~%s from data_versions, "
            "got %s (%.1f%% deviation — threshold %.0f%%)",
            table_name, expected, actual, deviation * 100, threshold * 100
        )
```

Add to `.env`:
```
ROW_COUNT_DEVIATION_THRESHOLD=0.05
```

---

#### `get_active_employees(version=None) → list[dict]`

No logic change. Remove hardcoded count assertion.

```python
# Replace this:
if len(rows) != 6016:
    LOGGER.warning("Expected 6,016 active employees but found %s", len(rows))

# With this:
_check_row_count("hr_headcount", len(rows))
# Note: hr_headcount total includes active + exited + pre-hire.
# The deviation check compares against total ingested count, not just active.
# A 5% threshold on 10,418 total = warn if active count suggests > 521 rows
# are missing or duplicated relative to last ingested total.
```

**Columns returned — unchanged:**
`employee_id`, `email`, `department`, `job_level`, `region`, `is_active`,
`hire_date`

---

#### `get_exited_employees(version=None) → list[dict]`

No logic change. Remove hardcoded count. Replace exit_type validation.

```python
# Replace this:
ALLOWED_EXIT_TYPES = {"voluntary", "layoff", "performance", "retirement"}
for row in rows:
    if row.get("exit_type") not in ALLOWED_EXIT_TYPES:
        LOGGER.warning(...)

# With this:
allowed = _get_allowed_exit_types()
if allowed:  # only validate if discovery has run
    for row in rows:
        exit_type = row.get("exit_type")
        if exit_type is not None and exit_type not in allowed:
            LOGGER.warning(
                "Unexpected exit_type value %r — not in discovered values %s",
                exit_type, allowed
            )
```

**SQL filter stays:** `WHERE employee_status = 'exited'` — correct. This
correctly excludes pre-hire rows that also have `is_active = 0`.

**Columns returned — unchanged:**
`employee_id`, `email`, `department`, `job_level`, `region`, `is_active`,
`exit_date`, `exit_type`

---

#### `get_future_hires(department=None, before_date=None, version=None) → list[dict]`

No logic change. The Python-side filtering of `department` and `before_date`
is acceptable here since the full pre-hire population is 180 rows — pushing
filters to SQL is an optimization, not a correctness requirement at this scale.

**Columns returned — unchanged:**
`employee_id`, `email`, `department`, `job_level`, `region`, `hire_date`,
`employee_status`

---

#### `get_employee_by_email(email, version=None) → dict`

No change. Logic is correct as implemented.

**Columns returned — unchanged:**
`employee_id`, `email`, `department`, `job_level`, `region`, `is_active`,
`hire_date`, `exit_date`, `exit_type`, `manager_id`

---

#### `get_department_headcount(version=None) → dict`

Replace hardcoded department list with discovered values. The zero-fill logic
stays but uses the discovered list instead of a literal.

```python
# Replace this:
KNOWN_DEPARTMENTS = ["Engineering", "Sales", ...]
counts = {department: 0 for department in KNOWN_DEPARTMENTS}

# With this:
known = _get_known_departments()
counts = {dept: 0 for dept in known}
# If known is empty (discovery not run), counts starts empty.
# Result will still be populated from the SQL query rows.
# A warning was already logged by _get_known_departments().
```

**Return shape — same structure, values read from discovery:**
```python
{
    "Engineering": 1847,
    "Sales": 1155,
    "Customer Success": 915,
    "Marketing": 613,
    "Operations & IT": 465,
    "Product": 424,
    "HR & People": 317,
    "Finance": 280
}
```

---

### `services/trueup_service.py` — no change

Stub as implemented. Raises `NotImplementedError`. No changes.

### `services/forecast_service.py` — no change

Stub as implemented. Raises `NotImplementedError`. No changes.

---

## What Moves to Phase 1C Processing Layer

These three functions are removed from `license_service` and become processing
layer modules:

| Removed Service Function | Becomes Processing Module | Input |
|---|---|---|
| `get_ghost_licenses()` | `processing/ghost_detector.py` | `license_service.get_raw_licenses(status_filter=None)` + `employee_service.get_exited_employees()` |
| `get_reclamation_candidates()` | `processing/reclamation_detector.py` | `license_service.get_raw_licenses()` + `employee_service.get_active_employees()` |
| `get_utilization_summary()` | `processing/utilization_aggregator.py` | `license_service.get_raw_licenses()` |

The processing layer calls `get_raw_licenses()` with appropriate filters and
derives the signal itself. The service layer has no knowledge of what ghost,
reclamation, or utilization mean.

---

## Impact on Existing Tests — 87 Tests

Most of the 87 passing tests remain valid. The changes are targeted.

### Tests that need updating

| Test | Change |
|---|---|
| `test_get_ghost_licenses_*` (all) | Delete — function removed from service layer |
| `test_get_reclamation_candidates_*` (all) | Delete — function removed |
| `test_get_utilization_summary_*` (all) | Delete — function removed |
| `test_get_active_provisioned_*` | Rename to `test_get_raw_licenses_*`, update function name in call |
| `test_get_department_headcount_all_eight_departments` | Update — now validates against discovered values, not hardcoded list |
| Any test asserting exact row count as hardcoded number | Update — assert within 5% of last ingested count instead |

### Tests that stay unchanged

All `contract_service` tests — logic unchanged, only constants refactored.
All `employee_service` function tests except headcount department list.
All stub tests (`trueup_service`, `forecast_service`).
All integration tests — join assumptions unchanged.

### New tests required

| Test | What to Assert |
|---|---|
| `test_get_raw_licenses_no_filter` | Returns all active vendor rows, all `license_status` values present |
| `test_get_raw_licenses_status_filter_active_overtier` | Returns only `active` and `over_tier` rows |
| `test_get_raw_licenses_status_filter_ghost` | Returns only `ghost` rows — processing layer can call this |
| `test_get_raw_licenses_columns_complete` | All 30 columns present in every returned dict |
| `test_get_discovered_values_departments` | Returns non-empty list for `hr_headcount` + `department` |
| `test_get_discovered_values_exit_types` | Returns non-empty list for `hr_headcount` + `exit_type` |
| `test_get_discovered_values_unknown_column` | Returns empty list, does not raise |
| `test_get_last_ingested_count_hr_headcount` | Returns integer close to 10,418 |
| `test_get_last_ingested_count_unknown_table` | Returns `None`, does not raise |
| `test_row_count_check_warns_on_deviation` | Patch `get_last_ingested_count` to return 10418, pass 9000 rows, assert warning logged |

---

## Summary of All Changes

| File | Change Type | What Changes |
|---|---|---|
| `.env` | Addition | `ACTIVE_VENDORS`, `ROW_COUNT_DEVIATION_THRESHOLD` |
| `services/ingestion_service.py` | Addition | `get_discovered_values()`, `get_last_ingested_count()` |
| `services/license_service.py` | Refactor | Remove 3 functions, rename 1 to `get_raw_licenses()`, add `status_filter` param, widen column projection |
| `services/contract_service.py` | Refactor | Replace hardcoded vendor references with env var |
| `services/employee_service.py` | Refactor | Remove 3 hardcoded constants, replace with discovery functions and soft row count check |
| `services/trueup_service.py` | No change | — |
| `services/forecast_service.py` | No change | — |
| `schemas/` | No change | — |
| `processing/` | Phase 1C | `ghost_detector`, `reclamation_detector`, `utilization_aggregator` added here |

---

## Build Order for This Refactor

1. Add `ACTIVE_VENDORS` and `ROW_COUNT_DEVIATION_THRESHOLD` to `.env`
2. Add `get_discovered_values()` and `get_last_ingested_count()` to
   `ingestion_service.py`
3. Write and run `test_get_discovered_values_*` and
   `test_get_last_ingested_count_*` — confirm discovery data is readable
4. Refactor `services/employee_service.py` — remove constants, add soft checks
5. Refactor `services/contract_service.py` — replace vendor references
6. Refactor `services/license_service.py` — remove 3 functions, add
   `get_raw_licenses()`
7. Update test file — delete removed function tests, rename active_provisioned
   tests, add new `get_raw_licenses` tests
8. Run full test suite — target: all remaining tests pass

---

## What Does Not Change

- `db/connection.py` — no changes
- `db/schema.py` — no changes
- `config/vendor_rules.py` — written by ingestion, not imported by services
- `schemas/` — no changes
- `exceptions.py` — no changes
- Phase 1A ingestion logic — no changes, only additions

---

*Phase 1B Services Redefined · Audit Date: 2026-05-01 · Active Vendors: read
from .env · No hardcoded constants in service files · Ghost/reclamation/
utilization signals deferred to Phase 1C processing layer*
