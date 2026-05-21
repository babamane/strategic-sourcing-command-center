# SaaS Spend Management — Phase 1B: Services Layer Spec

**Phase:** 1B — Services Layer Only
**Depends on:** Phase 1A (ingestion layer complete, versioned SQLite tables live,
`db/connection.py` working, `current_versions` promoted)
**Audit Date Constant:** `2026-05-01` — read from `.env` as `SAAS_SPEND_AUDIT_DATE`
**Active Vendors:** Atlassify, Nexaflow, Cloudora only
**Deferred Vendors:** Databridge, Prismly, Veloxa — reserved for pipeline
validation and demos in a later phase
**Primary Consumer:** Internal processing layer (no UI, no agents, no API yet)

---

## What This Phase Builds

Four service files and three Pydantic schemas. Nothing else.

- `schemas/vendor_contract.py`
- `schemas/employee.py`
- `schemas/license_record.py`
- `services/contract_service.py`
- `services/license_service.py`
- `services/employee_service.py`
- `services/trueup_service.py`

API layer, processing layer, and notification layer are all deferred to later
phases. The processing layer is not built yet — `trueup_service.py` is specced
here as a stub that will be completed once the processing layer exists.

---

## Folder Structure — This Phase Only

```
saas_managment/
├── schemas/
│   ├── vendor_contract.py       ← BUILD THIS
│   ├── employee.py              ← BUILD THIS
│   ├── license_record.py        ← BUILD THIS
│   └── data_version.py          ← ALREADY BUILT (Phase 1A)
├── services/
│   ├── ingestion_service.py     ← ALREADY BUILT (Phase 1A) — do not modify
│   ├── contract_service.py      ← BUILD THIS
│   ├── license_service.py       ← BUILD THIS
│   ├── employee_service.py      ← BUILD THIS
│   └── trueup_service.py        ← BUILD STUB ONLY
├── db/
│   ├── connection.py            ← ALREADY BUILT — do not modify
│   └── schema.py                ← ALREADY BUILT — do not modify
├── config/
│   └── vendor_rules.py          ← ALREADY BUILT — do not modify
├── exceptions.py                ← ALREADY BUILT — do not modify
└── .env                         ← ADD: SAAS_SPEND_AUDIT_DATE=2026-05-01
```

---

## Layer Rules — Non-Negotiable

| From | To | Allowed |
|---|---|---|
| `services/` | `db/connection.py` | Yes — services call `get_connection()` directly |
| `services/` | `schemas/` | Yes — for return type construction and validation |
| `services/` | other `services/` | Only `trueup_service` may call other services |
| Anything | `db/schema.py` | NEVER — schema.py is startup-only |
| Anything | raw sqlite3 outside `db/` | NEVER |

**Return type rule:** Every service function returns `list[dict]` or `dict`.
Never a pandas DataFrame. Never a raw sqlite3 cursor. Never a Pydantic model
instance directly — serialize to dict before returning so callers have no
Pydantic dependency.

**Version parameter rule:** Every service function accepts
`version: int = None`. When `None`, `get_connection()` resolves the currently
promoted version from `current_versions`. When an integer is passed, that
specific versioned table is used. The caller decides — the service never
assumes.

**Vendor scope rule:** All service functions accept `vendor: str = None`.
When passed, filter to that vendor only. When `None`, return all records but
only for `Atlassify`, `Nexaflow`, `Cloudora`. Do not hardcode the vendor list
inside service logic — read it from a constant in `config/vendor_rules.py`:

```python
# config/vendor_rules.py — add this constant
ACTIVE_VENDORS = ["Atlassify", "Nexaflow", "Cloudora"]
```

Services apply `WHERE vendor IN (ACTIVE_VENDORS)` on every query unless a
specific vendor is passed. This ensures deferred vendors never accidentally
appear in service output during this phase.

---

## Phase 1A File Reconciliation — No Renames, No Duplicates

Before touching any code, confirm the following. The Phase 1B spec introduces
only new files. Nothing from Phase 1A is renamed, moved, or duplicated.

### Existing Phase 1A files — do not touch

| Phase 1A File | Status in Phase 1B |
|---|---|
| `Saas_managment/.env` | Keep — add `SAAS_SPEND_AUDIT_DATE=2026-05-01` only |
| `Saas_managment/config/vendor_rules.py` | Keep — add `ACTIVE_VENDORS` constant only |
| `Saas_managment/db/connection.py` | Keep — no changes |
| `Saas_managment/db/schema.py` | Keep — no changes |
| `Saas_managment/exceptions.py` | Keep — no changes |
| `Saas_managment/main.py` | Keep — no changes |
| `Saas_managment/requirements.txt` | Keep — no additions needed this phase |
| `Saas_managment/services/ingestion_service.py` | Keep — no changes |

