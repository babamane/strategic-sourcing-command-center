# SaaS Spend Management — Phase 1C: Processing Layer

**Phase:** 1C — Processing Layer  
**Depends on:** Phase 1B complete — service layer verified, 101 tests passing,
`hr_headcount_v2` and `license_utilization_v4` promoted as current versions  
**Audit Date:** `2026-05-01` — read from `.env` as `SAAS_SPEND_AUDIT_DATE`  
**Active Vendors:** Read from `.env` as `ACTIVE_VENDORS`  
**Source of truth:** `SAAS_BASE_LAYER_README_V5.md`  
**Version:** v2

---

## Purpose of This Phase

Phase 1C builds the processing layer — the signal derivation tier that sits
between the service layer and every consumer above it (API, dashboard, chatbot).

Every processor in this phase:
- Receives data through a `ProcessingContext` object — never imports or calls
  service functions directly
- Joins across context data — never joins inside a service function
- Derives signals — classifies, aggregates, scores, ranks
- Returns typed output objects defined in `schemas/processing_results.py` —
  no raw dicts at any public function boundary
- Is independently runnable and independently testable by injecting a
  hand-built context

The chatbot tool surface is the primary design constraint for this phase.
Every processor must answer real procurement questions, not just produce
analytics tables. Where the question requires department or job level
granularity, the processor emits that grain. Where the question is
forward-looking, the processor uses the pre-hire pipeline.

---

## Architectural Boundary

```
SERVICE LAYER           FACADE LAYER                PROCESSING LAYER        CONSUMERS
(raw versioned rows)    (single coupling point)     (signal derivation)     (API/chatbot/dashboard)

contract_service  ──┐                               trueup_processor
                    ├──→  context_builder.py   ──→  breakdown_enricher ──→  chatbot tools
license_service   ──┤     builds                    ghost_detector          API endpoints
                    │     ProcessingContext          reclamation_detector    dashboard views
employee_service  ──┘                               utilization_aggregator
                                                    license_demand_forecaster
                                                    renewal_pressure_forecaster
```

**The Facade layer rule — one file owns all service coupling:**
`context_builder.py` is the only file in the entire `processing/` package that
imports from `services/`. It fetches data from the service layer, assembles it
into a `ProcessingContext` dataclass, and hands it to processors. If a service
function signature changes, `context_builder.py` is the only file that needs
updating. No processor file changes.

**Processing layer rules — enforced at every step:**
- Processors receive a `ProcessingContext` — never import from `services/`
  or `db/`.
- Never write back to any SQLite table.
- Never hardcode vendor names, department names, job levels, or row counts.
- Read `SAAS_SPEND_AUDIT_DATE` from `.env` for all date arithmetic.
- Read `ACTIVE_VENDORS` from `.env` for all vendor filtering.
- Return typed dataclass instances defined in `schemas/proc_results.py`.
  No raw dicts at any public function boundary.
- Every public function includes a `computed_at` timestamp in its output.

---

## File Structure

```
processing/
    __init__.py
    context_builder.py          ← ONLY file that imports from services/
    trueup_processor.py
    breakdown_enricher.py
    ghost_detector.py
    reclamation_detector.py
    utilization_aggregator.py
    license_demand_forecaster.py
    renewal_pressure_forecaster.py

schemas/
    __init__.py                     ← already exists from Phase 1B
    svc_vendor_contract.py          ← renamed from vendor_contract.py (Phase 1B)
    svc_employee.py                 ← renamed from employee.py (Phase 1B)
    svc_license_record.py           ← renamed from license_record.py (Phase 1B)
    proc_results.py                 ← NEW — typed output shapes for all processors
    proc_forecast_results.py        ← NEW stub — typed shapes for future ML outputs

processing_main.py          ← manual runner, mirrors services_main.py pattern
processing_smoke_test.py    ← smoke test, mirrors services_smoke_test.py pattern

tests/
    conftest.py                         ← pytest convention, no prefix
    test_proc_context_builder.py
    test_proc_trueup.py
    test_proc_breakdown.py
    test_proc_ghost.py
    test_proc_reclamation.py
    test_proc_utilization.py
    test_proc_demand_forecast.py
    test_proc_renewal_pressure.py
    test_proc_integration.py
```

---

## Environment and Config Rules

All rules from Phase 1B apply without exception.

```python
import os

AUDIT_DATE: str = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")
ACTIVE_VENDORS: list[str] = [
    v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()
]
```

No processor file may contain a hardcoded date, vendor name, department name,
job level string, or numeric row count. If a processor needs to know known
departments or job levels, those values arrive through the `ProcessingContext`
— the context builder reads them via `ingestion_service.get_discovered_values()`
before assembling the context.

**Absolute import rule for processor files:**
No processor file may contain `from services.` or `import services.` at any
level. Linting or a pre-commit hook should enforce this. The only permitted
service import in the entire `processing/` package is in `context_builder.py`.

---

## `ProcessingContext` — The Data Contract Between Layers

`ProcessingContext` is a plain Python dataclass defined in
`processing/context_builder.py`. It holds all pre-fetched service data that
processors need. Processors never fetch data — they receive it.

```python
from dataclasses import dataclass

@dataclass
class ProcessingContext:
    # Raw service data — fetched once per query by context_builder
    licenses: list[dict]              # get_raw_licenses() — all statuses
    entitlement: list[dict]           # get_entitlement()
    active_contracts: list[dict]      # get_active_contracts()
    active_employees: list[dict]      # get_active_employees()
    exited_employees: list[dict]      # get_exited_employees()
    future_hires: list[dict]          # get_future_hires()

    # Discovery-backed metadata — read once via ingestion_service
    known_departments: list[str]      # get_discovered_values("hr_headcount", "department")
    known_job_levels: list[str]       # get_discovered_values("hr_headcount", "job_level")

    # Runtime config
    audit_date: str                   # SAAS_SPEND_AUDIT_DATE from .env
    active_vendors: list[str]         # ACTIVE_VENDORS from .env
    fetched_at: str                   # ISO timestamp of when context was built
```

