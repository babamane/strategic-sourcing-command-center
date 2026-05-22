"""
seed_state.py — VendorFlow AI / CRA
=====================================
Run ONCE to pre-populate state files so the dashboard shows data immediately.

Usage:
    cd cra_workflow
    python seed_state.py

Creates:
    data/trigger_log.json
    data/email_state.json
    data/agent_state.json
"""

import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone, timedelta

from email_service import (
    CSV_FILE, DATA_DIR, EMAIL_STATE_FILE,
    TRIGGER_LOG_FILE, _map_vendor_name, ALERT_FIELDS,
)

STATE_FILE = os.path.join(DATA_DIR, "agent_state.json")

WORKFLOW_STAGES = {
    "Planning":  "Procurement Team",
    "Budgeting": "Procurement Team",
    "Approval":  "Executive Approver",
    "Execution": "Procurement Team",
    "Closed":    "None",
}

# (alert_key, days_low, days_high, util_min, util_max, ttype, lifecycle, stage, max_sample)
WINDOWS = [
    ("Alert_180",      91,  180, 0,   200, "180-Day Planning",          "Renewal Planning",             "Planning",   8),
    ("Alert_90",       31,   90, 0,   200, "90-Day Finance Escalation", "Finance Escalation",           "Budgeting",  6),
    ("Alert_30",        8,   30, 0,   200, "30-Day Exec Escalation",    "Critical / Executive Review",  "Approval",   5),
    ("Alert_Critical",  0,    7, 0,   200, "Critical 7-Day",            "Expiring",                     "Execution",  4),
    ("Alert_High_Util", 0,  365, 80,  200, "High Utilization Critical", "Capacity Planning",            "Planning",   5),
    ("Alert_Low_Util",  0,  365, 0,   70,  "Underutilized License",     "Optimization Review",          "Planning",   5),
]


def _safe_int(val):
    try: return int(float(str(val).strip()))
    except: return None

def _safe_float(val):
    try: return float(str(val).replace("%","").strip())
    except: return None

def _write(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def seed():
    if not os.path.exists(CSV_FILE):
        print(f"CSV not found: {CSV_FILE}")
        return

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    now = datetime.now(timezone.utc)
    trigger_log = {}
    email_state = {}
    agent_state = {}

    for alert_key, d_low, d_high, u_min, u_max, ttype, lifecycle, stage, limit in WINDOWS:
        picked = []
        for r in all_rows:
            days = _safe_int(r.get("Days_to_Renewal"))
            util = _safe_float(r.get("Avg_Utilization_Pct"))
            if days is None or util is None: continue
            if d_low <= days <= d_high and u_min <= util <= u_max:
                picked.append(r)
        picked = picked[:limit]

        for row in picked:
            cid    = row["Contract_ID"]
            vendor = _map_vendor_name(row.get("Vendor", ""), cid)
            days   = _safe_int(row.get("Days_to_Renewal")) or 0
            ts     = (now - timedelta(hours=days % 24)).isoformat()

            trigger_log.setdefault(cid, {})
            trigger_log[cid][alert_key]         = {"status": "SENT", "days": days, "vendor": vendor, "ts": ts}
            trigger_log[cid]["trigger_type"]    = ttype
            trigger_log[cid]["lifecycle_stage"] = lifecycle

            email_state.setdefault(cid, {f: "" for f in ALERT_FIELDS})
            email_state[cid][alert_key] = "SENT"

            if cid not in agent_state:
                agent_state[cid] = {
                    "Stage":            stage,
                    "Pending_With":     WORKFLOW_STAGES.get(stage, "Procurement Team"),
                    "Email_Sent":       True,
                    "Execution_Status": "Email Sent",
                    "Escalated":        days <= 30,
                    "Stage_History":    [stage],
                }

    _write(TRIGGER_LOG_FILE, trigger_log)
    _write(EMAIL_STATE_FILE,  email_state)
    _write(STATE_FILE,        agent_state)

    stage_counter = Counter(v["Stage"] for v in agent_state.values())
    print("Seed complete:")
    print(f"   trigger_log  -> {TRIGGER_LOG_FILE}  ({len(trigger_log)} contracts)")
    print(f"   email_state  -> {EMAIL_STATE_FILE}  ({len(email_state)} contracts)")
    print(f"   agent_state  -> {STATE_FILE}  ({len(agent_state)} contracts)")
    print()
    print("Workflow stage breakdown:")
    for s, n in sorted(stage_counter.items()):
        print(f"   {s:<12} : {n} contracts")


if __name__ == "__main__":
    seed()
