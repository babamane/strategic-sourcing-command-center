# Phase 2A/1F — Pipeline Trial Runs & Control Panel

**Project:** SaaS Spend Management Platform  
**Phase:** 2A/1F — Combined Pipeline Orchestration + Frontend Control Panel  
**Status:** Specification — ready for implementation  
**Depends on:** Phase 1E complete · 171 tests passing · frontend build passing  
**Scope:** Pipeline trial run backend (2A) + pipeline API endpoints + frontend landing page (1F). Zero changes to existing dashboard views, existing API routes, or existing tests.

---

## Why These Two Phases Are Combined

Phase 2A (pipeline trial run orchestration) and Phase 1F (pipeline control panel) share a single seam: `pipeline.runner.run_trial()`. Phase 1F's `_execute_pipeline()` background worker calls `run_trial()` directly. Building both in the same implementation pass avoids the awkward intermediate state where the trial runner exists but has no UI trigger, and the UI exists but has no real runner behind it.

The build order remains sequential — all 2A steps gate the 1F steps that depend on them.

---

## Problem Statement

The current ingestion flow is a single-shot operation:

```
Drop CSV into data/uploads/ → python ingestion_main.py → version promoted to current
```

If any downstream layer breaks after ingestion (service, processing, API), the broken version is already promoted and live. There is no checkpoint, no rollback, and no structured report of what failed. There is also no UI path for a non-technical operator to upload files and trigger ingestion without touching the terminal.

This combined phase introduces:

1. A **trial run** mode that ingests pending, validates layer by layer, promotes only on full pass, and rolls back on any failure — with a structured report.
2. A **pipeline control panel** (landing page) that lets the operator drag-drop CSVs, trigger the pipeline, and watch step-by-step progress before entering the dashboard.

---

## Architecture

### Backend pipeline (2A)

The trial run sits between ingestion and promotion. The existing version-parameter chain (`build_context(version=N)` → service functions with `version=N` → `get_connection(table, version=N)`) already supports targeting an unpromoted version. Phase 2A uses this chain to run checks before calling `promote_version`.

```
CSV file
  │
  ▼
pipeline/runner.py  run_trial()
  │
  ├── Step 1: ingest_pending()         → ingestion_service (auto_promote=False)
  │           Returns: pending_version (e.g. 4)
  │
  ├── Step 2: check_ingestion()        → pipeline/checks.py
  │           Row count deviation · schema fingerprint · derived fields present
  │
  ├── Step 3: check_service_layer()    → pipeline/checks.py
  │           Service functions with version=pending_version
  │           Non-empty results · no DataNotReadyError · all ACTIVE_VENDORS present
  │
  ├── Step 4: check_processing_layer() → pipeline/checks.py
  │           build_context(version=pending_version) · all 7 processors run
  │           Annual exposure within ±10% of baseline
  │
  ├── Step 5: check_api_layer()        → pipeline/checks.py
  │           httpx calls with ?version=pending_version
  │           Skipped gracefully if API server not reachable
  │
  ├── [ALL PASS] → promote_version(table, pending_version)
  │                Mark data_versions row 'promoted'
  │                Emit TrialRunReport (all_passed=True, promoted=True)
  │
  └── [ANY FAIL] → rollback(table, pending_version)
                   DROP TABLE {table}_v{pending_version}
                   Mark data_versions row 'trial_failed'
                   Emit TrialRunReport (all_passed=False, rolled_back=True)
```

### Frontend pipeline (1F)

The frontend control panel sits at the app root. `App.jsx` gates on a Zustand boolean `enterDashboard`. When false, `PipelineView` is shown. When true, the existing dashboard renders.

```
App loads → GET /api/v1/pipeline/versions
  │
  ├── All 3 tables promoted? YES → versions strip + "Enter Dashboard →" button
  │                          NO  → upload-required state
  │
User drops CSVs → POST /api/v1/pipeline/upload (×1 per file)
User clicks "Run Pipeline" → POST /api/v1/pipeline/run → { run_id }
Frontend polls GET /api/v1/pipeline/status/{run_id} every 2s
  │
  ├── status="running"  → step cards animate in real time
  ├── status="complete" → invalidate all React Query caches
  │                       "Enter Dashboard →" + auto-redirect after 3s
  └── status="failed"   → failure detail on broken step card
                          "Fix and Re-run" resets to upload state
```

---

## Required Changes to Existing Code

