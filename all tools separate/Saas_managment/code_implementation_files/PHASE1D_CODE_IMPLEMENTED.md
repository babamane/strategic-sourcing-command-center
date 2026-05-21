# Phase 1D Code Implemented

**Project:** SaaS Spend Management Platform  
**Phase:** 1D — API layer, FastMCP server, write triggers, recommendations persistence, demos  
**Status:** Implemented per `PHASE1D_API_MCP_SPEC_V1.md` (with noted deviations below)  
**Spec reference:** [PHASE1D_API_MCP_SPEC_V1.md](./PHASE1D_API_MCP_SPEC_V1.md)  
**Depends on:** Phase 1C processing layer + services (unchanged except `processing/context_builder.py` cache)

## What We Implemented and Why

### 1. Context cache (`processing/context_builder.py`)

**What:** In-process cache keyed on `(vendor, version)` with 60s TTL. Fresh loads moved to `_build_fresh_context`; public `build_context` signature unchanged.

**Why:** Spec requires fewer duplicate service/SQLite round-trips when an agent or UI chains multiple tool or API calls in one session. TTL uses `total_seconds()` (not `timedelta.seconds`) so the window is correct beyond one minute and across sub-minute boundaries.

### 2. Recommendations table (`db/recommendations_table.py`)

**What:** SQLite DDL for `recommendations`, plus `insert_recommendation`, `get_pending_recommendations`, `get_recommendation_by_id`. JSON serialization for `affected_records`.

**Why:** Phase 1D defines the synchronous handoff surface for Phase 2: structured payloads only, `status = pending` on insert, no execution agent in this phase.

### 3. FastAPI REST layer (`api/`)

**What:**

- `api/main.py` — app, CORS, HTTP middleware that builds `ProcessingContext` once per request from query `vendor` and stores it on `request.state.ctx`.
- Routers mirroring the spec path map: `health`, `trueup`, `ghost`, `reclamation`, `utilization`, `renewal`, `forecast`.
- `api/schemas/responses.py` — Pydantic models aligned with processor/dataclass outputs for JSON responses.

**Why:** Exposes the same logic as the processing layer over HTTP for agents, dashboards, and local demos without duplicating business rules. Vendor scoping follows the spec: optional `vendor` query param; middleware narrows the loaded context the same way `build_context(vendor=...)` does.

### 4. FastMCP server (`mcp_server/`)

**What:**

- `mcp_server/server.py` — `FastMCP` instance, bootstraps `sys.path` to repo root so `py -3 mcp_server/server.py` works; imports `mcp_server.tools` to register tools; `FASTMCP_TRANSPORT` for stdio vs `streamable-http`.
- `mcp_server/tools.py` — nine read tools + three write tools. Read tools delegate to processors after `build_context`. Write tools implement preview then `confirmed=true` dispatch + `insert_recommendation`.
- `mcp_server/actions.py` — `dispatch_jira`, `dispatch_slack`, `dispatch_csv`; missing credentials log a warning and return mock-shaped results so demos do not crash.

**Why:** Spec calls for FastMCP (`@mcp.tool()`), non-technical docstrings, optional `vendor` on reads, and a two-step human confirmation pattern for writes. Mock dispatch keeps local runs safe without Jira/Slack env.

### 5. Demos (`demo/`)

**What:**

- `demo/cli.py` — thin REPL calling `await mcp.call_tool(...)` in-process; `tools` command uses `mcp.list_tools()`; parses `key=value` with light type coercion (`true`/`false`, ints, floats).
- `demo/chatbot_cli.py` — Ollama `/api/chat` with configurable defaults (`OllamaClientConfig`). **Planning** requests use `format: "json"` and a JSON contract (`phase` + `tools` calls or `answer`). **Final** user-facing text uses a follow-up request **without** `format: "json"` so the model answers in plain language after tool results are injected.

**Why:** CLI proves MCP tools without Claude Desktop. Chatbot proves the same tool surface behind natural language with explicit separation between structured planning and readable answers (per product request).

### 6. Tests (`tests/`)