**Context is assembled once per query — not once per processor.**
The API route handler, chatbot tool executor, or manual runner calls
`build_context()` once, then passes the same context object to however many
processors it needs. This means a chatbot query requiring two processor calls
(e.g. `get_trueup_exposure` then `get_trueup_breakdown`) hits the service
layer only once.

**Context is always passed — never mutated.**
Processors read from the context. They never modify it. If a processor needs a
filtered subset of licenses, it filters in its own local scope.

**Context fields that are not needed are still present.**
Every context always contains all fields. Processors ignore what they don't
need. This means the context builder has one consistent interface regardless
of which processor will consume it.

---

## `processing/context_builder.py`

The only file in `processing/` that imports from `services/`. All other
processor files import from `processing.context_builder` only.

```python
import os
import logging
from datetime import datetime

from services.contract_service import get_entitlement, get_active_contracts
from services.license_service import get_raw_licenses
from services.employee_service import (
    get_active_employees,
    get_exited_employees,
    get_future_hires,
)
from services.ingestion_service import get_discovered_values

LOGGER = logging.getLogger(__name__)

AUDIT_DATE: str = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")
ACTIVE_VENDORS: list[str] = [
    v.strip() for v in os.getenv("ACTIVE_VENDORS", "").split(",") if v.strip()
]


def build_context(
    vendor: str | None = None,
    version: str | None = None,
) -> ProcessingContext:
    """
    Fetches all data required by the processing layer from the service layer.
    Assembles and returns a ProcessingContext.
    Optional vendor narrows license and contract fetches to a single vendor.
    version passed through to all service calls — None resolves to current.
    """
    return ProcessingContext(
        licenses=get_raw_licenses(vendor=vendor, version=version),
        entitlement=get_entitlement(vendor=vendor, version=version),
        active_contracts=get_active_contracts(vendor=vendor, version=version),
        active_employees=get_active_employees(version=version),
        exited_employees=get_exited_employees(version=version),
        future_hires=get_future_hires(version=version),
        known_departments=get_discovered_values("hr_headcount", "department"),
        known_job_levels=get_discovered_values("hr_headcount", "job_level"),
        audit_date=AUDIT_DATE,
        active_vendors=ACTIVE_VENDORS if vendor is None else [vendor],
        fetched_at=datetime.utcnow().isoformat(),
    )
```

**What this means for the API layer (Phase 1D):**

```python
# API route handler — total coupling surface is two imports
from processing.context_builder import build_context
from processing.trueup_processor import get_trueup_exposure

@app.get("/api/v1/trueup")
def trueup_endpoint(vendor: str = None):
    ctx = build_context(vendor=vendor)
    return get_trueup_exposure(ctx)
```

The route handler knows nothing about the service layer. If a service function
is renamed tomorrow, the route handler does not change.

**What this means for testing processors:**

```python
# Test injects a hand-built context — zero service layer involvement
def make_test_context(**overrides) -> ProcessingContext:
    defaults = ProcessingContext(
        licenses=FIXTURE_LICENSES,
        entitlement=FIXTURE_ENTITLEMENT,
        active_contracts=FIXTURE_CONTRACTS,
        active_employees=FIXTURE_EMPLOYEES,
        exited_employees=FIXTURE_EXITED,
        future_hires=FIXTURE_HIRES,
        known_departments=["Engineering", "Sales"],
        known_job_levels=["L1","L2","L3","L4","L5","L6","L7"],
        audit_date="2026-05-01",
        active_vendors=["Atlassify", "Nexaflow", "Cloudora"],
        fetched_at="2026-05-01T00:00:00",
    )
    return dataclasses.replace(defaults, **overrides)

def test_trueup_exposure_nexaflow():
    ctx = make_test_context()
    result = get_trueup_exposure(ctx, vendor="Nexaflow")
    assert len(result) > 0
    assert result[0].vendor == "Nexaflow"
```

No database. No service calls. Processors are pure functions over injected data.

---

## Typed Output Schemas — `schemas/proc_results.py`

Phase 1B's `schemas/` package defined input shapes (employee, license, contract).
Phase 1C adds output shapes — the typed return types of every processor function.

**Why typed output instead of plain dicts:**
- The chatbot tool layer and API layer both consume processor output. Typed
  shapes make field names and types explicit — a missing field is a Python
  error at definition time, not a KeyError at runtime.
- When ML models produce `ForecastResult` objects in Phase 1D+, the typed
  schema pattern is already established. Adding a new output type is additive —
  it does not require changing existing processor return types.
- Tests become more readable — `result.exposure_seats` instead of
  `result["exposure_seats"]`.

**Implementation:** Use Python `dataclasses` for Phase 1C. Migrate to `pydantic`
if API validation becomes a requirement in Phase 1D.

**Example shapes (illustrative — full definitions go in the file):**

