import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from pipeline.runner import run_trial
from pathlib import Path

csv_path = Path("data/uploads/vendor_overview_patched_v5.csv")

def on_step(step_name, status):
    print(f"STEP: {step_name} -> {status}")

report = run_trial(
    file_path=str(csv_path),
    table_name="vendor_overview",
    audit_date="2026-05-01",
    vendor="Atlassify",
    api_base_url="http://127.0.0.1:8010",
    force_promote=False,
    status_callback=on_step
)

print(f"All passed: {report.all_passed}")
print(f"Rolled back: {report.rolled_back}")
print(f"Failure summary: {report.failure_summary}")
for c in report.checks:
    print(c)