### New files introduced in Phase 1B

| New File | Notes |
|---|---|
| `Saas_managment/schemas/vendor_contract.py` | New folder `schemas/` — create it |
| `Saas_managment/schemas/employee.py` | |
| `Saas_managment/schemas/license_record.py` | |
| `Saas_managment/services/contract_service.py` | Folder already exists |
| `Saas_managment/services/license_service.py` | |
| `Saas_managment/services/employee_service.py` | |
| `Saas_managment/services/trueup_service.py` | Stub only this phase |

### Folder name note

Phase 1A uses `Saas_managment/` — this has a typo (missing `e`). The correct
spelling is `Saas_management/`. This is the last low-cost moment to fix it
before the codebase grows. Decision: either fix it now by renaming the root
folder, or accept the typo permanently. Do not fix it mid-phase — rename
before starting any Phase 1B file creation so all new files land in the
correct folder from the start.

### `schemas/` folder

Phase 1A has no `schemas/` folder. Create it fresh. Add an empty
`__init__.py` so it is importable as a Python package.

```
Saas_managment/schemas/__init__.py   ← empty file, required for imports
```

---

## Pre-Build Checklist

Before writing any code in this phase:

- [ ] Confirm `.env` has `SAAS_SPEND_AUDIT_DATE=2026-05-01`
- [ ] Confirm `ingestion_service.py` reads audit date from env, not `datetime.now()`
- [ ] Confirm versioned tables exist in SQLite:
      `vendor_overview_v1`, `hr_headcount_v1`, `license_utilization_v1`
- [ ] Confirm `current_versions` table has a promoted version for all three tables
- [ ] Add `ACTIVE_VENDORS = ["Atlassify", "Nexaflow", "Cloudora"]` to
      `config/vendor_rules.py`

---

## Pydantic Models — `schemas/`

Pure schema definitions only. No database logic. No service logic. No imports
from `db/` or `services/`. Used by service functions to validate return data
before serializing to dict.

**Coding agent rule:** Define all date fields as `Optional[date]` where nulls
are expected. Use `Optional[str]` not bare `str` for any field the README
marks as having nulls. Do not use `datetime` for date-only fields — use
`date` from the `datetime` module.

---

### `schemas/vendor_contract.py`

**Source table:** `vendor_overview_v{N}`
**Class name:** `VendorContract`

| Field | Python Type | Required | Allowed Values / Notes |
|---|---|---|---|
| `of_id` | `str` | Yes | e.g. `V1-OF-008` — primary key |
| `vendor` | `str` | Yes | |
| `sku` | `str` | Yes | |
| `seat_type` | `str` | Yes | `Full` / `Contributor` / `Collaborator` |
| `contracted_seats` | `int` | Yes | Amendment-level count — **never use for true-up** |
| `effective_total_seats` | `int` | Yes | **Always use this for true-up math** |
| `unit_price` | `float` | Yes | Per seat per month |
| `contract_start` | `date` | Yes | |
| `contract_expiry` | `date` | Yes | |
| `notice_deadline` | `date` | Yes | Action deadline — not expiry date |
| `auto_renewal` | `bool` | Yes | |
| `true_down_rights` | `bool` | Yes | |
| `measurement_method` | `str` | Yes | `peak` / `average` / `snapshot` |
| `contract_status` | `str` | Yes | `active` / `superseded` |
| `contract_event_type` | `str` | Yes | `new` / `renewal` / `upsell` / `amendment` |
| `contract_group_id` | `Optional[str]` | No | Groups parallel chains |
| `predecessor_of_id` | `Optional[str]` | No | Null for 81 chain-start OFs |
| `seat_delta` | `Optional[int]` | No | 0 for renewals, positive for upsells/amendments |

---

### `schemas/employee.py`

**Source table:** `hr_headcount_v{N}`
**Class name:** `Employee`

| Field | Python Type | Required | Allowed Values / Notes |
|---|---|---|---|
| `employee_id` | `str` | Yes | e.g. `EMP-00001` — primary key |
| `email` | `str` | Yes | **Primary join key to license table** |
| `department` | `str` | Yes | `Engineering` / `Sales` / `Customer Success` / `Marketing` / `Operations & IT` / `Product` / `HR & People` / `Finance` |
| `job_level` | `str` | Yes | `L1` through `L7` |
| `region` | `str` | Yes | `US` / `EU` / `APAC` |
| `is_active` | `bool` | Yes | |
| `hire_date` | `date` | Yes | |
| `exit_date` | `Optional[date]` | No | Null for 6,016 active employees |
| `exit_type` | `Optional[str]` | No | `voluntary` / `layoff` / `performance` / `retirement` — null if active. **Not** `resignation` or `termination` — those values do not exist |
| `manager_id` | `Optional[str]` | No | Null for 583 L6–L7 managers — not a data error |