### `services/ingestion_service.py` — add `auto_promote` flag

Add one parameter with a default that preserves all existing behavior. No existing callers change. No existing tests change.

```python
def ingest_csv(
    file_path: str,
    table_name: str,
    audit_date: str,
    auto_promote: bool = True,   # NEW — default True preserves existing behavior
) -> dict:
    """
    Ingests a CSV into a versioned table.
    If auto_promote=True (default): promotes immediately. Existing behavior unchanged.
    If auto_promote=False: writes table + data_versions row with status='pending'.
    Does NOT call promote_version. Caller is responsible for promotion or rollback.
    Returns: {
        "version": int,
        "table_name": str,
        "row_count": int,
        "schema_fingerprint": str,
        "promoted": bool,
    }
    """
```

New `data_versions.status` values (no schema migration needed — status is free-form text):

| Value | Meaning |
|---|---|
| `'pending'` | Ingested but not yet promoted; trial run in progress |
| `'trial_failed'` | Trial run failed; version was rolled back |

### `db/connection.py` — add `get_promoted_versions()`

Used by `GET /pipeline/versions` to tell the frontend whether existing data is present.

```python
def get_promoted_versions() -> dict:
    """
    Returns {table_name: {version, promoted_at, row_count}} for all tables
    with a promoted version in current_versions.
    Returns an empty dict if no versions are promoted yet.
    """
    conn = open_database_connection()
    try:
        rows = conn.execute(
            """
            SELECT cv.table_name, cv.version_id,
                   dv.uploaded_at, dv.row_count
            FROM current_versions cv
            JOIN data_versions dv
              ON dv.table_name = cv.table_name
             AND dv.version_id = cv.version_id
            """
        ).fetchall()
        return {
            r["table_name"]: {
                "version":     r["version_id"],
                "promoted_at": r["uploaded_at"],
                "row_count":   r["row_count"],
            }
            for r in rows
        }
    finally:
        conn.close()
```

---

## New Backend Files

### `pipeline/__init__.py`

Empty. Mirrors `processing/__init__.py` pattern.

---

### `pipeline/checks.py`

Layer-by-layer health checks. Each function returns a list of `CheckResult`.

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class CheckResult:
    layer:      str    # "ingestion" | "service" | "processing" | "api"
    check_name: str
    passed:     bool
    message:    str
    detail:     Any = None   # optional counts, diffs, etc.
```

#### `check_ingestion(table_name, pending_version, deviation_threshold) -> list[CheckResult]`

Reads the `data_versions` row for `(table_name, pending_version)`.

| Check | Pass condition |
|---|---|
| `row_count_deviation` | Deviation from previous version's row count ≤ `deviation_threshold` (env `ROW_COUNT_DEVIATION_THRESHOLD`, default 0.05). First ingestion always passes. |
| `schema_fingerprint_change` | Fingerprint diff emits a WARNING (passed=True, message explains change). Never fails — schema changes are valid. |
| `derived_fields_present` | Row count > 0 and `days_since_last_active` column present (for `license_utilization`). |

#### `check_service_layer(table_name, pending_version) -> list[CheckResult]`

Table-to-service routing:

| `table_name` | Functions called |
|---|---|
| `license_utilization` | `get_raw_licenses(version=pending_version)` |
| `vendor_overview` | `get_entitlement(version=pending_version)`, `get_active_contracts(version=pending_version)` |
| `hr_headcount` | `get_active_employees(version=pending_version)`, `get_exited_employees(version=pending_version)`, `get_future_hires(version=pending_version)` |

| Check | Pass condition |
|---|---|
| `service_returns_rows` | Each function returns a non-empty list. |
| `no_data_not_ready_error` | No `DataNotReadyError` raised. |
| `active_vendors_present` | For license/contract calls: at least one row per vendor in `ACTIVE_VENDORS`. |

#### `check_processing_layer(pending_version) -> list[CheckResult]`

```python
ctx = build_context(version=pending_version)
```

If only one table is being re-ingested, `build_context` resolves the other two to their current promoted versions automatically.

| Check | Pass condition |
|---|---|
| `context_builds` | `build_context()` completes without exception. |
| `trueup_runs` | `get_trueup_exposure(ctx)` non-empty, `computed_at` present on all rows. |
| `ghost_runs` | `get_ghost_summary(ctx)` non-empty. |
| `reclamation_runs` | `get_reclamation_candidates(ctx)` non-empty. |
| `utilization_runs` | `get_utilization_summary(ctx)` non-empty. |
| `demand_forecast_runs` | `get_license_demand_forecast(ctx)` non-empty. |
| `renewal_pressure_runs` | `get_renewal_pressure(ctx)` non-empty. |
| `validation_targets` | Annual exposure within ±10% of `TRUEUP_EXPOSURE_BASELINE_ANNUAL` from `.env`. Skipped (passes with notice) if env var absent. |

#### `check_api_layer(pending_version, base_url) -> list[CheckResult]`

Uses `httpx` (already in `requirements.txt`). If server unreachable, all checks are skipped with `passed=True, message="API server not reachable — skipped"`.

| Check | Pass condition |
|---|---|
| `health_ok` | `GET /health` → HTTP 200. |
| `trueup_responds` | `GET /trueup/exposure?version={v}` → HTTP 200, non-empty JSON list. |
| `ghost_responds` | `GET /ghost/summary?version={v}` → HTTP 200. |
| `forecast_responds` | `GET /forecast?version={v}` → HTTP 200. |

---

### `pipeline/runner.py`

The orchestrator.

```python
@dataclass
class TrialRunReport:
    table_name:      str
    pending_version: int | None      # None if ingestion itself failed
    all_passed:      bool
    promoted:        bool
    rolled_back:     bool
    checks:          list[CheckResult]
    started_at:      str             # ISO timestamp
    completed_at:    str
    failure_summary: str | None      # first failure message, or None

