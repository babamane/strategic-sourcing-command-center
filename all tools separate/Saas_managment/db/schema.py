"""SQLite schema initialization for the SaaS Spend project."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from db.connection import get_database_path, get_uploads_dir, open_database_connection

DDL_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS data_versions (
        version_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor TEXT NOT NULL,
        table_name TEXT NOT NULL,
        triggered_by TEXT NOT NULL,
        uploaded_at TIMESTAMP NOT NULL,
        audit_date DATE NOT NULL,
        row_count INTEGER NOT NULL,
        schema_fingerprint TEXT NOT NULL,
        status TEXT NOT NULL,
        mode TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS current_versions (
        table_name TEXT PRIMARY KEY,
        current_version INTEGER NOT NULL,
        promoted_at TIMESTAMP NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vendor_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor TEXT NOT NULL,
        table_name TEXT NOT NULL,
        derived_from_version INTEGER NOT NULL,
        column_name TEXT NOT NULL,
        observed_values TEXT NOT NULL,
        null_rate REAL NOT NULL,
        row_count INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS validation_errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        table_name TEXT NOT NULL,
        row_number INTEGER NOT NULL,
        column_name TEXT NOT NULL,
        error_type TEXT NOT NULL,
        error_message TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    """,
)


def initialize_schema() -> None:
    """Create project directories and all managed SQLite tables."""

    db_path = get_database_path()
    uploads_dir = get_uploads_dir()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    db_path.touch(exist_ok=True)

    with open_database_connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        for statement in DDL_STATEMENTS:
            connection.execute(statement)
        connection.commit()