**Permanently excluded — never add to this schema:**
`full_name`, `sub_team` — not join keys, not needed by processing layer.

---

### `schemas/license_record.py`

**Source table:** `license_utilization_v{N}`
**Class name:** `LicenseRecord`

Split into required load-bearing fields and optional enrichment fields.
Processing layer cannot function without required fields. Optional fields
may be null or absent without breaking processing.

**Required fields:**

| Field | Python Type | Allowed Values / Notes |
|---|---|---|
| `license_id` | `str` | e.g. `LIC-0000001` — primary key |
| `of_id` | `str` | FK → original OF in vendor_overview |
| `current_of_id` | `str` | FK → current active OF — **use this for renewal lookups, not `of_id`** |
| `vendor` | `str` | |
| `sku` | `str` | |
| `seat_type` | `str` | `Full` / `Contributor` / `Collaborator` |
| `assigned_email` | `str` | FK → `hr_headcount.email` — zero orphans confirmed |
| `employee_id` | `str` | Denormalized from HR |
| `department` | `str` | Denormalized from HR |
| `job_level` | `str` | Denormalized from HR |
| `license_status` | `str` | `active` / `ghost` / `deprovisioned` / `over_tier` |
| `usage_tier` | `str` | `power` / `moderate` / `underutilized` / `dormant` / `inactive` |
| `seat_tier_match` | `str` | `match` / `over_tier` / `under_tier` |
| `monthly_cost` | `float` | unit_price × 1 seat — pre-computed |
| `cost_at_risk` | `float` | >0 for ghost/deprovisioned only. 0 for active/over_tier |
| `reclamation_candidate` | `bool` | |
| `renewal_urgency` | `str` | `ok` / `expired` |
| `days_until_notice` | `int` | Audit date → notice_deadline |
| `contract_days_remaining` | `int` | Audit date → contract_expiry |
| `notice_deadline` | `date` | Denormalized from vendor_overview |
| `auto_renewal` | `bool` | Denormalized from vendor_overview |
| `true_down_rights` | `bool` | Denormalized from vendor_overview |
| `measurement_method` | `str` | Denormalized from vendor_overview |

**Optional enrichment fields:**

| Field | Python Type | Null Pattern / Notes |
|---|---|---|
| `churn_risk_score` | `Optional[float]` | Null for ghost (6,828) + deprovisioned (4,148) = 10,976 nulls total |
| `active_usage_rate` | `Optional[float]` | 0.00–1.00 |
| `login_events_30d` | `Optional[int]` | 0 for ghost/deprovisioned |
| `days_since_last_active` | `Optional[float]` | Null for deprovisioned only (4,148). Source of truth is `last_active_date` — this is derived |
| `last_active_date` | `Optional[date]` | Null for deprovisioned only. **Source of truth** |
| `days_since_provisioned` | `Optional[int]` | |
| `license_age_band` | `Optional[str]` | `new` / `maturing` / `established` / `legacy` |
| `tenure_days` | `Optional[int]` | Employee-level — identical across all license rows for one person |
| `hire_cohort_year` | `Optional[int]` | |
| `hire_cohort_half` | `Optional[str]` | `YYYY-H1` / `YYYY-H2` |
| `annual_cost` | `Optional[float]` | monthly_cost × 12 |
| `provisioned_date` | `Optional[date]` | 390 rows forward-dated past audit date — do not filter |
| `effective_license_date` | `Optional[date]` | Must fall within `of_id` contract window |

---

## Services — `services/`

### How to Read These Specs

Each function spec contains:
- **Signature** — exact function name and parameters
- **Source table** — which versioned SQLite table to query
- **SQL** — the exact query to run (parameterized)
- **Columns returned** — exact list, no extras
- **Return shape** — what a single dict in the returned list looks like
- **Validation** — what to assert before returning
- **Error behavior** — what to raise and when

**DB access pattern for all service functions:**

```python
from db.connection import get_connection
from config.vendor_rules import ACTIVE_VENDORS

conn = get_connection("vendor_overview", version)  # or hr_headcount, license_utilization
cursor = conn.cursor()
cursor.row_factory = sqlite3.Row  # enables dict-like access
```

Always close the connection after the query. Use a try/finally block.

