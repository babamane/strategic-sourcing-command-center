"""Persistent pipeline run state store using SQLite."""

from __future__ import annotations

import uuid
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from db.connection import open_database_connection


@dataclass
class StepStatus:
    step: str               # "ingestion" | "service" | "processing" | "promotion"
    label: str              # "Ingestion" | "Service Layer" | etc.
    status: str             # "pending" | "running" | "passed" | "failed" | "skipped"
    message: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    checks: list[dict] = field(default_factory=list)  # CheckResult dicts


@dataclass
class RunStatus:
    run_id: str
    status: str             # "running" | "complete" | "failed"
    current_step: str
    steps: list[StepStatus] = field(default_factory=list)
    started_at: str = ""
    completed_at: str | None = None
    promoted_versions: dict | None = None   # {"license_utilization": 4, ...} on success
    failure_summary: str | None = None


def _default_steps() -> list[StepStatus]:
    """Return the four default step cards in their initial state."""

    return [
        StepStatus(step="ingestion", label="Ingestion", status="pending"),
        StepStatus(step="service", label="Service Layer", status="pending"),
        StepStatus(step="processing", label="Processing", status="pending"),
        StepStatus(step="promotion", label="Promotion", status="pending"),
    ]


def _save_run(run: RunStatus) -> None:
    """Persist a run status to the database."""

    conn = open_database_connection()
    try:
        state_json = json.dumps(asdict(run))
        conn.execute(
            """
            INSERT INTO pipeline_runs (run_id, status, current_step, state_json, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status = excluded.status,
                current_step = excluded.current_step,
                state_json = excluded.state_json,
                completed_at = excluded.completed_at
            """,
            (run.run_id, run.status, run.current_step, state_json, run.started_at, run.completed_at)
        )
        conn.commit()
    finally:
        conn.close()


class _RunStoreCompat:
    """Backward-compatible hook for tests that used to clear in-memory state."""

    def clear(self) -> None:
        conn = open_database_connection()
        try:
            conn.execute("DELETE FROM pipeline_runs")
            conn.commit()
        finally:
            conn.close()


_runs = _RunStoreCompat()


def create_run() -> RunStatus:
    """Create a new pipeline run and persist it."""

    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run = RunStatus(
        run_id=run_id,
        status="running",
        current_step="ingestion",
        steps=_default_steps(),
        started_at=now,
    )
    _save_run(run)
    return run


def get_run(run_id: str) -> RunStatus | None:
    """Retrieve a run by ID from the database."""

    conn = open_database_connection()
    try:
        row = conn.execute("SELECT state_json FROM pipeline_runs WHERE run_id = ?", (run_id,)).fetchone()
    finally:
        conn.close()
    
    if not row:
        return None
    
    data = json.loads(row[0])
    # Reconstruct dataclasses
    steps = [StepStatus(**s) for s in data.pop("steps", [])]
    return RunStatus(steps=steps, **data)


def update_run(run: RunStatus) -> None:
    """Public helper to persist updates to an existing run object."""
    _save_run(run)


def get_latest_run() -> RunStatus | None:
    """Return the most recently created run from the database."""

    conn = open_database_connection()
    try:
        row = conn.execute("SELECT run_id FROM pipeline_runs ORDER BY started_at DESC LIMIT 1").fetchone()
    finally:
        conn.close()
    
    if not row:
        return None
    return get_run(row[0])


def is_any_run_active() -> bool:
    """Return True if any run is currently in 'running' status in the database."""

    conn = open_database_connection()
    try:
        row = conn.execute("SELECT 1 FROM pipeline_runs WHERE status = 'running' LIMIT 1").fetchone()
    finally:
        conn.close()
    return row is not None