```python
from dataclasses import dataclass

@dataclass
class TrueUpResult:
    vendor: str
    sku: str
    seat_type: str
    effective_total_seats: int
    active_provisioned_seats: int
    exposure_seats: int
    shelfware_seats: int
    unit_price: float
    exposure_amount_monthly: float
    shelfware_amount_monthly: float
    exposure_amount_annual: float
    shelfware_amount_annual: float
    portfolio_ratio: float
    notice_deadline: str
    days_until_notice_deadline: int
    auto_renewal: bool
    true_down_rights: bool
    measurement_method: str
    renewal_urgency: str
    computed_at: str

@dataclass
class GhostSummaryResult:
    vendor: str
    ghost_license_count: int
    total_cost_at_risk_monthly: float
    total_cost_at_risk_annual: float
    avg_days_orphaned: float
    max_days_orphaned: int
    by_department: list[dict]
    computed_at: str

@dataclass
class RenewalPressureResult:
    vendor: str
    sku: str
    seat_type: str
    of_id: str
    contract_expiry: str
    notice_deadline: str
    days_until_notice_deadline: int
    renewal_urgency: str
    auto_renewal: bool
    true_down_rights: bool
    current_provisioned: int
    effective_total_seats: int
    exposure_seats: int
    hires_before_deadline: int
    hires_by_department: list[dict]
    urgency_score: float
    growth_score: float
    exposure_score: float
    pressure_score: float
    pressure_classification: str
    exit_model_applied: bool
    computed_at: str

# All other result types follow the same pattern.
# Full definitions in schemas/processing_results.py.
```

---

## `schemas/proc_forecast_results.py` — Phase 1D+ Stub

Define this file now as an empty module with a comment. When ML-based
time-series forecasting is built, its output types are added here — not in
`proc_results.py`. Keeping them separate makes it clear which outputs
are rule-based (processing layer) and which are model-based (ML layer).

```python
# schemas/proc_forecast_results.py
#
# Typed output shapes for ML-based forecast models.
# Populated in Phase 1D+ when time-series forecasting is introduced.
#
# Future types expected here:
#   ForecastResult      — time-series seat demand forecast per vendor+SKU
#   PressureScoreV2     — ML-enhanced renewal pressure with confidence interval
#   ChurnPrediction     — per-license churn probability from trained model
#
# Phase 1C rule: do not add anything to this file.
# Phase 1D rule: add new types here, not to proc_results.py.
```

---

## Versioning — Where It Applies in This Project

Data table versioning (`hr_headcount_v{N}`, `license_utilization_v{N}`) was
established in Phase 1A. Phase 1C introduces new entities that also require
versioning. Here is the complete versioning map across the project:

| Entity | Versioning mechanism | Why |
|---|---|---|
| Raw data tables | `data_versions` SQLite table + `current_versions` promotion | Established Phase 1A. New CSV ingestion creates v{N+1}. |
| Service functions | `version` parameter passed through to table name resolution | Established Phase 1B. `None` resolves to current. |
| `ProcessingContext` | `version` parameter on `build_context()` passed to all service calls | New Phase 1C. Same pattern as services. |
| Processor output schemas | `schemas/processing_results.py` dataclass definitions | Versioned by Python class name if breaking changes needed — e.g. `TrueUpResultV2`. Non-breaking field additions are additive. |
| ML model outputs | `schemas/forecast_results.py` — separate file | Phase 1D+. Model version carried as a field (`model_version: str`) inside each result object. Old results remain in `ml_forecasts` table with their model version. |
| Chatbot tool definitions | Tool schema versioned in Phase 1D | A tool parameter change is a breaking change for the chatbot. Tool names should be stable. |
| API endpoints | URL versioned — `/api/v1/` prefix | Phase 1D. `/v2/` introduced only for breaking changes to response shape. |

**Rule for processor output schema changes:**
- Adding a new field to a result dataclass → additive, no version bump needed.
- Renaming or removing a field → breaking change. Create `TrueUpResultV2`,
  keep `TrueUpResult` until all consumers are migrated. Never silently change
  a field's meaning.

**Rule for stored ML forecasts:**
Every row in the `ml_forecasts` table carries `model_version`. When
`forecast_store_service` reads back results, it returns the latest non-expired
result by default, or a specific model version if requested. Consumers always
know which model version produced the answer.

---

## New Service File — `services/forecast_store_service.py` (Stub)

When ML forecasts are computed and stored, a new service file reads them back.
Define the stub now so Phase 1D has a clear landing zone.

```python
# services/forecast_store_service.py
#
# Reads stored ML forecast results from the ml_forecasts table.
# This file is the ONLY consumer of the ml_forecasts table.
# It follows the same patterns as all other service files:
#   - Returns plain dicts (until schemas/forecast_results.py types are stable)
#   - Never imports from processing/ or db/ directly
#   - Version parameter resolves to latest non-expired result by default
#
# Phase 1C rule: do not implement anything in this file.
# Phase 1D rule: implement get_forecast_results() and get_latest_forecast() here.

def get_forecast_results(
    vendor: str | None = None,
    model_version: str | None = None,
    version: str | None = None,
) -> list[dict]:
    raise NotImplementedError("forecast_store_service not implemented until Phase 1D")
```

**Why a separate service file and not an addition to existing service files:**
Stored ML forecasts are a different data source from raw ingested data. Adding
reads from `ml_forecasts` to `license_service.py` would give that file two
jobs — reading raw license utilization data AND reading computed model outputs.
One source table family per service file. This rule does not change.

---

## Processors

---

### 1. `processing/trueup_processor.py`

**Purpose:** Compute true-up exposure and shelfware at the
`vendor + SKU + seat_type` grain. This is Table 4 described in the base layer
README. The primary output that procurement acts on.

**Chatbot questions answered:**
- "What is our true-up exposure for Nexaflow?"
- "Which vendor has the highest shelfware?"
- "Are we over or under our Atlassify entitlement?"
- "What is our total annual true-up liability?"

**Context fields used:**

```python
ctx.licenses          # filtered to status_filter=["active", "over_tier"] inline
ctx.entitlement       # deduplicated at vendor+sku+seat_type grain
ctx.active_vendors    # for vendor filtering
ctx.audit_date        # for days_until_notice_deadline computation
```

**Logic:**