---

### `services/contract_service.py`

**Source table:** `vendor_overview_v{N}` (resolved via `get_connection`)

**File-level imports required:**
```python
import sqlite3
from typing import Optional
from db.connection import get_connection
from config.vendor_rules import ACTIVE_VENDORS
from exceptions import DataNotReadyError
```

**Critical design note — dedup rule:**
Multiple active OFs can exist per `vendor + sku + seat_type` combination
(2–3 in this dataset). All carry the same `effective_total_seats` value.
The dedup must happen inside this service. The processing layer must never
replicate it. Use `GROUP BY vendor, sku, seat_type` with `MIN(of_id)` to
pick a stable representative row, then join back to get all fields for that
row. Do not `SUM(effective_total_seats)` — that double/triple-counts.

---

#### `get_entitlement(vendor: Optional[str] = None, version: Optional[int] = None) → list[dict]`

**Purpose:** Single source of entitlement truth for true-up math. Returns
one row per `vendor + sku + seat_type` grain. Dedup applied here.

**Source table:** `vendor_overview_v{N}`

**SQL:**
```sql
SELECT
    vendor,
    sku,
    seat_type,
    effective_total_seats,
    unit_price,
    notice_deadline,
    auto_renewal,
    true_down_rights,
    measurement_method,
    contract_status
FROM vendor_overview_v{N}
WHERE contract_status = 'active'
  AND vendor IN ({ACTIVE_VENDORS})
  -- if vendor param passed: AND vendor = ?
GROUP BY vendor, sku, seat_type
ORDER BY vendor, sku, seat_type
```

**Columns returned (exactly these, no others):**
`vendor`, `sku`, `seat_type`, `effective_total_seats`, `unit_price`,
`notice_deadline`, `auto_renewal`, `true_down_rights`, `measurement_method`,
`contract_status`

**Return shape (single row):**
```python
{
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "effective_total_seats": 850,
    "unit_price": 12.50,
    "notice_deadline": "2026-10-01",
    "auto_renewal": True,
    "true_down_rights": False,
    "measurement_method": "peak",
    "contract_status": "active"
}
```

**Validation before return:**
- Assert no duplicate `vendor + sku + seat_type` rows in result
- Assert `effective_total_seats > 0` for all rows
- If result is empty and no vendor filter was applied, raise `DataNotReadyError`

---

#### `get_active_contracts(vendor: Optional[str] = None, version: Optional[int] = None) → list[dict]`

**Purpose:** Returns all active Order Forms including parallel chains.
No dedup — returns multiple rows per `vendor + sku + seat_type` if parallel
chains exist. Used for contract detail views and renewal tracking.

**Source table:** `vendor_overview_v{N}`

**SQL:**
```sql
SELECT
    of_id,
    vendor,
    sku,
    seat_type,
    contracted_seats,
    effective_total_seats,
    unit_price,
    contract_start,
    contract_expiry,
    notice_deadline,
    auto_renewal,
    true_down_rights,
    measurement_method,
    contract_event_type,
    contract_group_id
FROM vendor_overview_v{N}
WHERE contract_status = 'active'
  AND vendor IN ({ACTIVE_VENDORS})
  -- if vendor param passed: AND vendor = ?
ORDER BY vendor, sku, seat_type, contract_start
```

**Columns returned (exactly these, no others):**
`of_id`, `vendor`, `sku`, `seat_type`, `contracted_seats`,
`effective_total_seats`, `unit_price`, `contract_start`, `contract_expiry`,
`notice_deadline`, `auto_renewal`, `true_down_rights`, `measurement_method`,
`contract_event_type`, `contract_group_id`

**Return shape (single row):**
```python
{
    "of_id": "V1-OF-008",
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "contracted_seats": 200,
    "effective_total_seats": 850,
    "unit_price": 12.50,
    "contract_start": "2025-01-01",
    "contract_expiry": "2026-01-01",
    "notice_deadline": "2025-10-01",
    "auto_renewal": True,
    "true_down_rights": False,
    "measurement_method": "peak",
    "contract_event_type": "renewal",
    "contract_group_id": "ATL-PROJ-FULL"
}
```

**Validation before return:**
- Assert all rows have `contract_status = 'active'` (no superseded rows)
- Assert `of_id` is unique across all rows

---

#### `get_contract_history(vendor: str, sku: str, seat_type: str, version: Optional[int] = None) → list[dict]`

**Purpose:** Full renewal chain for a specific `vendor + sku + seat_type`.
Returns both active and superseded OFs. Used for lineage tracing — not for
processing math.

**Source table:** `vendor_overview_v{N}`

