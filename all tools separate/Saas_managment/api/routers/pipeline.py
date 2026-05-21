"""Pipeline control panel API endpoints.

Four endpoints under /pipeline/:
- POST /pipeline/upload   — save CSV, detect table from filename
- POST /pipeline/run      — start background trial run
- GET  /pipeline/status/{run_id} — poll for step progress
- GET  /pipeline/versions  — return promoted table versions
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from api.pipeline_state import (
    RunStatus,
    StepStatus,
    create_run,
    get_run,
    update_run,
    is_any_run_active,
)
from db.connection import get_promoted_versions, get_uploads_dir

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Table name detection from filename prefix
TABLE_PREFIXES = {
    "license_utilization": "license_utilization",
    "vendor_overview": "vendor_overview",
    "hr_headcount": "hr_headcount",
}

TABLE_LABELS = {
    "vendor_overview": "Vendor Overview",
    "hr_headcount": "HR Headcount",
    "license_utilization": "License Utilization",
}

UPLOADS_DIR = get_uploads_dir()


def _detect_table(filename: str) -> str | None:
    """Detect table name from filename prefix."""

    stem = Path(filename).stem.lower()
    for prefix, table in TABLE_PREFIXES.items():
        if stem.startswith(prefix):
            return table
    return None


# ---------------------------------------------------------------------------
# POST /pipeline/upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept a single CSV file, detect target table, save to uploads dir."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    table = _detect_table(file.filename)
    if table is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unrecognised filename prefix: '{file.filename}'. "
                   f"Expected one of: {', '.join(TABLE_PREFIXES.keys())}",
        )

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = UPLOADS_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)

    return {
        "filename": file.filename,
        "table": table,
        "saved_path": str(save_path),
        "size_bytes": len(content),
    }


# ---------------------------------------------------------------------------
# POST /pipeline/run
# ---------------------------------------------------------------------------

@router.post("/run")
async def start_run():
    """Start pipeline trial run in a background thread. Returns run_id."""

    if is_any_run_active():
        raise HTTPException(status_code=409, detail="A pipeline run is already active")

    run = create_run()
    thread = threading.Thread(
        target=_execute_pipeline,
        args=(run,),
        daemon=True,
    )
    thread.start()

    return {"run_id": run.run_id}


@router.post("/refresh")
async def refresh_from_existing_data():
    """Start a pipeline trial run using the last stored source CSV paths."""

    if is_any_run_active():
        raise HTTPException(status_code=409, detail="A pipeline run is already active")

    run = create_run()
    thread = threading.Thread(
        target=_execute_refresh_pipeline,
        args=(run,),
        daemon=True,
    )
    thread.start()

    return {"run_id": run.run_id, "status": run.status}


# ---------------------------------------------------------------------------
# GET /pipeline/status/{run_id}
# ---------------------------------------------------------------------------

@router.get("/status/{run_id}")
async def get_status(run_id: str):
    """Return current run status. Polled every 2s by frontend."""

    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run_id: {run_id}")

    return asdict(run)


# ---------------------------------------------------------------------------
# GET /pipeline/versions
# ---------------------------------------------------------------------------

@router.get("/versions")
async def get_versions():
    """Return promoted table versions for the frontend data strip."""

    return get_promoted_versions()


@router.get("/last-run")
async def get_last_completed_run():
    """Return the most recent completed pipeline run, if one exists."""

    from db.connection import open_database_connection

    with open_database_connection() as conn:
        row = conn.execute(
            """
            SELECT run_id, status, started_at, completed_at
            FROM pipeline_runs
            WHERE status = 'complete'
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return {"run_id": None, "status": None, "started_at": None, "completed_at": None}

    return {
        "run_id": row[0],
        "status": row[1],
        "started_at": row[2],
        "completed_at": row[3],
    }


# ---------------------------------------------------------------------------
# Discovery & Baselines
# ---------------------------------------------------------------------------

@router.get("/discovery")
async def get_discovery():
    """Calculate current portfolio metrics to propose as baselines."""

    try:
        from processing.context_builder import build_context
        from processing.trueup_processor import get_trueup_exposure
        from db.connection import get_promoted_versions

        # 1. Check if we have any data
        versions = get_promoted_versions()
        if not versions:
            return {
                "can_establish": False,
                "message": "No promoted data found. Please ingest and promote your first datasets first.",
                "metrics": []
            }

        ctx = build_context()
        trueup_rows = get_trueup_exposure(ctx)
        annual_exposure = sum(
            getattr(r, "exposure_amount_annual", 0) or 0
            for r in trueup_rows
        )

        return {
            "can_establish": True,
            "message": "Ready to establish ground truth baselines from current promoted data.",
            "metrics": [
                {
                    "metric_name": "annual_exposure",
                    "label": "Annual Exposure",
                    "current_value": annual_exposure,
                    "unit": "$"
                }
            ]
        }
    except Exception as exc:
        return {
            "can_establish": False,
            "message": f"Discovery failed: {exc}",
            "metrics": []
        }


