# Phase 2A/1F Code Implemented

**Project:** SaaS Spend Management Platform  
**Phase:** 2A — Trial Run Orchestration & 1F — Pipeline Control Panel  
**Status:** **STABILIZED** with Persistence & Resilient Context

## What We Implemented and Why

### 1. Ingestion Trial Mode (`services/ingestion_service.py`)
- **What:** Standardized `vendor_profiles` and `data_versions` schemas.
- **Why:** Fixed `OperationalError` by aligning the database columns (`table_name`, `ingested_at`) across the service and database layers.

### 2. Resilient Processing Context (`processing/context_builder.py`)
- **What:** Modified `_build_fresh_context` to handle missing tables gracefully during initial ingestion.
- **Why:** Prevents `DataNotReadyError` when performing the very first ingestion of a multi-table set. Secondary tables are treated as empty instead of crashing the trial.

### 3. Persistent Pipeline Runs (`api/pipeline_state.py`)
- **What:** Moved pipeline run status from in-memory to the `pipeline_runs` SQLite table.
- **Why:** Prevents `404 Not Found` errors when polling for status. The frontend can now pick up progress even if the backend process reloads or restarts.

### 4. Zombie Run Cleanup (`db/connection.py`)
- **What:** Automated cleanup of stuck "Running" states on server startup.
- **Why:** Prevents `409 Conflict` errors. Any run interrupted by a crash or restart is automatically failed, clearing the path for new trials.

### 5. Discovery & Baseline Management (`src/views/PipelineView.jsx`)
- **What:** A stunning, tabbed UI that separates Ingestion from Governance.
    - **Discovery Tab:** Visual comparison of current metrics vs. established baselines.
    - **Establish Baseline:** One-click "Freeze" of current metrics as the new Ground Truth.

### 6. Calculation Accuracy Fixes
- **Ghost Licenses:** Fixed `processing/ghost_detector.py` to filter out `future_hires` in the summary view, ensuring consistency with the detailed breakdown.
- **True-up Exposure:** Fixed `services/contract_service.py` to use `MAX(of_id)` instead of `MIN(of_id)`. This ensures that expansion contracts (which increase the total seat limit) are prioritized, preventing over-reporting of true-up exposure costs.
- **Pipeline Vendor Detection:** Removed hardcoded "Atlassify" vendor tag in `pipeline/runner.py`. The pipeline now automatically detects the vendor name from the uploaded `vendor_overview` file, ensuring metadata in `data_versions` is accurate.
- **Dynamic Vendor Discovery:** Implemented logic to extract unique vendors from `vendor_overview` after promotion and automatically update the `.env` file and current process environment (`ACTIVE_VENDORS`).
- **Calibrated Validation:** Updated `pipeline/checks.py` and `pipeline/runner.py` to perform "calibrated" health checks. The pipeline now scans the pending data for vendors *before* running checks, ensuring that the validation logic only requires data for the vendors actually present in the current upload. This resolves "Catch-22" failures where stale environment settings blocked new uploads.
- **Zero-Restart Architecture:** Services and processing layers now resolve active vendors at runtime, allowing the dashboard to reflect newly discovered or removed vendors instantly without a server restart.

## File Index

| Area | Files |
|------|--------|
| **Backend Core** | `services/ingestion_service.py`, `db/connection.py` |
| **Pipeline Logic** | `pipeline/checks.py`, `pipeline/runner.py`, `processing/context_builder.py` |
| **API** | `api/pipeline_state.py`, `api/routers/pipeline.py`, `api/main.py` |
| **Frontend** | `frontend/src/views/PipelineView.jsx`, `frontend/src/components/pipeline/UploadZone.jsx`, `frontend/src/components/pipeline/StepCard.jsx` |

## Verification Workflow (Fresh Start)
1. **Upload**: Drop 3 CSVs into the Ingestion tab.
2. **Run**: Start the pipeline. (Resilient context ensures it passes even without existing data).
3. **Discover**: Switch to the Discovery tab.
4. **Establish**: Freeze the metrics.
5. **Stability**: Subsequent runs now have persistent state and baseline targets.

## Handover Notes
- **Schema Lock:** The database schemas are now locked to the `ingestion_service.py` format.
- **Persistence:** All pipeline runs are logged in `pipeline_runs`. This serves as a permanent audit trail of data ingestion attempts.
- **Lenient Checks:** Processing checks for empty result sets (e.g. 0 ghosts) are now allowed during trials to support partial data onboarding.