1. Filter `ctx.licenses` to `status in ["active", "over_tier"]` — billable
   provisioned seats.
2. Filter `ctx.entitlement` to the requested vendor(s). `effective_total_seats`
   is the contracted ceiling.
3. Group provisioned rows by `vendor + sku + seat_type`. Count = provisioned seats.
4. Full outer join entitlement against provisioned on `vendor + sku + seat_type`.
5. Compute per row:
   - `exposure_seats = max(0, provisioned - entitlement)`
   - `shelfware_seats = max(0, entitlement - provisioned)`
   - `exposure_amount_monthly = exposure_seats × unit_price`
   - `shelfware_amount_monthly = shelfware_seats × unit_price`
   - `exposure_amount_annual = exposure_amount_monthly × 12`
   - `shelfware_amount_annual = shelfware_amount_monthly × 12`
   - `portfolio_ratio = provisioned / entitlement` (null-safe — 0 if entitlement is 0)
   - `days_until_notice_deadline = notice_deadline − ctx.audit_date`

**Public function:**

```python
def get_trueup_exposure(
    ctx: ProcessingContext,
    vendor: str | None = None,
) -> list[TrueUpResult]:
    """
    Returns true-up exposure and shelfware per vendor+SKU+seat_type.
    Filters to ctx.active_vendors by default.
    Optional vendor filter narrows to a single vendor.
    """
```

**Return shape (single row):**

```python
{
    "vendor": "Nexaflow",
    "sku": "Flow Automation",
    "seat_type": "Contributor",
    "effective_total_seats": 420,
    "active_provisioned_seats": 467,
    "exposure_seats": 47,
    "shelfware_seats": 0,
    "unit_price": 14.50,
    "exposure_amount_monthly": 681.50,
    "shelfware_amount_monthly": 0.0,
    "exposure_amount_annual": 8178.0,
    "shelfware_amount_annual": 0.0,
    "portfolio_ratio": 1.112,
    "notice_deadline": "2026-08-15",
    "days_until_notice_deadline": 106,
    "auto_renewal": True,
    "true_down_rights": False,
    "measurement_method": "peak",
    "renewal_urgency": "ok",
    "computed_at": "2026-05-12T10:30:00"
}
```

**Validation targets (from base layer README):**

| Vendor | Expected Annual Exposure | Expected Annual Shelfware |
|---|---|---|
| Nexaflow | $95,258 | $56,094 |
| Cloudora | $81,899 | $19,065 |
| Atlassify | $39,027 | $9,463 |
| **Total exposure** | **$347,647** | |
| **Total shelfware** | **$211,171** | |

These figures are the pass criteria for integration tests. If totals deviate
from these numbers the processor has a logic error — not a data issue.

---

### 2. `processing/breakdown_enricher.py`

**Purpose:** Answer the "who is causing this?" question that the base
`trueup_processor` cannot. Takes a `vendor + SKU + seat_type` combination
that has exposure and breaks it down by department and job level. This is a
second-pass enrichment, not a standalone processor — it always follows a
`get_trueup_exposure()` call.

**Chatbot questions answered:**
- "Which department is driving my Nexaflow true-ups?"
- "Which job level is causing Atlassify over-provisioning?"
- "Is it Engineering L4s or L5s pushing us over on Cloudora?"
- "Break down who is over their Nexaflow entitlement by team"

**Context fields used:**

```python
ctx.licenses          # filtered to ["active", "over_tier"] for the given vendor inline
ctx.entitlement       # for effective_total_seats lookup
ctx.audit_date        # carried into computed_at
```

**Logic:**

1. Filter `ctx.licenses` to `status in ["active", "over_tier"]` and to the
   given `vendor + sku + seat_type`.
2. Group by `department` then by `job_level` within each department.
3. Count provisioned seats per group.
4. Get `effective_total_seats` from `ctx.entitlement` for proportional
   attribution:
   `dept_exposure_share = dept_provisioned / total_provisioned × total_exposure_seats`
5. Emit one row per `department + job_level` combination with at least one
   provisioned seat.

**Public function:**

```python
def get_trueup_breakdown(
    ctx: ProcessingContext,
    vendor: str,
    sku: str,
    seat_type: str,
) -> TrueUpBreakdownResult:
    """
    Returns department and job-level breakdown of provisioned seats for a
    given vendor+SKU+seat_type. Always call get_trueup_exposure() first to
    confirm there is exposure before calling this function.
    """
```

**Return shape:**

```python
{
    "vendor": "Nexaflow",
    "sku": "Flow Automation",
    "seat_type": "Contributor",
    "total_provisioned": 467,
    "effective_total_seats": 420,
    "exposure_seats": 47,
    "by_department": [
        {
            "department": "Engineering",
            "provisioned": 198,
            "exposure_share": 19.9,
            "by_job_level": [
                {"job_level": "L4", "provisioned": 87},
                {"job_level": "L5", "provisioned": 63},
                {"job_level": "L3", "provisioned": 48}
            ]
        },
        {
            "department": "Sales",
            "provisioned": 142,
            "exposure_share": 14.3,
            "by_job_level": [
                {"job_level": "L3", "provisioned": 78},
                {"job_level": "L4", "provisioned": 64}
            ]
        }
    ],
    "computed_at": "2026-05-12T10:30:00"
}
```

**Design note:** `by_department` is sorted by `provisioned` descending so the
chatbot can immediately surface the top offender. `by_job_level` within each
department is also sorted descending. The chatbot should always present the top
department first, not alphabetically.

---

### 3. `processing/ghost_detector.py`

**Purpose:** Identify licenses held by exited employees that were never
deprovisioned. Computes the cost the company is paying for zero-utility seats
and how long each has been orphaned since the employee exited.

