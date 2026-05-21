# SaaS Spend Management - Phase 1A Implementation Notes

## Purpose

This project phase establishes the database and ingestion foundation for the SaaS Spend Management platform. It is intentionally limited to deterministic CSV ingestion, SQLite storage, discovery profiling, and version promotion.

This phase does **not** include APIs, dashboards, auth, async orchestration, ML, or a validation engine.

## What Was Implemented

### Core capabilities

- SQLite schema initialization
- Versioned source table creation
- CSV ingestion into versioned tables
- Discovery-mode categorical profiling
- Persistence of discovered vendor rules
- Current-version promotion and lookup
- Basic derived-field recomputation for `license_utilization`
- Environment-based path resolution for database and uploads

### Supported dataset tables

- `vendor_overview`
- `hr_headcount`
- `license_utilization`

These are the phase 1A source tables used by the ingestion layer.

## Project Structure

```text
Saas_managment/
├── .env
├── PHASE1A_IMPLEMENTATION.md
├── config/
│   └── vendor_rules.py
├── data/
│   ├── uploads/
│   └── saas_spend.db
├── db/
│   ├── connection.py
│   └── schema.py
├── exceptions.py
├── ingestion_main.py
├── requirements.txt
└── services/
    └── ingestion_service.py
```

## File Responsibilities

### `.env`

Stores environment-driven paths so the project does not depend on hardcoded filesystem locations.

Current variables:

- `SAAS_SPEND_DB_PATH`
- `SAAS_SPEND_UPLOADS_DIR`
- `SAAS_SPEND_VENDOR_RULES_PATH`

### `requirements.txt`

Contains the minimal third-party dependencies for this phase:

- `pandas`
- `pydantic`

### `exceptions.py`

Defines the small exception set used across the ingestion layer.

- `DataNotReadyError`
- `DiscoveryRequiredError`
- `VersionPromotionError`

### `config/vendor_rules.py`

Holds discovery output in a simple Python dictionary:

```python
vendor_rules = {}
```

Discovery runs can append observed categorical values here. This file is intentionally simple so later phases can extend it without changing the storage contract.

### `db/connection.py`

Owns database access helpers and version resolution.

Responsibilities:

- load `.env`
- resolve project-relative or env-based paths
- open raw `sqlite3` connections
- resolve the current active version from `current_versions`
- centralize versioned table naming
- promote a table version to current
- expose `get_connection(table_name, version=None)`

Important rule:

- Only this file should understand how active versions are resolved and how versioned table names are formed.

### `db/schema.py`

Owns all DDL creation logic.

Responsibilities:

- create the SQLite database file if missing
- create the uploads directory if missing
- initialize all managed tables:
  - `data_versions`
  - `current_versions`
  - `vendor_profiles`
  - `validation_errors`

Important rule:

- Only this file should define `CREATE TABLE` statements for the managed schema.

### `services/ingestion_service.py`

This is the core of Phase 1A.

Responsibilities:

- read CSV files
- compute deterministic schema fingerprints
- detect discovery vs validation mode
- profile categorical columns during discovery
- persist discovery output to `vendor_profiles`
- update `config/vendor_rules.py`
- recompute selected derived fields for `license_utilization`
- write versioned tables to SQLite
- insert rows into `data_versions`
- promote the new version in `current_versions`

Current derived-field recomputation covers:

- `days_since_last_active`
- `days_since_provisioned`
- `contract_days_remaining`
- `days_until_notice`
- `renewal_urgency`

For this phase, missing contract fields do not fail the ingest. They only produce warnings.

Important rules:

- CSV reading belongs here
- versioned table creation belongs here
- schema fingerprinting belongs here
- discovery profiling belongs here

### `ingestion_main.py`

Entry-point script for bootstrapping the phase 1A scaffold.

Responsibilities:

- configure logging
- initialize schema
- look for example CSVs in `data/uploads`
- ingest any files that are present

This file is intentionally lightweight so it can stay stable as a launcher across later phases.

## Database Tables

### `data_versions`

Tracks each ingestion event and version status.

Important fields:

- `version_id`
- `vendor`
- `table_name`
- `uploaded_at`
- `audit_date`
- `row_count`
- `schema_fingerprint`
- `status`
- `mode`

### `current_versions`

Stores the currently promoted version per logical table.

### `vendor_profiles`

Stores discovery profiling output for categorical columns.

### `validation_errors`

Created now for future phases, even though validation logic is not implemented yet.

## Versioning Rules

### Versioned table naming

Versioned source tables follow this centralized pattern:

```python
f"{table_name}_v{version}"
```

Examples:

- `vendor_overview_v1`
- `license_utilization_v3`
- `hr_headcount_v2`

### Active version lookup

If `get_connection(table_name)` is called without a version:

- the code looks up the active version in `current_versions`
- if none exists, `DataNotReadyError` is raised

### Promotion behavior

Each successful ingest:

1. writes a new versioned table
2. inserts a row in `data_versions`
3. promotes the version in `current_versions`

This keeps table history available while always exposing a single active version.

### Schema fingerprinting

Schema fingerprints are deterministic and based on sorted column-name + dtype tokens hashed with SHA-256.

This is used to track structural changes over time without relying on file names.

## Discovery Behavior

Discovery mode activates when no prior `vendor_profiles` row exists for the vendor/table pair.

During discovery, the ingestion layer:

- identifies categorical columns
- computes null rates
- records observed values
- saves rows to `vendor_profiles`
- updates `config/vendor_rules.py`

This phase does **not** enforce rules. It only captures them.

## Working With Data Uploads

Drop source CSV files into:

```text
Saas_managment/data/uploads/
```

Expected filenames for the current demo launcher:

- `vendor_overview_patched_v5.csv`
- `hr_headcount.csv`
- `license_utilization_v4.csv`

Then run:

```bash
python ingestion_main.py
```

## Future Versioning Guidance

When adding later phases, keep these boundaries intact:

- `db/schema.py` owns schema creation
- `db/connection.py` owns version resolution and table naming
- `services/ingestion_service.py` owns ingestion and CSV reading
- `config/vendor_rules.py` remains the discovery output store

If a future phase changes the schema or the versioning contract, update this document alongside the code so the contract stays explicit.
