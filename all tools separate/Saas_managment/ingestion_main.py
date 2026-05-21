"""Entry point for the SaaS Spend Phase 1A ingestion scaffold."""

from __future__ import annotations

import logging

from db.connection import get_uploads_dir
from db.schema import initialize_schema
from services.ingestion_service import ingest


def configure_logging() -> None:
    """Set up readable INFO-level logs."""

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def main() -> None:
    """Initialize schema and ingest any uploaded example CSVs."""

    configure_logging()
    logging.info("Creating schema...")
    initialize_schema()

    uploads_dir = get_uploads_dir()
    example_files = [
        (uploads_dir / "vendor_overview_patched_v5.csv", "Atlassify", "vendor_overview", "2026-05-01"),
        (uploads_dir / "hr_headcount.csv", "Atlassify", "hr_headcount", "2026-05-01"),
        (uploads_dir / "license_utilization_v4.csv", "Atlassify", "license_utilization", "2026-05-01"),
    ]

    for csv_path, vendor, table_name, audit_date in example_files:
        if not csv_path.exists():
            logging.info("Skipping missing upload: %s", csv_path)
            continue
        ingest(str(csv_path), vendor=vendor, table_name=table_name, audit_date=audit_date)


if __name__ == "__main__":
    main()