**Chatbot questions answered:**
- "How many ghost licenses do we have for Atlassify?"
- "What is our total ghost license cost?"
- "Which exited employees still have active Nexaflow licenses?"
- "How long have these ghost licenses been sitting since the person left?"

**Context fields used:**

```python
ctx.licenses          # filtered to ["ghost"] inline
ctx.exited_employees  # for exit context enrichment — join on employee_id
ctx.audit_date        # for days_orphaned computation
ctx.active_vendors    # for vendor filtering
```

**Logic:**

1. Filter `ctx.licenses` to `status = "ghost"`.
2. Build a lookup dict from `ctx.exited_employees` keyed on `employee_id`.
3. For each ghost license, join against the lookup to get exit context:
   - `days_orphaned = ctx.audit_date − exit_date`
   - `total_cost_at_risk_monthly = sum of cost_at_risk` per ghost record
4. Aggregate to vendor-level summary. Also retain flat row-level list for
   detailed queries.

**Important:** `ctx.exited_employees` was fetched via `get_exited_employees()`
which uses `employee_status = 'exited'` — pre-hire rows are already excluded.
Do not re-derive this filter inside the processor.

**Public functions:**

```python
def get_ghost_summary(
    ctx: ProcessingContext,
    vendor: str | None = None,
) -> list[GhostSummaryResult]:
    """
    Returns ghost license summary per vendor. One row per vendor.
    Optional vendor filter narrows to single vendor.
    """

def get_ghost_detail(
    ctx: ProcessingContext,
    vendor: str | None = None,
    department: str | None = None,
) -> list[GhostDetailResult]:
    """
    Returns flat row-level ghost license list enriched with exit context.
    Supports vendor and department filters.
    Ordered by cost_at_risk descending.
    """
```

**Return shape — `get_ghost_summary()` (single row):**

```python
{
    "vendor": "Atlassify",
    "ghost_license_count": 1817,
    "total_cost_at_risk_monthly": 4230.50,
    "total_cost_at_risk_annual": 50766.0,
    "avg_days_orphaned": 312.4,
    "max_days_orphaned": 1847,
    "by_department": [
        {"department": "Engineering", "ghost_count": 642, "monthly_cost": 1490.20},
        {"department": "Sales", "ghost_count": 431, "monthly_cost": 1002.80}
    ],
    "computed_at": "2026-05-12T10:30:00"
}
```

**Return shape — `get_ghost_detail()` (single row):**

```python
{
    "license_id": "LIC-0004821",
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "employee_id": "EMP-03847",
    "email": "former.employee@company.com",
    "department": "Engineering",
    "job_level": "L4",
    "exit_date": "2024-11-15",
    "exit_type": "voluntary",
    "days_orphaned": 167,
    "monthly_cost": 12.50,
    "cost_at_risk": 12.50,
    "computed_at": "2026-05-12T10:30:00"
}
```

**Validation target:** Total ghost count across all vendors = 6,828.
Top vendor by ghost count: Veloxa (1,948), Atlassify (1,817).

---

### 4. `processing/reclamation_detector.py`

**Purpose:** Rank active licenses by reclamation value — identifying which
seats should be taken back based on usage pattern, days inactive, seat tier
mismatch, and cost. Ghost licenses are always reclamation candidates. Active
licenses are scored based on usage evidence.

**Chatbot questions answered:**
- "Which Atlassify licenses should we reclaim first?"
- "How much could we save by reclaiming underused Nexaflow seats?"
- "Which Engineering licenses are candidates for reclamation?"
- "Show me the highest-value licenses we're not actually using"

**Context fields used:**

```python
ctx.licenses          # filtered to ["active", "over_tier", "ghost"] inline
ctx.active_vendors    # for vendor filtering
ctx.audit_date        # carried into computed_at
```

**Logic:**

1. Filter `ctx.licenses` to `status in ["active", "over_tier", "ghost"]`.
2. For each row compute a `reclamation_score` (0.0–1.0):
   - `usage_tier = 'dormant'` or `'inactive'` → base score 0.7
   - `days_since_last_active > 60` → add 0.15
   - `seat_tier_match = 'over_tier'` → add 0.10
   - `reclamation_candidate = True` (pre-computed flag) → add 0.05
   - `license_status = 'ghost'` → score = 1.0 (always highest priority)
   - Cap at 1.0
3. Filter to rows where `reclamation_score >= min_score`.
4. Sort by `reclamation_score` descending, then `monthly_cost` descending
   within same score.

**Note on pre-computed `reclamation_candidate` flag:** The dataset carries
this column. Treat it as one input signal worth 0.05 weight — not as the
verdict. The processing layer owns the reclamation decision.

**Public function:**

```python
def get_reclamation_candidates(
    ctx: ProcessingContext,
    vendor: str | None = None,
    department: str | None = None,
    min_score: float = 0.7,
) -> list[ReclamationResult]:
    """
    Returns ranked reclamation candidates.
    Filters to ctx.active_vendors by default.
    Optional vendor and department filters.
    min_score defaults to 0.7 — raise to tighten, lower to widen.
    """
```

**Return shape (single row):**

```python
{
    "license_id": "LIC-0009432",
    "vendor": "Nexaflow",
    "sku": "Analytics Engine",
    "seat_type": "Full",
    "employee_id": "EMP-02841",
    "email": "inactive.user@company.com",
    "department": "Marketing",
    "job_level": "L2",
    "license_status": "active",
    "usage_tier": "dormant",
    "days_since_last_active": 94.0,
    "seat_tier_match": "over_tier",
    "monthly_cost": 18.00,
    "annual_cost": 216.0,
    "reclamation_score": 1.0,
    "reclamation_candidate_flag": True,
    "computed_at": "2026-05-12T10:30:00"
}
```