def run_trial(
    file_path:    str,
    table_name:   str,
    audit_date:   str | None = None,   # defaults to SAAS_SPEND_AUDIT_DATE from .env
    api_base_url: str | None = None,   # defaults to PIPELINE_API_BASE_URL from .env
    force_promote: bool = False,        # skip checks and promote anyway (escape hatch)
) -> TrialRunReport:
    """
    Full trial run for one CSV against one table.
    Returns a structured TrialRunReport regardless of pass/fail.
    Raises no exceptions — all failures are captured in the report.
    """

def rollback(table_name: str, pending_version: int) -> None:
    """
    1. DROP TABLE IF EXISTS {table_name}_v{pending_version}
    2. UPDATE data_versions SET status='trial_failed'
       WHERE table_name=? AND version_id=?
    Uses a raw sqlite3 connection. Does not call any service function.
    """
```

---

### `pipeline/report.py`

Terminal and JSON output.

```python
def print_report(report: TrialRunReport) -> None:
    """Prints a structured pass/fail summary to stdout."""

def write_report_json(report: TrialRunReport, output_path: str) -> None:
    """Writes the report as JSON to output_path."""
```

Terminal format (success):

```
========================================
 PIPELINE TRIAL RUN — license_utilization v4
 Started:   2026-05-15T10:30:00
 Completed: 2026-05-15T10:30:04
========================================

 INGESTION
  ✓ row_count_deviation       27,540 rows (+1.2% vs v3, threshold 5.0%)
  ✓ schema_fingerprint_change No change
  ✓ derived_fields_present    days_since_last_active present

 SERVICE LAYER
  ✓ service_returns_rows      license_service: 27,540 rows
  ✓ no_data_not_ready_error   OK
  ✓ active_vendors_present    Atlassify ✓  Nexaflow ✓  Cloudora ✓

 PROCESSING LAYER
  ✓ context_builds            ProcessingContext ready
  ✓ trueup_runs               27 rows, computed_at present
  ✓ ghost_runs                3 vendors, 6,828 ghost licenses
  ✓ reclamation_runs          6,884 candidates
  ✓ utilization_runs          9 vendor+SKU rows
  ✓ demand_forecast_runs      216 rows
  ✓ renewal_pressure_runs     27 rows
  ✓ validation_targets        Annual exposure $347,612 (baseline $347,647, Δ 0.01%)

 API LAYER
  ✓ health_ok                 HTTP 200
  ✓ trueup_responds           27 rows
  ✓ ghost_responds            3 vendors
  ✓ forecast_responds         216 rows

========================================
 RESULT:  ALL CHECKS PASSED
 ACTION:  license_utilization promoted to v4
========================================
```

Terminal format (failure):

```
 SERVICE LAYER
  ✗ active_vendors_present    Nexaflow: 0 rows — check ACTIVE_VENDORS in .env
                              and confirm vendor_overview CSV contains Nexaflow rows

