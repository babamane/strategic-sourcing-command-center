# SaaS Spend Management Platform

A local-only SaaS Spend Management Platform for ingesting vendor, HR, and license utilization CSVs, validating them through a pipeline, and surfacing spend, true-up, ghost license, reclamation, renewal, utilization, and forecasting insights in a React dashboard. The project uses SQLite for local persistence, so no external database server is required.

## Project Structure

```text
Saas_managment/
|-- api/                   # FastAPI REST layer
|-- db/                    # SQLite connection helpers and table DDL
|-- demo/                  # CLI and chatbot demo scripts
|-- frontend/              # Vite + React dashboard
|   |-- src/
|   |-- package.json
|   `-- .env.local         # optional frontend port/base URL overrides
|-- mcp_server/            # FastMCP server
|-- pipeline/              # Ingestion pipeline runner and checks
|-- processing/            # Processing context builder and processors
|-- schemas/               # Dataclass/result schemas
|-- services/              # Service layer and DB read helpers
|-- tests/                 # pytest test suite
|-- .env                   # backend environment config
|-- requirements.txt       # Python dependencies
|-- pytest.ini
|-- ingestion_main.py
|-- services_main.py
|-- processing_main.py
`-- processing_smoke_test.py
```

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher and npm
- Git
- Optional: Ollama installed locally for chatbot features

## Python Setup

Create and activate a virtual environment from the repo root:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

## Environment Config

Copy the backend `.env.example` file to `.env` and adjust the variables as needed:

```bash
cp .env.example .env
```

Jira, Slack, and recommendation export settings are optional; the app runs in local mock/demo mode without them.

| Variable | Default | Description |
| --- | --- | --- |
| `SAAS_SPEND_AUDIT_DATE` | `2026-05-01` | Audit reference date used by processors |
| `ACTIVE_VENDORS` | `Atlassify,Nexaflow,Cloudora` | Comma-separated list of active vendors; auto-updated after pipeline runs |
| `ROW_COUNT_DEVIATION_THRESHOLD` | `0.05` | Allowed row-count variance for pipeline health checks |
| `JIRA_BASE_URL` | _(empty)_ | Optional Jira integration base URL for recommendation tickets |
| `JIRA_PROJECT_KEY` | _(empty)_ | Optional Jira project key |
| `JIRA_API_TOKEN` | _(empty)_ | Optional Jira API token |
| `SLACK_WEBHOOK_URL` | _(empty)_ | Optional Slack webhook URL for renewal alerts |
| `RECOMMENDATION_EXPORT_PATH` | _(empty)_ | Optional CSV export path for recommendations |
| `FASTMCP_TRANSPORT` | `stdio` | Set to `streamable-http` to run the MCP server over HTTP |

## Frontend Setup

Install frontend dependencies:

```bash
cd frontend
npm install
```

Optional: copy the frontend `.env.example` to `.env.local` (e.g. if backend port `8000` is busy, which is common on Windows):

```bash
cp .env.example .env.local
```


## Running The App

Run backend and frontend in separate terminals.

Terminal 1, backend:

```bash
# default port
uvicorn api.main:app --reload
```

If port `8000` is busy:

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8010 --reload
```

Terminal 2, frontend:

```bash
cd frontend
npm run dev
```

The frontend runs at `http://localhost:5173`, or the next available port. Vite prints the exact URL in the terminal.

## First Run And Data Ingestion

The app ships with no pre-loaded database. On first launch:

1. Open the frontend URL from Vite.
2. Go to the **Pipeline** tab. In the dashboard shell, use the sidebar footer **Re-run pipeline** button.
3. Upload the three required CSV files:
   - `vendor_overview`: vendor contract and entitlement data
   - `hr_headcount`: employee and headcount data
   - `license_utilization`: license usage records
4. Click **Run Pipeline**.
5. Once the pipeline completes successfully, all dashboard views populate automatically.

After the first successful ingestion, subsequent runs can use **Refresh from Existing Data**. That reruns the full pipeline from the last uploaded CSV paths without requiring another file selection.

## Running Tests

Run the full test suite:

```bash
pytest
```

Verbose mode:

```bash
pytest tests/ -v
```

Expected result: all tests pass. A pytest cache permission warning on Windows is non-fatal and can be ignored.

Useful smoke check:

```bash
python processing_smoke_test.py
```

## Optional MCP Server