**Validation target:** Dataset documents 6,884 reclamation candidates
(24.9% of licenses). Tests should confirm count is in the 6,500–7,200 range
(±5% tolerance) since our scoring may differ slightly from the pre-computed
flag.

---

### 5. `processing/utilization_aggregator.py`

**Purpose:** Roll up raw license rows into usage summaries by vendor, SKU,
and seat type. Answers the utilisation picture questions — how many seats are
actually being used and at what engagement level.

**Chatbot questions answered:**
- "What percentage of our Atlassify licenses are actively used?"
- "How many Nexaflow seats are dormant?"
- "Show me the utilisation breakdown for Cloudora"
- "Which vendor has the worst utilisation rate?"

**Context fields used:**

```python
ctx.licenses          # all statuses — no filter applied
ctx.active_vendors    # for vendor filtering
```

**Logic:**

1. Filter `ctx.licenses` to `ctx.active_vendors` (or the requested single
   vendor). No status filter — all licenses included.
2. Group by `vendor + sku + seat_type`.
3. For each group count per `usage_tier`:
   `power`, `moderate`, `underutilized`, `dormant`, `inactive`.
4. Compute:
   - `active_rate = (power + moderate) / total_licenses`
   - `waste_rate = (dormant + inactive) / total_licenses`
   - `total_monthly_cost = sum(monthly_cost)` for the group

**Public function:**

```python
def get_utilization_summary(
    ctx: ProcessingContext,
    vendor: str | None = None,
) -> list[UtilizationResult]:
    """
    Returns utilisation summary per vendor+SKU+seat_type.
    Optional vendor filter.
    All five usage tiers always present in output even if count is zero.
    """
```

**Return shape (single row):**

```python
{
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "total_licenses": 1240,
    "by_usage_tier": {
        "power": 498,
        "moderate": 374,
        "underutilized": 187,
        "dormant": 94,
        "inactive": 87
    },
    "active_rate": 0.703,
    "waste_rate": 0.146,
    "total_monthly_cost": 15500.0,
    "computed_at": "2026-05-12T10:30:00"
}
```

**Validation target:** Portfolio-level `active_rate` should resolve to ~55.0%
(matching Zylo 2026 benchmark cited in base layer README). If the computed
portfolio average deviates more than 2 percentage points, investigate before
proceeding.

---

### 6. `processing/license_demand_forecaster.py`

**Purpose:** Project how many new licenses will be needed per vendor and SKU
for the forward hire window (next quarter). Uses the pre-hire pipeline from
`employee_service.get_future_hires()` and derives expected license need by
applying provisioning rate patterns from existing active employees.

**Chatbot questions answered:**
- "What licenses will we need for next quarter's Atlassify renewal?"
- "How many Nexaflow seats should we add for incoming Engineering hires?"
- "What is the expected license demand for Q3 hires?"
- "Which department's hires will require the most new licenses?"

**Context fields used:**

```python
ctx.future_hires        # 180 pre-hire rows — grouped by department + job_level
ctx.licenses            # filtered to ["active", "over_tier"] inline
ctx.active_employees    # for provisioning rate denominator
ctx.active_vendors      # for vendor filtering
ctx.audit_date          # for hire_window_start
```

**Logic:**

1. Filter `ctx.future_hires` by `before_date` and `department` if provided.
   Group by `department + job_level`.
2. Filter `ctx.licenses` to `status in ["active", "over_tier"]`.
3. For each `vendor + sku + seat_type + department + job_level` combination,
   compute the **provisioning rate**:
   `provisioning_rate = active_provisioned_seats / active_employee_count`
   where both counts are scoped to the same `department + job_level` cohort
   from `ctx.active_employees`.
4. Apply rate to incoming pre-hire counts:
   `expected_new_licenses = pre_hire_count × provisioning_rate`
5. Round to nearest integer. Flag `low_confidence: True` where
   `provisioning_rate` is based on fewer than 5 active employees.

**Important caveat — no exit model:** This forecaster projects new demand only.
It does not model expected exits reducing demand. Include
`exit_model_applied: False` in every output row. The chatbot must surface this
caveat whenever presenting demand forecasts.

**Public function:**

```python
def get_license_demand_forecast(
    ctx: ProcessingContext,
    vendor: str | None = None,
    department: str | None = None,
    before_date: str | None = None,
) -> list[DemandForecastResult]:
    """
    Returns projected new license demand per vendor+SKU+seat_type.
    Optional vendor, department, and before_date filters.
    before_date narrows the hire window used from ctx.future_hires.
    exit_model_applied is always False in this version.
    """
```

**Return shape (single row):**

```python
{
    "vendor": "Atlassify",
    "sku": "Project Suite",
    "seat_type": "Full",
    "department": "Engineering",
    "incoming_hires": 54,
    "provisioning_rate": 0.68,
    "expected_new_licenses": 37,
    "low_confidence": False,
    "exit_model_applied": False,
    "hire_window_start": "2026-05-02",
    "hire_window_end": "2026-07-31",
    "computed_at": "2026-05-12T10:30:00"
}
```

**Chatbot note — how to answer the quarterly license question:**
When the chatbot calls this tool for "What licenses will I need for next
quarter for Atlassify?", it should sum `expected_new_licenses` across all
departments for each `sku + seat_type`, then present as:
"Based on 180 incoming hires and current provisioning patterns, you will likely
need approximately N new Atlassify Project Suite Full seats before July 31.
Note: this forecast does not account for expected exits."

---

### 7. `processing/renewal_pressure_forecaster.py`

**Purpose:** Score each active vendor contract by renewal pressure — combining
hire pipeline growth, true-up exposure, contract urgency, and expired contract
status. This is the highest-value processor for procurement decisions.

