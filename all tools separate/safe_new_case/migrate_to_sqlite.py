"""
migrate_to_sqlite.py
────────────────────
One-time migration script: reads all source tables from MySQL
using simple SELECT * queries and writes them into saas_data.db
(SQLite) in the project directory.

Run once:
    python migrate_to_sqlite.py

After this runs successfully, rag_engine_v4.py will use
saas_data.db exclusively — no MySQL server required.
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
import urllib.parse
from dotenv import load_dotenv

# ── Load credentials from .env ────────────────────────────────────────────────
load_dotenv()

DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_NAME     = os.getenv("DB_NAME", "saas_analytics")
SQLITE_PATH = os.getenv("SQLITE_DB_PATH", "saas_data.db")

# ── Tables to migrate ─────────────────────────────────────────────────────────
TABLES = [
    "fct_renewal_liability",
    "fct_license_forecast",
    "stg_at_risk_pool",
]

# ── SQLAlchemy MySQL engine (source) ──────────────────────────────────────────
try:
    from sqlalchemy import create_engine as _sa_create_engine
    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
    MYSQL_URI = (
        f"mysql+pymysql://{DB_USER}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    mysql_engine = _sa_create_engine(MYSQL_URI)
    print(f"[OK] Connected to MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
except Exception as exc:
    print(f"[ERROR] Could not connect to MySQL: {exc}")
    raise SystemExit(1)

# -- SQLite target -------------------------------------------------------------
sqlite_path = Path(__file__).resolve().parent / SQLITE_PATH
sqlite_conn = sqlite3.connect(sqlite_path)
print(f"[OK] SQLite target: {sqlite_path}")

# -- Migrate each table -------------------------------------------------------
for table in TABLES:
    print(f"\n-> Migrating [{table}] ...")
    try:
        with mysql_engine.connect() as conn:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
        row_count = len(df)
        df.to_sql(table, sqlite_conn, if_exists="replace", index=False)
        print(f"   [OK] {row_count:,} rows written to SQLite")
    except Exception as exc:
        print(f"   [ERROR] Failed to migrate [{table}]: {exc}")

sqlite_conn.close()
print(f"\n[DONE] Migration complete -> {sqlite_path}")
print("   You can now run the app without a MySQL server.")