Run the FastMCP server:

```bash
python mcp_server/server.py
```

For HTTP transport, set this in `.env`:

```env
FASTMCP_TRANSPORT=streamable-http
```

## Optional Chatbot / Ollama Demo

1. Install Ollama from `https://ollama.ai`.
2. Pull a local model:

```bash
ollama pull llama3
```

3. Run the chatbot demo:

```bash
python demo/chatbot_cli.py
```

If Ollama is not already running, start it first:

```bash
ollama serve
```

## Optional CLI Demo

The CLI demo does not require Ollama:

```bash
python demo/cli.py
```

Type `tools` to list available MCP tools. Use `key=value` pairs to call them.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Address already in use` on port 8000 | Add `--port 8010` to the uvicorn command and set `VITE_API_BASE_URL=http://127.0.0.1:8010` in `frontend/.env.local` |
| `ModuleNotFoundError` on backend start | The virtual environment is not activated. Run `venv\Scripts\activate` on Windows or `source venv/bin/activate` on macOS/Linux |
| Frontend shows a blank page or API errors | Backend is not running, or `VITE_API_BASE_URL` points to the wrong port |
| `npm: command not found` | Node.js is not installed or not on `PATH`. Install it from `https://nodejs.org` |
| Dashboard shows no data | Pipeline has not been run yet. Go to the Pipeline tab and upload the 3 CSVs |
| `409 Conflict` when starting pipeline | A previous pipeline run is stuck. Restart the backend; zombie cleanup runs automatically on startup |
| Chatbot returns errors | Ollama is not running or the model has not been pulled. Run `ollama serve` and `ollama pull llama3` |
| pytest cache permission warning on Windows | Non-fatal. It is ignored via `pytest.ini`; tests should still pass |

## Tech Stack

| Area | Tools |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Uvicorn, FastMCP |
| Database | SQLite |
| Frontend | Node.js 18+, Vite 5, React 18, Tailwind CSS 3 |
| Frontend State/Data | TanStack React Query, Zustand, Axios |
| Visualization/UI | Recharts, Lucide |
| Testing | pytest |
| Optional LLM Demo | Ollama |

## Portfolio Export Service

After each successful pipeline promotion of `vendor_overview`, the platform can optionally export newly onboarded vendor contracts to an external portfolio tracker CSV.

### How it works

1. When a `vendor_overview` version is promoted through the pipeline (all checks pass), the runner identifies contract rows with `contract_event_type = 'new'`.
2. These rows are passed to `services/portfolio_export_service.py`, which transforms each contract to the external portfolio schema and appends it to the CSV at `PORTFOLIO_EXPORT_PATH`.
3. The export is **idempotent** — re-running the pipeline with the same data never creates duplicate rows (deduplication by vendor + SKU + start date).
4. All errors are **non-fatal** — the pipeline continues regardless of export outcome.

### Environment variable

| Variable | Default | Description |
| --- | --- | --- |
| `PORTFOLIO_EXPORT_PATH` | _(empty)_ | Absolute path to the external portfolio tracker CSV. Leave empty to skip export silently. |

`SAAS_SPEND_AUDIT_DATE` (already present) is used as the reference date for all date-derived fields in the export.

### Vendor exclusion

The following vendors are **excluded** from portfolio export (case-insensitive). These are existing/legacy vendors whose portfolios are managed externally:

- Atlassify
- Veloxa
- Prismly
- Nexaflow
- Databridge
- Cloudora

Only vendors **not** in this list are written to the portfolio CSV.

### Exported fields

All usage-derived fields (`Active_Users`, `Avg_Utilization_Pct`, `Total_Actual_Spend_USD`, `Spend%`, `Total_True_Up_USD`) are set to **zero** at initial onboarding because no usage data exists yet for newly onboarded vendors. `Total_Annual_Budget_USD` is computed from the contract (`contracted_seats × unit_price × 12`). `Start_Date` uses the audit date from `.env`, not the contract start date.

### Files

| File | Change |
| --- | --- |
| `services/portfolio_export_service.py` | New service file |
| `tests/test_portfolio_export_service.py` | 12 tests |
| `pipeline/runner.py` | One additive try/except block after promotion |
| `.env` | `PORTFOLIO_EXPORT_PATH` variable added |

### Running the export tests

```bash
pytest tests/test_portfolio_export_service.py -v
```