**SQL:**
```sql
SELECT
    of_id,
    vendor,
    sku,
    seat_type,
    contracted_seats,
    effective_total_seats,
    unit_price,
    contract_start,
    contract_expiry,
    contract_status,
    contract_event_type,
    predecessor_of_id,
    seat_delta,
    contract_group_id
FROM vendor_overview_v{N}
WHERE vendor = ?
  AND sku = ?
  AND seat_type = ?
ORDER BY contract_start ASC
```

**Columns returned (exactly these, no others):**
`of_id`, `vendor`, `sku`, `seat_type`, `contracted_seats`,
`effective_total_seats`, `unit_price`, `contract_start`, `contract_expiry`,
`contract_status`, `contract_event_type`, `predecessor_of_id`, `seat_delta`,
`contract_group_id`

**Return shape (single row):**
```python
{
    "of_id": "V1-OF-001",
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "contracted_seats": 500,
    "effective_total_seats": 500,
    "unit_price": 11.00,
    "contract_start": "2019-01-01",
    "contract_expiry": "2020-01-01",
    "contract_status": "superseded",
    "contract_event_type": "new",
    "predecessor_of_id": None,
    "seat_delta": 500,
    "contract_group_id": "ATL-PROJ-FULL"
}
```

**Error behavior:**
- If no rows returned for the given `vendor + sku + seat_type`, raise
  `DataNotReadyError(f"No contract history for {vendor} / {sku} / {seat_type}")`
- Vendor must be in `ACTIVE_VENDORS` — raise `ValueError` otherwise

---

### `services/license_service.py`

**Source table:** `license_utilization_v{N}` (resolved via `get_connection`)

**File-level imports required:**
```python
import sqlite3
from typing import Optional
from db.connection import get_connection
from config.vendor_rules import ACTIVE_VENDORS
from exceptions import DataNotReadyError
```

**Column projection rule:** This table has 34 columns. Each function returns
only the exact columns its declared purpose requires. No function returns all
34 columns. No caller receives more than it needs.

**license_status definitions (for coding agent reference):**
- `active` — employed, provisioned, using the license
- `ghost` — exited employee, license never deprovisioned
- `deprovisioned` — license formally removed
- `over_tier` — seat type higher than job level warrants

---

#### `get_active_provisioned(vendor: Optional[str] = None, version: Optional[int] = None) → list[dict]`

**Purpose:** Returns licenses that count toward billable provisioned seats.
These are the records the vendor will bill against in a true-up.
`active` and `over_tier` both count — vendor does not discount over-tier seats.

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
    license_status,
    usage_tier,
    seat_tier_match,
    monthly_cost,
    current_of_id
FROM license_utilization_v{N}
WHERE license_status IN ('active', 'over_tier')
  AND vendor IN ({ACTIVE_VENDORS})
  -- if vendor param passed: AND vendor = ?
ORDER BY vendor, sku, seat_type
```

**Columns returned (exactly these, no others):**
`license_id`, `vendor`, `sku`, `seat_type`, `assigned_email`, `employee_id`,
`department`, `job_level`, `license_status`, `usage_tier`, `seat_tier_match`,
`monthly_cost`, `current_of_id`

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
    "license_status": "active",
    "usage_tier": "power",
    "seat_tier_match": "match",
    "monthly_cost": 12.50,
    "current_of_id": "V1-OF-008"
}
```

**Validation before return:**
- Assert all rows have `license_status` in `['active', 'over_tier']`
- If result is empty and no vendor filter was applied, raise `DataNotReadyError`

---

#### `get_ghost_licenses(vendor: Optional[str] = None, version: Optional[int] = None) → list[dict]`

**Purpose:** Returns all ghost records — exited employees whose licenses were
never deprovisioned. These are licenses the company is paying for with zero
utility. Primary cost-at-risk signal.

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
    license_status,
    cost_at_risk,
    monthly_cost,
    days_until_notice,
    renewal_urgency
FROM license_utilization_v{N}
WHERE license_status = 'ghost'
  AND vendor IN ({ACTIVE_VENDORS})
  -- if vendor param passed: AND vendor = ?
