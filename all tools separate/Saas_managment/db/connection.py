"""SQLite connection helpers and version resolution utilities."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from exceptions import DataNotReadyError

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
ENV_PATH: Final[Path] = PROJECT_ROOT / ".env"


def load_env_file(env_path: Path = ENV_PATH) -> None:
    """Load a lightweight .env file into process environment variables."""

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()


def get_project_root() -> Path:
    """Return the repository root for the SaaS Spend project."""

    return PROJECT_ROOT


def resolve_setting_path(env_key: str, default_relative: str) -> Path:
    """Resolve a path from env with a project-root relative fallback."""

    raw_value = os.environ.get(env_key, default_relative)
    candidate = Path(raw_value).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def get_database_path() -> Path:
    """Return the SQLite database path."""

    return resolve_setting_path("SAAS_SPEND_DB_PATH", "data/saas_spend.db")


def get_uploads_dir() -> Path:
    """Return the uploads directory path."""

    return resolve_setting_path("SAAS_SPEND_UPLOADS_DIR", "data/uploads")


def get_vendor_rules_path() -> Path:
    """Return the vendor rules file path."""

    return resolve_setting_path("SAAS_SPEND_VENDOR_RULES_PATH", "config/vendor_rules.py")


def initialize_database() -> None:
    """Ensure core system tables exist."""

    conn = open_database_connection()
    try:
        # 1. data_versions: tracking every ingestion trial/promotion
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_versions (
                version_id INTEGER PRIMARY KEY,
                table_name TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                schema_fingerprint TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'trial',
                vendor TEXT,
                mode TEXT
            )
            """
        )

        # 2. current_versions: mapping table_name to its promoted version
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS current_versions (
                table_name TEXT PRIMARY KEY,
                current_version INTEGER NOT NULL,
                promoted_at TEXT NOT NULL,
                FOREIGN KEY (current_version) REFERENCES data_versions (version_id)
            )
            """
        )

        # 3. vendor_profiles: tracking discovered values for each vendor
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vendor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor TEXT NOT NULL,
                table_name TEXT NOT NULL,
                derived_from_version INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                observed_values TEXT NOT NULL,
                null_rate REAL,
                row_count INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )

        # 4. pipeline_baselines: dynamic thresholds for validation
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_baselines (
                metric_name TEXT PRIMARY KEY,
                baseline_value REAL NOT NULL,
                established_at TEXT NOT NULL,
                established_version INTEGER NOT NULL
            )
            """
        )

        # 5. pipeline_runs: persistence for run status across restarts
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_step TEXT NOT NULL,
                state_json TEXT NOT NULL, -- Full dataclass as JSON
                started_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )

        # Clear any "zombie" runs from previous crashes/restarts
        conn.execute(
            "UPDATE pipeline_runs SET status = 'failed', completed_at = ? WHERE status = 'running'",
            (datetime.now(timezone.utc).replace(microsecond=0).isoformat(),)
        )
        conn.commit()
    finally:
        conn.close()