@router.get("/baselines")
async def get_baselines():
    """Return currently established baselines."""

    from db.connection import open_database_connection
    with open_database_connection() as conn:
        rows = conn.execute("SELECT metric_name, baseline_value, established_at FROM pipeline_baselines").fetchall()
    
    return [
        {"metric_name": r[0], "baseline_value": r[1], "established_at": r[2]}
        for r in rows
    ]


@router.post("/baselines")
async def establish_baselines():
    """Freeze current metrics as the established ground truth baselines."""

    from db.connection import open_database_connection, get_promoted_versions
    from processing.context_builder import build_context
    from processing.trueup_processor import get_trueup_exposure

    # 1. Calculate current state
    ctx = build_context()
    trueup_rows = get_trueup_exposure(ctx)
    annual_exposure = sum(
        getattr(r, "exposure_amount_annual", 0) or 0
        for r in trueup_rows
    )

    # 2. Persist
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with open_database_connection() as conn:
        conn.execute(
            """
            INSERT INTO pipeline_baselines (metric_name, baseline_value, established_at, established_version)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(metric_name) DO UPDATE SET
                baseline_value = excluded.baseline_value,
                established_at = excluded.established_at,
                established_version = excluded.established_version
            """,
            ("annual_exposure", annual_exposure, now, 0) # version 0 for manual discovery
        )
        conn.commit()

    return {"status": "ok", "message": "Baselines established successfully."}


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def _set_step(run: RunStatus, step_name: str, status: str, message: str = "", checks: list | None = None):
    """Update a step in the run status object with linear progress enforcement."""

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    step_order = ["ingestion", "service", "processing", "promotion"]
    try:
        target_idx = step_order.index(step_name)
    except ValueError:
        target_idx = -1

    for i, step in enumerate(run.steps):
        try:
            curr_idx = step_order.index(step.step)
        except ValueError:
            curr_idx = -1

        if step.step == step_name:
            step.status = status
            step.message = message
            if checks:
                step.checks = checks
            if status == "running":
                step.started_at = now
                run.current_step = step_name
            if status in ("passed", "failed", "skipped"):
                step.completed_at = now
        
        # If we are moving to a later step, ensure earlier steps aren't stuck in "running"
        elif status == "running" and curr_idx != -1 and target_idx != -1 and curr_idx < target_idx:
            if step.status in ("pending", "running"):
                step.status = "passed"
                if not step.completed_at:
                    step.completed_at = now
    
    update_run(run)


def _checks_by_layer(report_checks: list) -> tuple[list[dict], list[dict], list[dict]]:
    """Group CheckResult-like objects for the existing StepCard UI."""

    ingestion_checks = []
    service_checks = []
    processing_checks = []

    for check in report_checks:
        check_dict = asdict(check) if hasattr(check, "__dataclass_fields__") else {
            "layer": check.layer,
            "check_name": check.check_name,
            "passed": check.passed,
            "message": check.message,
        }
        if check.layer == "ingestion":
            ingestion_checks.append(check_dict)
        elif check.layer == "service":
            service_checks.append(check_dict)
        elif check.layer == "processing":
            processing_checks.append(check_dict)

    return ingestion_checks, service_checks, processing_checks