**Chatbot questions answered:**
- "Which vendor renewals are most urgent right now?"
- "Will Nexaflow's headcount grow before their notice deadline?"
- "What is the renewal pressure score for Cloudora?"
- "Which contracts are expired and need immediate attention?"
- "How many Engineering hires are coming before the Atlassify deadline?"

**Context fields used:**

```python
ctx.active_contracts    # one row per active OF with notice deadline
ctx.future_hires        # full pre-hire pipeline
ctx.licenses            # filtered to ["active", "over_tier"] inline
ctx.entitlement         # for exposure_seats computation
ctx.audit_date          # for days_until_notice_deadline and urgency scoring
ctx.active_vendors      # for vendor filtering
```

**Logic:**

1. Filter `ctx.active_contracts` to `ctx.active_vendors` (or requested vendor).
2. For each contract's `notice_deadline`, count pre-hires from `ctx.future_hires`
   where `hire_date <= notice_deadline`, grouped by department:
   `hires_before_deadline = count(pre_hires where hire_date <= notice_deadline)`
3. Compute exposure inline from `ctx.licenses` and `ctx.entitlement` at
   `vendor + sku + seat_type` grain — same arithmetic as `trueup_processor`
   but derived independently. Processors do not call other processors.
4. Compute pressure score components:
   - `urgency_score`: based on `days_until_notice_deadline`
     - `expired` (`renewal_urgency = 'expired'`) → 1.0
     - `<= 30 days` → 0.9
     - `<= 60 days` → 0.7
     - `<= 90 days` → 0.5
     - `> 90 days` → 0.2
   - `growth_score`: based on `hires_before_deadline / current_provisioned`
     - `>= 0.10` (10%+ growth) → 0.4
     - `>= 0.05` → 0.2
     - `< 0.05` → 0.0
   - `exposure_score`:
     - Has `exposure_seats > 0` → 0.3
     - No exposure → 0.0
   - `pressure_score = urgency_score + growth_score + exposure_score` capped at 1.0
5. Classify:
   - `pressure_score >= 0.8` → `critical`
   - `pressure_score >= 0.5` → `at-risk`
   - `pressure_score < 0.5` → `ok`

**Public function:**

```python
def get_renewal_pressure(
    ctx: ProcessingContext,
    vendor: str | None = None,
) -> list[RenewalPressureResult]:
    """
    Returns renewal pressure score per active contract.
    Sorted by pressure_score descending — highest risk first.
    Optional vendor filter.
    """
```

**Return shape (single row):**

```python
{
    "vendor": "Nexaflow",
    "sku": "Flow Automation",
    "seat_type": "Contributor",
    "of_id": "V4-OF-012",
    "contract_expiry": "2026-09-01",
    "notice_deadline": "2026-08-15",
    "days_until_notice_deadline": 106,
    "renewal_urgency": "ok",
    "auto_renewal": True,
    "true_down_rights": False,
    "current_provisioned": 467,
    "effective_total_seats": 420,
    "exposure_seats": 47,
    "hires_before_deadline": 38,
    "hires_by_department": [
        {"department": "Engineering", "count": 24},
        {"department": "Sales", "count": 14}
    ],
    "urgency_score": 0.2,
    "growth_score": 0.4,
    "exposure_score": 0.3,
    "pressure_score": 0.9,
    "pressure_classification": "critical",
    "exit_model_applied": False,
    "computed_at": "2026-05-12T10:30:00"
}
```

**Validation target:** Nexaflow and Cloudora have `renewal_urgency = 'expired'`
on 479 licenses (261 + 218). These contracts must appear as `critical` in the
pressure output regardless of growth or exposure scores, because `expired`
forces `urgency_score = 1.0`.

---

## Processor Dependency Map

```
trueup_processor            → contract_service, license_service
breakdown_enricher          → license_service, contract_service
ghost_detector              → license_service, employee_service
reclamation_detector        → license_service, employee_service
utilization_aggregator      → license_service
license_demand_forecaster   → employee_service, license_service
renewal_pressure_forecaster → contract_service, employee_service, license_service
```

**Processors never call other processors.** If two processors need the same
derived figure (e.g. exposure_seats in both trueup_processor and
renewal_pressure_forecaster), they each derive it independently from the same
service calls. This keeps every processor independently runnable and
independently testable.

---

## Chatbot Tool Surface

Each processor function maps to one chatbot tool. The tool name, description,
and parameter schema are defined in Phase 1D when the chatbot is wired up.
What matters in Phase 1C is that every function has:

- A clean, unambiguous name
- Parameters that map directly to what a user might specify
  (`vendor`, `department`, `before_date`, `min_score`)
- A consistent `computed_at` timestamp in every output row
- A consistent `exit_model_applied` flag on any forward-looking output

The chatbot will call multiple tools to answer compound questions. The tool
call sequence for "Which department is firing up my Nexaflow true-ups?" is:

```
1. get_trueup_exposure(vendor="Nexaflow")
   → identifies which SKU+seat_type has exposure

2. get_trueup_breakdown(vendor="Nexaflow", sku="Flow Automation", seat_type="Contributor")
   → surfaces Engineering as the dominant department
```

The tool call sequence for "What licenses will I need next quarter for Atlassify?" is:

```
1. get_license_demand_forecast(vendor="Atlassify")
   → projected new seats per SKU+seat_type across all departments

2. get_trueup_exposure(vendor="Atlassify")
   → existing headroom or deficit that affects net new requirement
```

These sequences must work correctly before Phase 1D begins.

---

## `processing_main.py` — Manual Runner

Mirrors `services_main.py` exactly in structure. Accepts `--vendor`,
`--json`, `--full` flags. Runs all seven processors in dependency order and
prints summaries. Used for manual verification, not production execution.