========================================
 RESULT:  FAILED at service layer (check: active_vendors_present)
 ACTION:  license_utilization v4 ROLLED BACK — v3 remains current
========================================
```

---

### `pipeline_trial_run.py` — CLI entry point

Mirrors `ingestion_main.py` in structure.

```python
# Usage examples:
# py -3 pipeline_trial_run.py
#     → scans data/uploads/, runs trial for each CSV found
#
# py -3 pipeline_trial_run.py --file data/uploads/license_utilization_v4.csv --table license_utilization
#     → trial run for a single file
#
# py -3 pipeline_trial_run.py --json-report pipeline_report.json
#     → writes machine-readable report to file
#
# py -3 pipeline_trial_run.py --force-promote
#     → skips all checks and promotes (emergency escape hatch)
```

Table name detection: if `--table` is not provided, derive from filename stem using the same prefix-matching logic already in `ingestion_main.py`.

---

### `api/pipeline_state.py`

In-process run state store. Single-user local tool — in-memory is appropriate. No SQLite table needed for run state.

```python
@dataclass
class StepStatus:
    step:         str               # "ingestion" | "service" | "processing" | "promotion"
    label:        str               # "Ingestion" | "Service Layer" | etc.
    status:       str               # "pending" | "running" | "passed" | "failed" | "skipped"
    message:      str = ""
    started_at:   str | None = None
    completed_at: str | None = None
    checks:       list[dict] = field(default_factory=list)  # CheckResult dicts

@dataclass
class RunStatus:
    run_id:            str
    status:            str           # "running" | "complete" | "failed"
    current_step:      str
    steps:             list[StepStatus]
    started_at:        str
    completed_at:      str | None = None
    promoted_versions: dict | None = None   # {"license_utilization": 4, ...} on success
    failure_summary:   str | None = None

_runs: dict[str, RunStatus] = {}    # module-level; one run at a time

def create_run() -> RunStatus: ...
def get_run(run_id: str) -> RunStatus | None: ...
def get_latest_run() -> RunStatus | None: ...
```

---

### `api/routers/pipeline.py`

Four endpoints. All sit under `/api/v1/pipeline/`.

#### `POST /pipeline/upload`

Accepts a single CSV file, detects target table from filename prefix, writes to `UPLOADS_DIR`, overwrites any existing file with the same name.

Returns `{ filename, table, saved_path, size_bytes }`. Returns HTTP 400 if filename prefix is unrecognised.

#### `POST /pipeline/run`

Starts `_execute_pipeline(run_id)` in a background thread. Returns `{ run_id }` immediately. Returns HTTP 409 if a run is already active.

#### `GET /pipeline/status/{run_id}`

Polled every 2 seconds by the frontend. Returns `asdict(RunStatus)`. Returns HTTP 404 for unknown `run_id`.

#### `GET /pipeline/versions`

Returns `get_promoted_versions()` from `db/connection.py`. Called on `PipelineView` mount to check whether existing data is present.

#### `_execute_pipeline(run_id)` — background worker

Runs in a thread. Updates the shared `RunStatus` in-place so every poll sees the latest state. Calls `run_trial()` per table file found in `UPLOADS_DIR`. Maps `TrialRunReport` check layers (`ingestion`, `service`, `processing`) onto the four step cards. Promotion step is set to `passed` after all trial runs complete.

```
for each CSV in UPLOADS_DIR:
    _set_step("ingestion", "running")
    report = run_trial(file_path, table_name, audit_date)
    if not report.all_passed:
        _set_step("ingestion", "failed", ...)
        _set_step("service", "skipped")
        _set_step("processing", "skipped")
        _set_step("promotion", "skipped")
        run.status = "failed"
        return

    _set_step("ingestion", "passed", ingestion_checks)
    _set_step("service", "passed", service_checks)
    _set_step("processing", "passed", processing_checks)