**What:** New modules `test_api_*.py`, `test_mcp_tools.py`, `test_actions.py`, `test_recommendations_table.py`; extended `tests/test_proc_context_builder.py` with cache identity test.

**Why:** API and MCP tests compare counts and aggregates to **live processor output** from the same SQLite-backed `build_context()` so they track the dataset instead of brittle magic numbers from an older audit snapshot. `test_recommendations_table.py` monkeypatches `open_database_connection` to a temp file so tests do not pollute the main DB.

## File Index (New or Materially Changed)

| Area | Files |
|------|--------|
| Processing (only change) | `processing/context_builder.py` |
| DB | `db/recommendations_table.py` |
| API | `api/__init__.py`, `api/main.py`, `api/schemas/__init__.py`, `api/schemas/responses.py`, `api/routers/__init__.py`, `api/routers/health.py`, `api/routers/trueup.py`, `api/routers/ghost.py`, `api/routers/reclamation.py`, `api/routers/utilization.py`, `api/routers/renewal.py`, `api/routers/forecast.py` |
| MCP | `mcp_server/__init__.py`, `mcp_server/server.py`, `mcp_server/tools.py`, `mcp_server/actions.py` |
| Demos | `demo/cli.py`, `demo/chatbot_cli.py` |
| Tests | `tests/test_api_health.py`, `tests/test_api_trueup.py`, `tests/test_api_ghost.py`, `tests/test_api_reclamation.py`, `tests/test_api_utilization.py`, `tests/test_api_renewal.py`, `tests/test_api_forecast.py`, `tests/test_mcp_tools.py`, `tests/test_actions.py`, `tests/test_recommendations_table.py`, `tests/test_proc_context_builder.py` (cache test) |
| Dependencies | `requirements.txt` (adds `fastapi`, `uvicorn[standard]`, `fastmcp`, `httpx`, `pytest`) |

## Intentional Deviations from the Written Spec

1. **`RenewalPressureResponse.hires_before_deadline`** is modeled as **`float`** in `api/schemas/responses.py` because the renewal processor rounds with two decimal places while `schemas/proc_results.RenewalPressureResult` still types the field as `int`. Pydantic validation failed on real rows until the API model matched actual values.

2. **Forecast API tests** assert portfolio momentum row count equals the processor and that the **count** of `ForecastUnavailableResult` rows matches JSON rows with `available: false`, instead of hard-coding vendor names like Prismly (which may be absent from `ACTIVE_VENDORS` in some `.env` setups).

3. **FastMCP API:** tests and demos use `await mcp.list_tools()` rather than a `get_tools()` name from an older spec draft.

## Operational Notes for the Next Session

### `ACTIVE_VENDORS` is the gate for vendor-scoped answers

Services read `ACTIVE_VENDORS` from `.env` at import time. A vendor must appear in that list or `build_context(vendor="X")` can fail validation or return empty processor results. To answer questions about a vendor (e.g. Veloxa), add it to `ACTIVE_VENDORS` **and** ensure contract history exists for scoped loads (otherwise `get_contract_history` can raise `DataNotReadyError`).

### Manual commands

```powershell
py -3 -m pytest tests/
py -3 -m uvicorn api.main:app --reload
py -3 demo/cli.py
py -3 demo/chatbot_cli.py
py -3 mcp_server/server.py
```

### Environment variables (Phase 1D additions)

See `PHASE1D_API_MCP_SPEC_V1.md` for `JIRA_*`, `SLACK_WEBHOOK_URL`, `RECOMMENDATION_EXPORT_PATH`, `FASTMCP_TRANSPORT`. All are optional for mock-only local runs.

### Phase 2 boundary (unchanged by design)

Phase 1D stops at writing `recommendations` with `status = pending`. No email, no async execution agent, no status transitions beyond insert.

## Verification

Full suite: `py -3 -m pytest tests/` — **161 passed** at time of writing (after forecast and renewal API test adjustments above).

---

*Prepared for continuation: wire real Jira/Slack, tighten chatbot prompts, expand `ACTIVE_VENDORS`, or begin Phase 2 execution agent against `recommendations`.*