ORDER BY cost_at_risk DESC
```

**Columns returned (exactly these, no others):**
`license_id`, `vendor`, `sku`, `seat_type`, `assigned_email`, `employee_id`,
`department`, `license_status`, `cost_at_risk`, `monthly_cost`,
`days_until_notice`, `renewal_urgency`

**Return shape (single row):**
```python
{
    "license_id": "LIC-0001234",
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "assigned_email": "john.smith@company.com",
    "employee_id": "EMP-01234",
    "department": "Sales",
    "license_status": "ghost",
    "cost_at_risk": 12.50,
    "monthly_cost": 12.50,
    "days_until_notice": 142,
    "renewal_urgency": "ok"
}
```

**Expected counts (for 3-vendor scope — Atlassify + Nexaflow + Cloudora):**
Atlassify: 1,817 ghosts. Nexaflow and Cloudora contribute additional records.
Total across all three vendors will be a subset of the full 6,828.

**Validation before return:**
- Assert all rows have `license_status = 'ghost'`
- Assert `cost_at_risk >= 0` for all rows

---

#### `get_reclamation_candidates(vendor: Optional[str] = None, version: Optional[int] = None) → list[dict]`

**Purpose:** Returns all licenses flagged for reclamation. Ordered by cost
impact descending so processing layer can prioritize highest-value reclamations.

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
    license_status,
    usage_tier,
    reclamation_candidate,
    cost_at_risk,
    monthly_cost,
    churn_risk_score
FROM license_utilization_v{N}
WHERE reclamation_candidate = 1
  AND vendor IN ({ACTIVE_VENDORS})
  -- if vendor param passed: AND vendor = ?
ORDER BY cost_at_risk DESC, monthly_cost DESC
```

**Columns returned (exactly these, no others):**
`license_id`, `vendor`, `sku`, `seat_type`, `assigned_email`, `employee_id`,
`department`, `license_status`, `usage_tier`, `reclamation_candidate`,
`cost_at_risk`, `monthly_cost`, `churn_risk_score`

**Return shape (single row):**
```python
{
    "license_id": "LIC-0002001",
    "vendor": "Nexaflow",
    "sku": "Flow Automation",
    "seat_type": "Collaborator",
    "assigned_email": "alex.jones@company.com",
    "employee_id": "EMP-02001",
    "department": "Marketing",
    "license_status": "active",
    "usage_tier": "dormant",
    "reclamation_candidate": True,
    "cost_at_risk": 0.0,
    "monthly_cost": 8.00,
    "churn_risk_score": 0.87
}
```

**Null handling:** `churn_risk_score` is null for ghost and deprovisioned rows
even if `reclamation_candidate = True`. Do not filter these out — return them
with `churn_risk_score: None`.

**Validation before return:**
- Assert all rows have `reclamation_candidate = True`

---

#### `get_utilization_summary(vendor: Optional[str] = None, version: Optional[int] = None) → dict`

**Purpose:** Returns aggregated `usage_tier` counts grouped by
`vendor + sku + seat_type`. Returns a nested summary dict — not row-level
records. Used by the processing layer for portfolio-level analysis.

**Source table:** `license_utilization_v{N}`

**SQL:**
```sql
SELECT
    vendor,
    sku,
    seat_type,
    usage_tier,
    COUNT(*) as count
FROM license_utilization_v{N}
WHERE vendor IN ({ACTIVE_VENDORS})
  -- if vendor param passed: AND vendor = ?
GROUP BY vendor, sku, seat_type, usage_tier
ORDER BY vendor, sku, seat_type, usage_tier
```

**Return shape:**
```python
{
    "Atlassify": {
        "Project Suite": {
            "Full": {
                "power": 412,
                "moderate": 308,
                "underutilized": 91,
                "dormant": 12,
                "inactive": 203
            },
            "Contributor": { ... },
            "Collaborator": { ... }
        },
        "Wiki Lite": { ... }
    },
    "Nexaflow": { ... },
    "Cloudora": { ... }
}
```

**Usage tier reference:**
- `power` — high engagement
- `moderate` — regular usage
- `underutilized` — occasional usage
- `dormant` — near-zero usage
- `inactive` — no activity (includes all ghost + deprovisioned)

**Validation before return:**
- Assert all five usage tier keys are present for each `vendor + sku + seat_type`
  group. If a tier has zero records, include it with count `0` — do not omit.

---

### `services/employee_service.py`

**Source table:** `hr_headcount_v{N}` (resolved via `get_connection`)

**File-level imports required:**
```python
import sqlite3
from typing import Optional
from db.connection import get_connection
from exceptions import DataNotReadyError
```

**PII boundary rule:** `full_name` and `sub_team` are never returned by any
function in this file. Not in bulk functions. Not in the single-record lookup.
These columns do not exist in the service layer.

**Join key note:** `email` is the primary join key to `license_utilization`.
Every function that returns `email` enables a join to license records.
Zero orphans confirmed — every license `assigned_email` resolves to a
`hr_headcount.email` record.

