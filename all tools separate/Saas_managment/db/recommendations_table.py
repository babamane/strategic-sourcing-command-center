"""SQLite persistence for Phase 1D agent recommendations (Phase 2 handoff)."""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from db.connection import open_database_connection

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS recommendations (
    id                  TEXT PRIMARY KEY,
    vendor              TEXT NOT NULL,
    action_type         TEXT NOT NULL,
    seat_delta          INTEGER NOT NULL,
    dollar_impact       REAL NOT NULL,
    affected_records    TEXT NOT NULL,
    recommended_action  TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'pending',
    created_at          TEXT NOT NULL,
    updated_at          TEXT
);
"""


def ensure_recommendations_table(connection: sqlite3.Connection | None = None) -> None:
    """Create the recommendations table if it does not exist."""

    owns = connection is None
    conn = connection or open_database_connection()
    try:
        conn.execute(DDL)
        if owns:
            conn.commit()
    finally:
        if owns:
            conn.close()


def insert_recommendation(payload: dict[str, Any]) -> str:
    """Write a pending recommendation. Returns the generated id."""

    ensure_recommendations_table()
    rec_id = f"rec-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with open_database_connection() as conn:
        conn.execute(
            """
            INSERT INTO recommendations (
                id, vendor, action_type, seat_delta, dollar_impact,
                affected_records, recommended_action, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                rec_id,
                str(payload["vendor"]),
                str(payload["action_type"]),
                int(payload["seat_delta"]),
                float(payload["dollar_impact"]),
                json.dumps(payload["affected_records"]),
                str(payload["recommended_action"]),
                now,
            ),
        )
        conn.commit()
    return rec_id


def get_pending_recommendations(vendor: Optional[str] = None) -> list[dict[str, Any]]:
    """Read pending records."""

    ensure_recommendations_table()
    with open_database_connection() as conn:
        if vendor:
            cur = conn.execute(
                "SELECT * FROM recommendations WHERE status = 'pending' AND vendor = ? ORDER BY created_at DESC",
                (vendor,),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM recommendations WHERE status = 'pending' ORDER BY created_at DESC"
            )
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        record = dict(zip(cols, row))
        try:
            record["affected_records"] = json.loads(record["affected_records"])
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid JSON in affected_records for id=%s", record.get("id"))
        results.append(record)
    return results


def get_recommendation_by_id(rec_id: str) -> Optional[dict[str, Any]]:
    """Read a single record by id."""

    ensure_recommendations_table()
    with open_database_connection() as conn:
        cur = conn.execute("SELECT * FROM recommendations WHERE id = ?", (rec_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
    record = dict(zip(cols, row))
    try:
        record["affected_records"] = json.loads(record["affected_records"])
    except (json.JSONDecodeError, TypeError):
        pass
    return record