def open_database_connection() -> sqlite3.Connection:
    """Open a raw sqlite3 connection to the project database."""

    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.touch(exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_versioned_table_name(table_name: str, version: int) -> str:
    """Return the canonical versioned source table name."""

    return f"{table_name}_v{version}"


def resolve_current_version(table_name: str) -> int:
    """Return the active version for a table or raise if none exists."""

    connection = open_database_connection()
    try:
        row = connection.execute(
            "SELECT current_version FROM current_versions WHERE table_name = ?",
            (table_name,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise DataNotReadyError(f"No active version exists for table '{table_name}'.")

    return int(row[0])


def get_next_version(table_name: str) -> int:
    """Return the next globally unique promoted version number."""

    connection = open_database_connection()
    try:
        row = connection.execute(
            "SELECT COALESCE(MAX(version_id), 0) + 1 FROM data_versions"
        ).fetchone()
    finally:
        connection.close()
    return int(row[0]) if row is not None else 1


def promote_current_version(
    table_name: str,
    version: int,
    connection: sqlite3.Connection | None = None,
) -> None:
    """Mark a version as the active version for a table."""

    owns_connection = connection is None
    conn = connection or open_database_connection()
    try:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        conn.execute(
            """
            INSERT INTO current_versions (table_name, current_version, promoted_at)
            VALUES (?, ?, ?)
            ON CONFLICT(table_name) DO UPDATE SET
                current_version = excluded.current_version,
                promoted_at = excluded.promoted_at
            """,
            (table_name, version, now),
        )
        if owns_connection:
            conn.commit()
    finally:
        if owns_connection:
            if connection is None:
                conn.close()


def sync_active_vendors(vendors: list[str]) -> None:
    """Persist the active vendor list to .env and current process environment."""

    vendor_str = ",".join(sorted(set(vendors)))
    os.environ["ACTIVE_VENDORS"] = vendor_str

    if not ENV_PATH.exists():
        ENV_PATH.write_text(f"ACTIVE_VENDORS={vendor_str}\n", encoding="utf-8")
        return

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    new_lines = []
    found = False
    for line in lines:
        if line.strip().startswith("ACTIVE_VENDORS="):
            new_lines.append(f"ACTIVE_VENDORS={vendor_str}")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append(f"ACTIVE_VENDORS={vendor_str}")
    
    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def sync_active_vendors_from_table(version: int, connection: sqlite3.Connection) -> None:
    """Extract unique vendors from vendor_overview and update global active set."""

    table_name = get_versioned_table_name("vendor_overview", version)
    try:
        rows = connection.execute(f"SELECT DISTINCT vendor FROM [{table_name}]").fetchall()
        vendors = [str(r[0]) for r in rows if r[0]]
        if vendors:
            sync_active_vendors(vendors)
    except Exception as exc:
        print(f"Failed to sync vendors from table {table_name}: {exc}")


def get_vendors_in_pending_version(table_name: str, version: int, connection: sqlite3.Connection) -> list[str]:
    """Return unique vendors present in a pending versioned table."""
    versioned_table = get_versioned_table_name(table_name, version)
    try:
        rows = connection.execute(f"SELECT DISTINCT vendor FROM [{versioned_table}]").fetchall()
        return [str(r[0]) for r in rows if r[0]]
    except Exception:
        return []


def get_promoted_versions() -> dict:
    """
    Return {table_name: {version, promoted_at, row_count}} for all tables
    with a promoted version in current_versions.
    Returns an empty dict if no versions are promoted yet.
    """

    conn = open_database_connection()
    try:
        rows = conn.execute(
            """
            SELECT cv.table_name, cv.current_version,
                   cv.promoted_at, dv.row_count
            FROM current_versions cv
            LEFT JOIN data_versions dv
              ON dv.table_name = cv.table_name
             AND dv.version_id = cv.current_version
            """
        ).fetchall()
        return {
            r[0]: {
                "version":     r[1],
                "promoted_at": r[2],
                "row_count":   r[3],
            }
            for r in rows
        }
    finally:
        conn.close()


def get_connection(table_name: str, version: int | None = None) -> tuple[sqlite3.Connection, int]:
    """Return a (connection, resolved_version) for a table lookup."""

    connection = open_database_connection()

    # Try explicitly requested version first
    if version is not None:
        versioned_table = get_versioned_table_name(table_name, version)
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (versioned_table,),
        ).fetchone()
        if row is not None:
            return connection, version

    # Fallback to current version
    try:
        resolved_version = resolve_current_version(table_name)
        versioned_table = get_versioned_table_name(table_name, resolved_version)
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (versioned_table,),
        ).fetchone()

        if row is None:
            connection.close()
            raise DataNotReadyError(
                f"Versioned table '{versioned_table}' is not available in the database."
            )
        return connection, resolved_version
    except DataNotReadyError:
        connection.close()
        # If we had a version and it failed, and now current fails, raise specific error
        if version is not None:
            raise DataNotReadyError(
                f"Requested version {version} and current version for '{table_name}' are both unavailable."
            )
        raise