**No vendor filter on this service.** HR headcount is not vendor-scoped.
`ACTIVE_VENDORS` does not apply here. All employee functions return records
across all employees regardless of which vendor licenses they hold.

---

#### `get_active_employees(version: Optional[int] = None) → list[dict]`

**Purpose:** Returns all currently employed employees. Used by the processing
layer for ghost detection cross-reference and department attribution.

**Source table:** `hr_headcount_v{N}`

**SQL:**
```sql
SELECT
    employee_id,
    email,
    department,
    job_level,
    region,
    is_active,
    hire_date
FROM hr_headcount_v{N}
WHERE is_active = 1
ORDER BY employee_id
```

**Columns returned (exactly these, no others):**
`employee_id`, `email`, `department`, `job_level`, `region`, `is_active`,
`hire_date`

**Return shape (single row):**
```python
{
    "employee_id": "EMP-00001",
    "email": "jane.doe@company.com",
    "department": "Engineering",
    "job_level": "L3",
    "region": "US",
    "is_active": True,
    "hire_date": "2021-03-15"
}
```

**Validation before return:**
- Assert all rows have `is_active = True`
- Expected count: 6,016 rows — log a warning if result deviates by more than 5%

---

#### `get_exited_employees(version: Optional[int] = None) → list[dict]`

**Purpose:** Returns all exited employees. Critical input for ghost detection
— cross-referenced against active license records to identify licenses that
were never deprovisioned after an employee left.

**Source table:** `hr_headcount_v{N}`

**SQL:**
```sql
SELECT
    employee_id,
    email,
    department,
    job_level,
    region,
    is_active,
    exit_date,
    exit_type
FROM hr_headcount_v{N}
WHERE is_active = 0
ORDER BY exit_date DESC
```

**Columns returned (exactly these, no others):**
`employee_id`, `email`, `department`, `job_level`, `region`, `is_active`,
`exit_date`, `exit_type`

**Return shape (single row):**
```python
{
    "employee_id": "EMP-03821",
    "email": "john.smith@company.com",
    "department": "Sales",
    "job_level": "L2",
    "region": "EU",
    "is_active": False,
    "exit_date": "2025-11-30",
    "exit_type": "voluntary"
}
```

**exit_type validation:** Allowed values are `voluntary`, `layoff`,
`performance`, `retirement` only. If any other value appears, log a warning —
do not raise, as this is a data quality signal, not a fatal error.

**Validation before return:**
- Assert all rows have `is_active = False`
- Assert all rows have a non-null `exit_date`
- Expected count: 4,222 rows — log a warning if result deviates by more than 5%

---

#### `get_employee_by_email(email: str, version: Optional[int] = None) → dict`

**Purpose:** Single employee lookup by email. Used for detail views and
per-license identity resolution. Returns one record or raises.

**Source table:** `hr_headcount_v{N}`

**SQL:**
```sql
SELECT
    employee_id,
    email,
    department,
    job_level,
    region,
    is_active,
    hire_date,
    exit_date,
    exit_type,
    manager_id
FROM hr_headcount_v{N}
WHERE email = ?
LIMIT 1
```

**Columns returned (exactly these, no others):**
`employee_id`, `email`, `department`, `job_level`, `region`, `is_active`,
`hire_date`, `exit_date`, `exit_type`, `manager_id`

**Note:** This is the only function that returns `exit_date`, `exit_type`, and
`manager_id`. These are excluded from bulk functions intentionally.

**Return shape:**
```python
{
    "employee_id": "EMP-00042",
    "email": "jane.doe@company.com",
    "department": "Engineering",
    "job_level": "L3",
    "region": "US",
    "is_active": True,
    "hire_date": "2021-03-15",
    "exit_date": None,
    "exit_type": None,
    "manager_id": "EMP-00010"
}
```

**Error behavior:**
- If no record found for the given email, raise
  `DataNotReadyError(f"No employee record found for email: {email}")`
- Returns a single dict, not a list

---

#### `get_department_headcount(version: Optional[int] = None) → dict`

**Purpose:** Returns active headcount grouped by department. Summary only —
no row-level data. Used by the processing layer for department-level spend
attribution.

**Source table:** `hr_headcount_v{N}`

**SQL:**
```sql
SELECT
    department,
    COUNT(*) as headcount
FROM hr_headcount_v{N}
WHERE is_active = 1
GROUP BY department
ORDER BY headcount DESC
```

**Return shape:**
```python
{
    "Engineering": 3048,
    "Sales": 2005,
    "Customer Success": 1587,
    "Marketing": 1066,
    "Operations & IT": 803,
    "Product": 684,
    "HR & People": 540,
    "Finance": 505
}
```

