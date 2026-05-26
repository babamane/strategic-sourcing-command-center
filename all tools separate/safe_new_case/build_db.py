"""
build_db.py — One-time setup: generates synthetic data and writes saas_data.db
Run: python build_db.py
Creates data/saas_data.db with tables: fct_renewal_liability, fct_license_forecast, stg_at_risk_pool
"""

import sqlite3
import sys
from pathlib import Path
from datetime import date

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
DATA_DIR   = BASE_DIR / "data"
SQLITE_PATH = DATA_DIR / "saas_data.db"

DATA_DIR.mkdir(exist_ok=True)

print("Generating synthetic SaaS data…")

# ── import generator ──────────────────────────────────────────────────────────
sys.path.insert(0, str(BASE_DIR))
from generate_license_data_v9 import generate_rows

rows = generate_rows()
print(f"  Generated {len(rows):,} raw rows")

# ── helpers ───────────────────────────────────────────────────────────────────
def month_start(date_str: str) -> str:
    """Return YYYY-MM-01 for any YYYY-MM-DD string."""
    return date_str[:7] + "-01"

def drop_reason(row: dict) -> str:
    codes = []
    if row["health_segment"] == "At Risk":
        codes.append("LOW_ACTIVITY")
    if row["documents_edited"] == 0:
        codes.append("ZERO_EDITS")
    if row["days_since_last_login"] > 60:
        codes.append("INACTIVE_60D")
    return ",".join(codes) if codes else "LOW_USAGE"

# ── build fact rows ───────────────────────────────────────────────────────────
# Map generator field names → rag_engine field names
def map_row(r):
    return {
        "saas_tool":              r["tool"],
        "license_tier":           r["user_type"],
        "department_pillar":      r.get("pillar_name", ""),
        "job_position":           r.get("position_name", ""),
        "renewal_date":           r["renewal_date"],
        "license_start_date":     r["license_start_date"],
        "days_to_renewal":        r["days_to_renewal"],
        "days_since_last_login":  r["days_since_last_login"],
        "health_segment":         r["health_segment"],
        "documents_edited":       r["documents_edited"],
        "is_renewal":             r["is_renewal"],
        "license_cycle":          r["license_cycle"],
        "contract_status":        r["contract_status"],
        "user_id":                r["user_id"],
    }

mapped = [map_row(r) for r in rows]

# ── fct_renewal_liability ─────────────────────────────────────────────────────
# Count contracts expiring per (saas_tool, license_tier, renewal_due_month)
from collections import defaultdict

rl_counts = defaultdict(int)
for r in mapped:
    key = (r["saas_tool"], r["license_tier"], month_start(r["renewal_date"]))
    rl_counts[key] += 1

rl_rows = [
    {"saas_tool": k[0], "license_tier": k[1],
     "renewal_due_month": k[2], "projected_renewal_count": v}
    for k, v in rl_counts.items()
]
print(f"  fct_renewal_liability: {len(rl_rows):,} rows")

# ── fct_license_forecast ──────────────────────────────────────────────────────
# New acquisitions per (saas_tool, license_tier, month_start_date, dept, job)
# "new acquisition" = first license cycle (license_cycle == 1)
lf_counts = defaultdict(int)
for r in mapped:
    if r["license_cycle"] == 1:
        key = (
            r["saas_tool"], r["license_tier"],
            month_start(r["license_start_date"]),
            r["department_pillar"], r["job_position"],
        )
        lf_counts[key] += 1

lf_rows = [
    {
        "saas_tool": k[0], "license_tier": k[1],
        "month_start_date": k[2], "department_pillar": k[3],
        "job_position": k[4], "forecasted_new_acquisitions": v,
    }
    for k, v in lf_counts.items()
]
print(f"  fct_license_forecast:  {len(lf_rows):,} rows")

# ── stg_at_risk_pool ──────────────────────────────────────────────────────────
# Users with health_segment in (Low Usage, At Risk) on their latest active record
at_risk = [
    {
        "user_id":                    r["user_id"],
        "saas_tool":                  r["saas_tool"],
        "license_tier":               r["license_tier"],
        "days_until_contract_renewal": r["days_to_renewal"],
        "days_since_last_activity":   r["days_since_last_login"],
        "drop_reason_codes":          drop_reason(r),
    }
    for r in mapped
    if r["health_segment"] in ("Low Usage", "At Risk")
    and r["contract_status"] == "Active"
]
print(f"  stg_at_risk_pool:      {len(at_risk):,} rows")

# ── write SQLite ──────────────────────────────────────────────────────────────
conn = sqlite3.connect(SQLITE_PATH)
cur  = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS fct_renewal_liability;
CREATE TABLE fct_renewal_liability (
    saas_tool              TEXT,
    license_tier           TEXT,
    renewal_due_month      TEXT,
    projected_renewal_count INTEGER
);

DROP TABLE IF EXISTS fct_license_forecast;
CREATE TABLE fct_license_forecast (
    saas_tool                   TEXT,
    license_tier                TEXT,
    month_start_date            TEXT,
    department_pillar           TEXT,
    job_position                TEXT,
    forecasted_new_acquisitions INTEGER
);

DROP TABLE IF EXISTS stg_at_risk_pool;
CREATE TABLE stg_at_risk_pool (
    user_id                      TEXT,
    saas_tool                    TEXT,
    license_tier                 TEXT,
    days_until_contract_renewal  INTEGER,
    days_since_last_activity     INTEGER,
    drop_reason_codes            TEXT
);
""")

cur.executemany(
    "INSERT INTO fct_renewal_liability VALUES (:saas_tool,:license_tier,:renewal_due_month,:projected_renewal_count)",
    rl_rows,
)
cur.executemany(
    "INSERT INTO fct_license_forecast VALUES (:saas_tool,:license_tier,:month_start_date,:department_pillar,:job_position,:forecasted_new_acquisitions)",
    lf_rows,
)
cur.executemany(
    "INSERT INTO stg_at_risk_pool VALUES (:user_id,:saas_tool,:license_tier,:days_until_contract_renewal,:days_since_last_activity,:drop_reason_codes)",
    at_risk,
)

conn.commit()
conn.close()

print(f"\n[OK] saas_data.db written -> {SQLITE_PATH}")
print("     Chatbot is ready.")