```
py -3 processing_main.py
py -3 processing_main.py --vendor Nexaflow
py -3 processing_main.py --json
```

---

## `processing_smoke_test.py` — Smoke Test

Mirrors `services_smoke_test.py`. Calls each public processor function once
with no filters and asserts:

- Return is a non-empty list
- Every row contains `computed_at`
- No exceptions raised

Run before every Phase 1D session to confirm the processing layer is healthy.

```
py -3 processing_smoke_test.py
```

---

## Test Suite

### Naming convention

All processing layer test files use the `test_proc_` prefix.
All service layer test files use the `test_svc_` prefix.
This makes layer ownership immediately visible in any file listing without
opening a file.

One test file per processor. One `test_proc_integration.py` for
cross-processor flows.

### Coverage requirements

Every public function must have tests for:

| Test type | What to assert |
|---|---|
| Happy path, no filter | Returns non-empty list, correct keys present |
| Vendor filter | Returns only rows for that vendor |
| Computed fields correct | Spot-check one row's arithmetic manually |
| `computed_at` present | Every row in every result has this key |
| Validation target | Aggregate totals match base layer README figures (within 1%) |
| Empty result | Passing a vendor not in ACTIVE_VENDORS returns empty list, does not raise |

### Integration tests — `test_proc_integration.py`

| Test | What to assert |
|---|---|
| `test_trueup_then_breakdown_nexaflow` | Breakdown department list is non-empty for the SKU with highest Nexaflow exposure |
| `test_demand_forecast_uses_prehire_pipeline` | Forecast returns non-zero expected_new_licenses for at least one vendor |
| `test_renewal_pressure_expired_contracts_critical` | All Nexaflow and Cloudora expired contracts score `critical` |
| `test_ghost_detector_excludes_prehire` | No pre-hire employee_id appears in ghost detail results |
| `test_ghost_total_matches_readme` | Sum of ghost_license_count across all vendors = 6,828 |
| `test_trueup_total_exposure_matches_readme` | Sum of exposure_amount_annual = $347,647 (±1%) |
| `test_trueup_total_shelfware_matches_readme` | Sum of shelfware_amount_annual = $211,171 (±1%) |

---

## Build Order

Follow this sequence. Each step has a test gate before moving to the next.

1. `processing/__init__.py` — empty, mirrors services pattern
2. `schemas/proc_results.py` + `schemas/proc_forecast_results.py` (stub)
   → Gate: all result dataclasses import cleanly, no circular imports
3. `processing/context_builder.py` + `test_proc_context_builder.py`
   → Gate: `build_context()` returns a fully populated `ProcessingContext`
4. `processing/trueup_processor.py` + `test_proc_trueup.py`
   → Gate: annual exposure and shelfware totals match README figures
5. `processing/breakdown_enricher.py` + `test_proc_breakdown.py`
   → Gate: `by_department` non-empty for any vendor with exposure > 0
6. `processing/ghost_detector.py` + `test_proc_ghost.py`
   → Gate: total ghost count = 6,828 across all vendors
7. `processing/reclamation_detector.py` + `test_proc_reclamation.py`
   → Gate: candidate count in 6,500–7,200 range
8. `processing/utilization_aggregator.py` + `test_proc_utilization.py`
   → Gate: portfolio active_rate resolves to ~55.0%
9. `processing/license_demand_forecaster.py` + `test_proc_demand_forecast.py`
   → Gate: forecast returns non-zero demand for at least one vendor+SKU+dept
10. `processing/renewal_pressure_forecaster.py` + `test_proc_renewal_pressure.py`
    → Gate: expired Nexaflow and Cloudora contracts classified as `critical`
11. `test_proc_integration.py` — all cross-processor tests
12. `processing_smoke_test.py` + `processing_main.py`

Do not begin step N+1 until step N's gate passes.

---

## What Does Not Change

- `db/` — no changes
- `services/` — no changes
- `schemas/__init__.py` — no changes
- `schemas/svc_vendor_contract.py`, `schemas/svc_employee.py`,
  `schemas/svc_license_record.py` — logic unchanged, files renamed from
  Phase 1B names. Update imports in service files accordingly.
- `config/vendor_rules.py` — no changes
- Phase 1A and 1B logic — untouched

---

## What Is Deferred to Phase 1D

| Feature | Reason |
|---|---|
| Chatbot tool definitions and parameter schemas | Processing layer must be stable first |
| API endpoint wiring | Depends on processing layer |
| Dashboard views | Depends on processing layer |
| Exit model for demand forecasting | Requires planned exit date data not in current HR model |
| Vendor-level optimization recommendations | Phase 1D signal interpretation layer |
| Negative amendment / seat reduction scenarios | V2 contract data feature |

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| v1 | 2026-05-13 | Initial spec. Seven processors defined. Breakdown enricher and license demand forecaster added. Chatbot tool sequences documented. Build order with test gates defined. |
| v2 (this file) | 2026-05-13 | `ProcessingContext` + `context_builder.py` facade pattern introduced — processors no longer import from services directly. All processor signatures updated to accept `ctx: ProcessingContext`. Typed output schemas added (`schemas/proc_results.py`, `schemas/proc_forecast_results.py` stub). `services/forecast_store_service.py` stub defined. Full versioning map added. File naming convention introduced: `svc_` prefix for service layer schemas and tests, `proc_` prefix for processing layer schemas and tests. Build order updated — schemas and context_builder build before processors. |

---

*Phase 1C Processing Layer v2 · Audit Date: 2026-05-01 · Depends on: Phase 1B
service layer (101 tests passing) · Seven processors · Facade pattern via
context_builder.py · No processor imports services directly · No direct db/
access · All outputs typed via schemas/proc_results.py · test_svc_* /
test_proc_* naming enforced*