def _apply_trial_reports(run: RunStatus, reports: list) -> None:
    """Persist aggregate progress for a completed multi-table trial sequence."""

    promoted_versions = {}
    all_ingestion_checks = []
    all_service_checks = []
    all_processing_checks = []

    for report in reports:
        ingestion_checks, service_checks, processing_checks = _checks_by_layer(report.checks)
        all_ingestion_checks.extend(ingestion_checks)
        all_service_checks.extend(service_checks)
        all_processing_checks.extend(processing_checks)

        if not report.all_passed:
            failed_layer = "ingestion"
            if report.failure_summary:
                if report.failure_summary.startswith("service"):
                    failed_layer = "service"
                elif report.failure_summary.startswith("processing"):
                    failed_layer = "processing"
                elif report.failure_summary.startswith("api"):
                    failed_layer = "processing"

            if failed_layer == "ingestion":
                _set_step(run, "ingestion", "failed", report.failure_summary or "Check failed", all_ingestion_checks)
                _set_step(run, "service", "skipped")
                _set_step(run, "processing", "skipped")
            elif failed_layer == "service":
                _set_step(run, "ingestion", "passed", "", all_ingestion_checks)
                _set_step(run, "service", "failed", report.failure_summary or "Check failed", all_service_checks)
                _set_step(run, "processing", "skipped")
            else:
                _set_step(run, "ingestion", "passed", "", all_ingestion_checks)
                _set_step(run, "service", "passed", "", all_service_checks)
                _set_step(run, "processing", "failed", report.failure_summary or "Check failed", all_processing_checks)

            _set_step(run, "promotion", "skipped")
            run.status = "failed"
            run.failure_summary = report.failure_summary
            run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            update_run(run)
            return

        if report.pending_version is not None:
            promoted_versions[report.table_name] = report.pending_version

    _set_step(run, "ingestion", "passed", "All tables ingested", all_ingestion_checks)
    _set_step(run, "service", "passed", "All service checks passed", all_service_checks)
    _set_step(run, "processing", "passed", "All processing checks passed", all_processing_checks)
    _set_step(run, "promotion", "passed", f"All tables promoted: {promoted_versions}")

    run.status = "complete"
    run.promoted_versions = promoted_versions
    run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    update_run(run)


def _fail_run_before_trial(run: RunStatus, message: str) -> None:
    """Mark a run failed before run_trial can emit layer-specific reports."""

    _set_step(run, "ingestion", "failed", message)
    for step_name in ("service", "processing", "promotion"):
        _set_step(run, step_name, "skipped")
    run.status = "failed"
    run.failure_summary = message
    run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    update_run(run)


def _has_complete_current_versions() -> bool:
    """Return True when all canonical pipeline tables have promoted current versions."""

    from db.connection import open_database_connection

    required = set(TABLE_PREFIXES.values())
    with open_database_connection() as conn:
        rows = conn.execute(
            "SELECT table_name FROM current_versions WHERE table_name IN (?, ?, ?)",
            ("vendor_overview", "hr_headcount", "license_utilization"),
        ).fetchall()
    return {row[0] for row in rows} >= required


def _execute_refresh_pipeline(run: RunStatus) -> None:
    """Run the pipeline using the latest stored CSV paths from data_versions."""

    from pipeline.runner import ExistingDataNotFoundError, run_from_existing_paths

    audit_date = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    try:
        _set_step(run, "ingestion", "running")

        def _on_step(step_name: str, status: str):
            _set_step(run, step_name, status)

        reports = run_from_existing_paths(
            audit_date=audit_date,
            status_callback=_on_step,
        )
        _apply_trial_reports(run, reports)

    except ExistingDataNotFoundError as exc:
        _fail_run_before_trial(run, str(exc))
    except Exception as exc:
        LOGGER.exception("Pipeline refresh failed")
        _fail_run_before_trial(run, f"Unhandled: {type(exc).__name__} - {exc}")