_set_step("promotion", "passed", "All tables promoted. ...")
run.status = "complete"
run.promoted_versions = {...}
```

Any unhandled exception sets all in-progress steps to `failed` and `run.status = "failed"`.

---

## New Frontend Files

### `src/views/PipelineView.jsx`

Entry gate — not in Sidebar nav. Shown at app root when `enterDashboard` is false.

```
┌─────────────────────────────────────────────────────────┐
│  [Logo / Product name]                                  │
│  "Upload your audit data to begin"                      │
├─────────────────────────────────────────────────────────┤
│  [Data Versions strip — only shown if data exists]      │
│  Vendor Overview v3 · HR Headcount v2 · License Util v4 │
│  Last ingested: 2026-05-01          [Enter Dashboard →] │
├──────────────┬──────────────┬──────────────────────────-┤
│  UPLOAD ZONE │  UPLOAD ZONE │       UPLOAD ZONE         │
│  Vendor      │  HR          │   License Utilization     │
│  Overview    │  Headcount   │                           │
│  Drop CSV    │  Drop CSV    │   Drop CSV here           │
│  here        │  here        │   [No file]               │
│  [No file]   │  [No file]   │                           │
├──────────────┴──────────────┴───────────────────────────┤
│  [Run Pipeline]  ← disabled until ≥1 file uploaded      │
├─────────────────────────────────────────────────────────┤
│  PROGRESS (hidden until Run clicked)                    │
│  ○ Ingestion      pending                               │
│  ○ Service Layer  pending                               │
│  ○ Processing     pending                               │
│  ○ Promotion      pending                               │
└─────────────────────────────────────────────────────────┘
```

Polling logic: `setInterval` at 2000ms after `POST /pipeline/run` returns. On `status === "complete"`: `queryClient.invalidateQueries()` (full cache invalidation), then `setTimeout(() => setEnterDashboard(true), 3000)`. On `status === "failed"`: stop polling, show failure detail on broken step card + "Fix and Re-run" button that resets to upload state.

Data versions strip: fetched via `useQuery` on mount. Shown only if `Object.keys(versions).length > 0`. Includes `TABLE_LABELS` map for display names + "Enter Dashboard →" button that bypasses upload if data already exists.

Success state (when `runData?.status === "complete"`):
```
✓ Pipeline complete — dashboard is ready
Entering dashboard in 3 seconds…
[Enter Dashboard →]
```

---

### `src/components/pipeline/UploadZone.jsx`

One card per table. Accepts `.csv` files only. On drop or file-input change, calls `POST /api/v1/pipeline/upload` immediately.

Props: `{ tableLabel, tableKey, hint, onUploaded }`

States:

| State | Appearance |
|---|---|
| Empty | Dashed border, upload icon, hint text, "or click to browse" |
| Uploading | Spinner, "Uploading…" |
| Uploaded | Green checkmark, filename, file size, "×" to remove (clears local state only) |
| Error | Red border, API error message |

Drag-and-drop: native HTML5, no library. `onDrop` → `uploadFile(file)`.

---

### `src/components/pipeline/StepCard.jsx`

Props: `{ label, status, message, checks }`

Visual states:

| Status | Icon | Color |
|---|---|---|
| `pending` | ○ empty circle | `text-text-dim` |
| `running` | ⟳ spinning | `text-amber-400` |
| `passed` | ✓ | `text-emerald-400` |
| `failed` | ✗ | `text-red-400` |
| `skipped` | — | `text-text-dim` |

When `status === "passed"` or `"failed"` and `checks.length > 0`: render a `<details>` element below the step label. Summary: "Show checks (N)". Content: table of check name / status / message in `font-mono text-[11px]`.

---

## Modified Files

| File | Change |
|---|---|
| `services/ingestion_service.py` | Add `auto_promote=True` parameter |
| `db/connection.py` | Add `get_promoted_versions()` |
| `api/main.py` | `app.include_router(pipeline_router.router, prefix="/api/v1")` |
| `src/App.jsx` | Add `enterDashboard` gate — renders `PipelineView` when false, existing dashboard when true |
| `src/store/useAppStore.js` | Add `enterDashboard: false` and `setEnterDashboard: (v) => set({ enterDashboard: v })` |
| `src/components/layout/Sidebar.jsx` | Add "↑ Re-run pipeline" footer link that calls `setEnterDashboard(false)` |

---

## Tests

### `tests/test_pipeline_checks.py` (2A)

All monkeypatched — no live DB required.

| Test | Asserts |
|---|---|
| `test_row_count_within_threshold` | `check_ingestion()` passes when new count is within 5% of previous |
| `test_row_count_exceeds_threshold` | `check_ingestion()` fails when deviation >5% |
| `test_schema_fingerprint_change_is_warning_not_failure` | Fingerprint change → `passed=True`, message contains "SCHEMA CHANGE" |
| `test_service_check_passes_when_rows_returned` | `check_service_layer()` passes when mocked service returns rows |
| `test_service_check_fails_on_empty_results` | `check_service_layer()` fails when mocked service returns `[]` |
| `test_rollback_marks_data_versions_row` | `rollback()` sets `status='trial_failed'` on the correct row |
| `test_full_trial_run_promotes_on_all_pass` | `run_trial()` with all mocked checks passing → `report.promoted=True` |
| `test_full_trial_run_rolls_back_on_failure` | `run_trial()` with one check failing → `report.rolled_back=True`, `report.promoted=False` |

### `tests/test_api_pipeline.py` (1F)

| Test | Asserts |
|---|---|
| `test_upload_valid_file` | `POST /pipeline/upload` with valid license_utilization CSV → HTTP 200, `table` field correct |
| `test_upload_unknown_filename` | `POST /pipeline/upload` with `random_data.csv` → HTTP 400 |
| `test_versions_returns_dict` | `GET /pipeline/versions` → HTTP 200, dict with known keys |
| `test_run_returns_run_id` | `POST /pipeline/run` → HTTP 200, `run_id` is a valid UUID string |
| `test_status_returns_run` | `GET /pipeline/status/{run_id}` → HTTP 200, `status` field present |
| `test_status_404_unknown_run` | `GET /pipeline/status/nonexistent` → HTTP 404 |
| `test_double_run_rejected` | Second `POST /pipeline/run` while first is running → HTTP 409 |

---

## New Files Summary

```
pipeline/__init__.py
pipeline/checks.py
pipeline/runner.py
pipeline/report.py
pipeline_trial_run.py
api/pipeline_state.py
api/routers/pipeline.py
tests/test_pipeline_checks.py
tests/test_api_pipeline.py
src/views/PipelineView.jsx
src/components/pipeline/UploadZone.jsx
src/components/pipeline/StepCard.jsx
```

---

## `.env` Additions

```env
# Pipeline trial run settings (2A)
PIPELINE_API_BASE_URL=http://127.0.0.1:8010
TRUEUP_EXPOSURE_BASELINE_ANNUAL=347647
PIPELINE_REPORT_OUTPUT_PATH=pipeline_report.json
```

`TRUEUP_EXPOSURE_BASELINE_ANNUAL` is set once after the first successful trial run. If absent, the `validation_targets` check is skipped (passes with a notice). No new packages required — `httpx` is already present from Phase 1D.

---

## Build Order

All 2A backend steps must gate before 1F steps that depend on `run_trial()`.

| Step | Files | Gate |
|---|---|---|
| 1 | `services/ingestion_service.py` — add `auto_promote=True` | Existing 171 tests still pass. `ingest_csv(..., auto_promote=False)` writes table + data_versions row but does NOT update current_versions. |
| 2 | `db/connection.py` — add `get_promoted_versions()` | Returns non-empty dict when called against live DB with promoted versions. |
| 3 | `pipeline/__init__.py` | Imports cleanly. |
| 4 | `pipeline/checks.py` — `CheckResult` dataclass + `check_ingestion()` | Unit test: row count deviation passes and fails correctly. |
| 5 | `pipeline/checks.py` — `check_service_layer()` | Unit test: empty service result → failed CheckResult. |
| 6 | `pipeline/checks.py` — `check_processing_layer()` | Unit test: context builds against current version → all processor checks pass. |
| 7 | `pipeline/checks.py` — `check_api_layer()` | Unit test: unreachable server → all skipped with passed=True. |
| 8 | `pipeline/runner.py` — `TrialRunReport` + `run_trial()` + `rollback()` | Unit test: mock all checks → promote on pass, rollback on fail. |
| 9 | `pipeline/report.py` — `print_report()` + `write_report_json()` | Manual: output matches format above. |
| 10 | `pipeline_trial_run.py` | Manual: `py -3 pipeline_trial_run.py --file <csv> --table license_utilization` → full run against live DB, prints report. |
| 11 | `tests/test_pipeline_checks.py` | All 8 tests pass. Full suite still 171+ passed. |
| 12 | `api/pipeline_state.py` | `create_run()` returns a valid `RunStatus`; `get_run(run_id)` retrieves it. |
| 13 | `api/routers/pipeline.py` — `upload` + `versions` endpoints | `POST /pipeline/upload` saves file · `GET /pipeline/versions` returns current table versions. |
| 14 | `api/routers/pipeline.py` — `run` + `status` endpoints + `_execute_pipeline()` | `POST /pipeline/run` returns run_id · `GET /pipeline/status/{id}` returns step list. |
| 15 | `api/main.py` — register router | All `/api/v1/pipeline/*` routes return non-404. |
| 16 | `tests/test_api_pipeline.py` | All 7 tests pass. Full suite 171+ passed. |
| 17 | `src/store/useAppStore.js` — add `enterDashboard` | `useAppStore.getState().enterDashboard === false` in console. |
| 18 | `src/components/pipeline/StepCard.jsx` | Renders correctly for each status value in isolation. |
| 19 | `src/components/pipeline/UploadZone.jsx` | File drop → POST fires → card switches to uploaded state. |
| 20 | `src/views/PipelineView.jsx` — versions strip + upload zones | Versions strip appears when data exists · "Enter Dashboard" navigates to dashboard. |
| 21 | `src/views/PipelineView.jsx` — run button + polling | Clicking Run → step cards animate → complete triggers `invalidateQueries` + auto-redirect. |
| 22 | `src/App.jsx` — gate | App loads to PipelineView · "Enter Dashboard" shows full dashboard · "Re-run pipeline" returns to PipelineView. |
| 23 | `src/components/layout/Sidebar.jsx` — footer link | "Re-run pipeline" visible at bottom of sidebar · click returns to PipelineView. |
| 24 | Full integration pass | Drop 3 CSVs → Run Pipeline → all 4 step cards pass → auto-redirect → all dashboard views show fresh data. |

Do not begin step N+1 until step N's gate passes.

---

## What This Phase Does Not Change

- `db/schema.py` — no DDL changes
- `db/connection.py` — `promote_version()` unchanged; runner calls it directly. Only addition is `get_promoted_versions()`.
- `services/` — only `ingestion_service.py` changes (one new parameter, default preserves old behavior)
- `processing/` — untouched; checks call existing public functions
- All existing dashboard API routes — untouched; new routes sit under `/pipeline/` prefix
- All existing dashboard frontend views — untouched; `PipelineView` is a pre-gate, not a nav item
- All existing 171 tests — must remain passing after step 1

## What This Phase Does Not Include

| Item | Reason |
|---|---|
| Per-file upload progress bar | File sizes are small; instant upload is fine. `XMLHttpRequest` progress events add complexity for negligible benefit. |
| Persistent run history | Local tool; in-memory is sufficient. Add a `pipeline_runs` SQLite table in Phase 2B if needed. |
| Partial re-run (single table) | Uncommon; full 3-table run is the normal flow. Add `table_filter` param to `/run` in Phase 2B. |
| WebSocket / SSE | Polling at 2s was chosen. Upgrade path: replace `setInterval` with `EventSource`. |
| Auth gate on pipeline endpoints | Local tool assumption; add API key check if moved to a shared environment. |

---

## Operational Notes

### Running a trial alongside a live server

Steps 1–4 (ingestion, service, processing) run in-process. API checks (step 5) are skipped gracefully if the server is unreachable. The trial run does not require the API server to be up.

### Multi-table ingestion order

When re-ingesting all three tables, run trial runs in this order:

```
1. vendor_overview      (contract + entitlement source)
2. hr_headcount         (employee source)
3. license_utilization  (license source — depends on derived fields from the other two)
```

Each trial run is independent. If `vendor_overview` fails, stop and fix before running `hr_headcount`.

### First run baseline

On the first successful trial run after this phase is deployed, copy `TRUEUP_EXPOSURE_BASELINE_ANNUAL` from the processing check output into `.env`. From that point forward, `validation_targets` uses the live baseline.

### Manual commands

```powershell
# Backend
py -3 -m pytest tests/
py -3 -m uvicorn api.main:app --reload --port 8010
py -3 pipeline_trial_run.py --file data/uploads/license_utilization_v4.csv --table license_utilization
py -3 pipeline_trial_run.py --json-report pipeline_report.json

# Frontend
cd frontend
npm.cmd run dev
```

---

*Phase 2A/1F · Pipeline trial run orchestration (backend) + pipeline control panel (frontend)*  
*Adds `auto_promote` flag to ingestion · layer-by-layer checks · rollback · structured report · drag-drop upload UI · real-time step polling · React Query full invalidation on complete*  
*All existing behavior preserved — default `auto_promote=True` unchanged · 171+ tests must remain green after step 1*
