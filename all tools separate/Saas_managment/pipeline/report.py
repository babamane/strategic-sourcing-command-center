"""Terminal and JSON output for pipeline trial run reports."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TextIO
import sys

from pipeline.checks import CheckResult
from pipeline.runner import TrialRunReport


def print_report(report: TrialRunReport, file: TextIO | None = None) -> None:
    """Print a structured pass/fail summary to stdout (or any file-like)."""

    out = file or sys.stdout
    w = out.write

    version_label = f"v{report.pending_version}" if report.pending_version else "N/A"
    w("\n")
    w("=" * 56 + "\n")
    w(f" PIPELINE TRIAL RUN — {report.table_name} {version_label}\n")
    w(f" Started:   {report.started_at}\n")
    w(f" Completed: {report.completed_at}\n")
    w("=" * 56 + "\n")
    w("\n")

    # Group checks by layer
    layers = ("ingestion", "service", "processing", "api")
    layer_labels = {
        "ingestion": "INGESTION",
        "service": "SERVICE LAYER",
        "processing": "PROCESSING LAYER",
        "api": "API LAYER",
    }

    for layer in layers:
        layer_checks = [c for c in report.checks if c.layer == layer]
        if not layer_checks:
            continue

        w(f" {layer_labels.get(layer, layer.upper())}\n")
        for check in layer_checks:
            icon = "✓" if check.passed else "✗"
            w(f"  {icon} {check.check_name:<28s}{check.message}\n")
        w("\n")

    w("=" * 56 + "\n")
    if report.all_passed:
        w(f" RESULT:  ALL CHECKS PASSED\n")
        action = f"{report.table_name} promoted to {version_label}" if report.promoted else "No promotion"
        w(f" ACTION:  {action}\n")
    else:
        w(f" RESULT:  FAILED\n")
        if report.failure_summary:
            w(f" DETAIL:  {report.failure_summary}\n")
        if report.rolled_back:
            w(f" ACTION:  {report.table_name} {version_label} ROLLED BACK\n")
        else:
            w(f" ACTION:  No rollback performed\n")
    w("=" * 56 + "\n")
    w("\n")


def write_report_json(report: TrialRunReport, output_path: str) -> None:
    """Write the report as JSON to output_path."""

    data = asdict(report)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