def _execute_pipeline(run: RunStatus) -> None:
    """Run trial for each CSV found in UPLOADS_DIR. Updates RunStatus in-place."""

    from pipeline.runner import ExistingDataNotFoundError, run_initial_discovery_batch, run_trial
    from pipeline.checks import CheckResult

    audit_date = os.getenv("SAAS_SPEND_AUDIT_DATE", "2026-05-01")

    try:
        # Find CSV files in uploads
        csv_files = list(UPLOADS_DIR.glob("*.csv"))
        if not csv_files:
            _set_step(run, "ingestion", "failed", "No CSV files found in uploads directory")
            for step_name in ("service", "processing", "promotion"):
                _set_step(run, step_name, "skipped")
            run.status = "failed"
            run.failure_summary = "No CSV files found"
            run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            update_run(run)
            return

        # Sort by recommended order
        order = {"vendor_overview": 0, "hr_headcount": 1, "license_utilization": 2}
        file_table_pairs = []
        for csv_path in csv_files:
            table = _detect_table(csv_path.name)
            if table:
                file_table_pairs.append((csv_path, table))

        file_table_pairs.sort(key=lambda x: order.get(x[1], 99))

        if not file_table_pairs:
            _set_step(run, "ingestion", "failed", "No recognised CSV files found")
            for step_name in ("service", "processing", "promotion"):
                _set_step(run, step_name, "skipped")
            run.status = "failed"
            run.failure_summary = "No recognised CSV files"
            run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            update_run(run)
            return

        if not _has_complete_current_versions():
            try:
                reports = run_initial_discovery_batch(
                    [(csv_path, table_name) for csv_path, table_name in file_table_pairs],
                    audit_date=audit_date,
                    status_callback=lambda step_name, status: _set_step(run, step_name, status),
                )
                _apply_trial_reports(run, reports)
            except ExistingDataNotFoundError as exc:
                _fail_run_before_trial(run, str(exc))
            return

        promoted_versions = {}
        all_ingestion_checks = []
        all_service_checks = []
        all_processing_checks = []

        _set_step(run, "ingestion", "running")

        # Detect vendor from vendor_overview if present
        detected_vendor = None
        for csv_path, table_name in file_table_pairs:
            if table_name == "vendor_overview":
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_path, nrows=1)
                    if "vendor" in df.columns:
                        detected_vendor = str(df["vendor"].iloc[0])
                        LOGGER.info("Detected vendor for pipeline run: %s", detected_vendor)
                except Exception as exc:
                    LOGGER.warning("Could not detect vendor from CSV: %s", exc)
                break

        def _on_step(step_name: str, status: str):
            _set_step(run, step_name, status)

        for csv_path, table_name in file_table_pairs:
            LOGGER.info("Trial run: %s → %s", csv_path.name, table_name)

            report = run_trial(
                file_path=str(csv_path),
                table_name=table_name,
                audit_date=audit_date,
                vendor=detected_vendor,
                status_callback=_on_step,
            )

            # Categorise checks by layer
            for check in report.checks:
                check_dict = asdict(check) if hasattr(check, "__dataclass_fields__") else {
                    "layer": check.layer,
                    "check_name": check.check_name,
                    "passed": check.passed,
                    "message": check.message,
                }
                if check.layer == "ingestion":
                    all_ingestion_checks.append(check_dict)
                elif check.layer == "service":
                    all_service_checks.append(check_dict)
                elif check.layer == "processing":
                    all_processing_checks.append(check_dict)

            if not report.all_passed:
                # Determine which step failed
                failed_layer = "ingestion"
                if report.failure_summary:
                    if report.failure_summary.startswith("service"):
                        failed_layer = "service"
                    elif report.failure_summary.startswith("processing"):
                        failed_layer = "processing"
                    elif report.failure_summary.startswith("api"):
                        failed_layer = "processing"  # group with processing

                if failed_layer == "ingestion":
                    _set_step(run, "ingestion", "failed", report.failure_summary or "Check failed", all_ingestion_checks)
                    _set_step(run, "service", "skipped")
                    _set_step(run, "processing", "skipped")
                elif failed_layer == "service":
                    _set_step(run, "ingestion", "passed", "", all_ingestion_checks)
                    _set_step(run, "service", "failed", report.failure_summary or "Check failed", all_service_checks)
                    _set_step(run, "processing", "skipped")
                else:
                    _set_step(run, "ingestion", "passed", "", all_ingestion_checks)
                    _set_step(run, "service", "passed", "", all_service_checks)
                    _set_step(run, "processing", "failed", report.failure_summary or "Check failed", all_processing_checks)

                _set_step(run, "promotion", "skipped")
                run.status = "failed"
                run.failure_summary = report.failure_summary
                run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
                update_run(run)
                return

            if report.pending_version is not None:
                promoted_versions[table_name] = report.pending_version

        # All files passed
        _set_step(run, "ingestion", "passed", "All tables ingested", all_ingestion_checks)
        _set_step(run, "service", "passed", "All service checks passed", all_service_checks)
        _set_step(run, "processing", "passed", "All processing checks passed", all_processing_checks)
        _set_step(run, "promotion", "passed", f"All tables promoted: {promoted_versions}")

        run.status = "complete"
        run.promoted_versions = promoted_versions
        run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        update_run(run)

    except Exception as exc:
        LOGGER.exception("Pipeline execution failed")
        import traceback
        with open("scratch/pipeline_crash.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
            
        for step in run.steps:
            if step.status == "running":
                step.status = "failed"
                step.message = str(exc)
                step.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            elif step.status == "pending":
                step.status = "skipped"

        run.status = "failed"
        run.failure_summary = f"Unhandled: {type(exc).__name__} — {exc}"
        run.completed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        try:
            update_run(run)
        except Exception as e:
            with open("scratch/pipeline_crash.txt", "a", encoding="utf-8") as f:
                f.write("\n\nFailed to update run:\n" + traceback.format_exc())