**Validation before return:**
- Assert all 8 known departments are present in the result. If a department
  is missing (zero active employees), include it with count `0`.
- Known departments: `Engineering`, `Sales`, `Customer Success`, `Marketing`,
  `Operations & IT`, `Product`, `HR & People`, `Finance`

---

### `services/trueup_service.py` — Stub Only

This file is specced as a stub in Phase 1B. It will be completed in Phase 1C
once the processing layer exists. Build the file and function signatures now
so the import chain is established, but do not implement computation logic yet.

**File-level imports required:**
```python
import sqlite3
from typing import Optional
from db.connection import get_connection
from config.vendor_rules import ACTIVE_VENDORS
from exceptions import DataNotReadyError
```

**Functions to stub:**

```python
def compute_snapshot(vendor: Optional[str] = None,
                     version: Optional[int] = None) -> list[dict]:
    """
    Phase 1C — not implemented yet.
    Will call processing/trueup_processor.compute() once processing layer exists.
    Stub raises NotImplementedError so callers fail loudly, not silently.
    """
    raise NotImplementedError("trueup_service.compute_snapshot is implemented in Phase 1C")


def get_latest_snapshot(vendor: Optional[str] = None) -> list[dict]:
    """
    Phase 1C — not implemented yet.
    Will query trueup_snapshots table once snapshots exist.
    """
    raise NotImplementedError("trueup_service.get_latest_snapshot is implemented in Phase 1C")


def get_snapshot_history(vendor: Optional[str] = None) -> list[dict]:
    """
    Phase 1C — not implemented yet.
    Will return all past snapshots with computed_at timestamps.
    """
    raise NotImplementedError("trueup_service.get_snapshot_history is implemented in Phase 1C")
```

**Do not implement any SQL or computation in this file in Phase 1B.**

---

## Expected Data Volumes (3-Vendor Scope)

These are reference figures for the three active vendors only.
Use to validate service output during build.

**vendor_overview (Atlassify + Nexaflow + Cloudora):**
- Atlassify: 3 SKUs — Project Suite, Wiki Lite, Reporting Add-on
- Nexaflow: 4 SKUs — Flow Automation, Flow Lite, Analytics Engine, Mobile Access
- Cloudora: 2 SKUs — Cloud Infra Core, DevOps Toolkit
- Active OFs across these three vendors: subset of 81 total active OFs
- `contract_status = 'active'` rows only used by `get_entitlement`

**license_utilization (Atlassify + Nexaflow + Cloudora):**
- Total 27,646 rows across all 6 vendors — 3-vendor subset is proportional
- Atlassify ghosts: 1,817
- Nexaflow has 261 `renewal_urgency = 'expired'` licenses
- Cloudora has 218 `renewal_urgency = 'expired'` licenses

**hr_headcount:**
- Not vendor-scoped — all 10,238 rows always available
- 6,016 active, 4,222 exited

---

## Build Order

1. Add `ACTIVE_VENDORS = ["Atlassify", "Nexaflow", "Cloudora"]` to
   `config/vendor_rules.py`
2. Add `SAAS_SPEND_AUDIT_DATE=2026-05-01` to `.env`
3. `schemas/vendor_contract.py`
4. `schemas/employee.py`
5. `schemas/license_record.py`
6. `services/contract_service.py`
   — test: `get_entitlement()` returns no duplicate `vendor+sku+seat_type` rows
   — test: `get_entitlement(vendor="Nexaflow")` returns only Nexaflow rows
7. `services/license_service.py`
   — test: `get_active_provisioned()` returns only `active` and `over_tier` rows
   — test: `get_ghost_licenses()` returns only `ghost` rows
   — test: `get_utilization_summary()` has all five tier keys for every group
8. `services/employee_service.py`
   — test: `get_active_employees()` returns exactly 6,016 rows
   — test: `get_exited_employees()` returns exactly 4,222 rows
   — test: `get_employee_by_email("nonexistent@x.com")` raises `DataNotReadyError`
9. `services/trueup_service.py` — stub only, no logic

---

## What Is Explicitly Not In This Phase

- FastAPI routes — Phase 1C
- Processing layer (`trueup_processor`, `ghost_detector`, `shelfware_detector`) — Phase 1C
- `trueup_snapshots` SQLite table — Phase 1C
- Notification / mail service — future phase
- Databridge, Prismly, Veloxa vendor data — reserved for pipeline validation
- Authentication — future phase
- Async / aiosqlite — future phase

---

*Phase 1B Spec · Services Layer Only · Active Vendors: Atlassify, Nexaflow,
Cloudora · Audit Date: 2026-05-01*
