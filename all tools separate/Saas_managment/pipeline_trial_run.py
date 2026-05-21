"""CLI entry point for pipeline trial runs.

Usage examples:
    py -3 pipeline_trial_run.py
        → scans data/uploads/, runs trial for each CSV found

    py -3 pipeline_trial_run.py --file data/uploads/license_utilization_v4.csv --table license_utilization
        → trial run for a single file

    py -3 pipeline_trial_run.py --json-report pipeline_report.json
        → writes machine-readable report to file

    py -3 pipeline_trial_run.py --force-promote
        → skips all checks and promotes (emergency escape hatch)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from db.connection import get_uploads_dir
from db.schema import initialize_schema
from pipeline.report import print_report, write_report_json
from pipeline.runner import run_trial


# Table name detection: derive from filename prefix
TABLE_PREFIXES = {
    "license_utilization": "license_utilization",
    "vendor_overview": "vendor_overview",
    "hr_headcount": "hr_headcount",
}


def detect_table_name(filename: str) -> str | None:
    """Detect table name from filename prefix."""

    stem = Path(filename).stem.lower()
    for prefix, table in TABLE_PREFIXES.items():
        if stem.startswith(prefix):
            return table
    return None


def configure_logging() -> None:
    """Set up readable INFO-level logs."""

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline trial run for SaaS Spend ingestion")
    parser.add_argument("--file", type=str, help="Path to a single CSV file")
    parser.add_argument("--table", type=str, help="Target table name (auto-detected from filename if omitted)")
    parser.add_argument("--json-report", type=str, help="Write JSON report to this path")
    parser.add_argument("--force-promote", action="store_true", help="Skip checks and promote (emergency)")
    args = parser.parse_args()

    configure_logging()
    initialize_schema()

    files_to_run: list[tuple[str, str]] = []  # (file_path, table_name)

    if args.file:
        # Single file mode
        file_path = Path(args.file).expanduser().resolve()
        if not file_path.exists():
            logging.error("File not found: %s", file_path)
            sys.exit(1)

        table_name = args.table or detect_table_name(file_path.name)
        if table_name is None:
            logging.error(
                "Cannot detect table from filename '%s'. Use --table to specify.",
                file_path.name,
            )
            sys.exit(1)

        files_to_run.append((str(file_path), table_name))
    else:
        # Scan uploads directory
        uploads_dir = get_uploads_dir()
        if not uploads_dir.exists():
            logging.error("Uploads directory not found: %s", uploads_dir)
            sys.exit(1)

        # Process in recommended order
        ordered_tables = ["vendor_overview", "hr_headcount", "license_utilization"]
        csv_files = list(uploads_dir.glob("*.csv"))

        for target_table in ordered_tables:
            for csv_path in csv_files:
                detected = detect_table_name(csv_path.name)
                if detected == target_table:
                    files_to_run.append((str(csv_path), target_table))
                    break

        if not files_to_run:
            logging.info("No CSV files found in %s", uploads_dir)
            sys.exit(0)

    all_reports = []
    any_failed = False

    for file_path, table_name in files_to_run:
        logging.info("Running trial: %s → %s", Path(file_path).name, table_name)
        report = run_trial(
            file_path=file_path,
            table_name=table_name,
            force_promote=args.force_promote,
        )
        all_reports.append(report)
        print_report(report)

        if not report.all_passed:
            any_failed = True
            logging.warning("Trial FAILED for %s — stopping.", table_name)
            break

    if args.json_report:
        # Write the last report (or all reports) as JSON
        if len(all_reports) == 1:
            write_report_json(all_reports[0], args.json_report)
        else:
            import json
            from dataclasses import asdict
            with open(args.json_report, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in all_reports], f, indent=2, default=str)
        logging.info("Report written to %s", args.json_report)

    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
