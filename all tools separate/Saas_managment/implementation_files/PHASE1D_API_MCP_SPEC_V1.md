# Phase 1D — API Layer, MCP Server, and Agent Triggers

**Version:** v1 · **Audit Date:** 2026-05-01 · **Session:** Phase 1D Spec  
**Depends on:** Phase 1C + Forecasting V1 complete · 127 tests passing  
**Prepared for:** API / MCP / chatbot demo implementation handoff

---

## What This Phase Is

Phase 1D exposes the processing layer over HTTP and MCP, adds agent-callable
write triggers, and plants the `recommendations` table that the Phase 2
execution agent will pick up.

This phase completes the **demand identification platform**. The system will
be able to answer natural-language questions about SaaS waste, forecast demand,
surface renewal pressure, and trigger structured actions — all through a
chatbot or agent interface.

---

## What This Phase Is Not

Phase 1D does not build:

- Email sending or rightsizing mail campaigns
- Reply tracking, aggregation, or async state
- Execution agent or workflow engine of any kind
- Contract creation triggers (expansion, downsell, flat renewal)
- Demand planning feedback loop from campaign results

All of the above belong to **Phase 2**. The async boundary starts exactly at
the point where emails go out and replies are awaited. Everything in Phase 1D
is synchronous.

The one exception is the `recommendations` table, which is written
synchronously at trigger time but is designed to be consumed asynchronously by
the Phase 2 execution agent. Its schema is defined here and must not change
in Phase 2 without a migration.

---

## Architecture

Four layers with clear ownership boundaries:

### Processing layer — unchanged

All nine processor functions remain as-is. The only modification to existing
code is a context cache in `processing/context_builder.py`. No other existing
file is touched.

### FastAPI REST layer — new

HTTP surface over all processors. One router per domain. Pydantic response
models. Context built once per request at middleware level and stored on
request state. All endpoints are read-only except `/health`.

### MCP server — new

Built with **FastMCP** (`pip install fastmcp`). FastMCP wraps the MCP SDK with
a decorator-based API — tools are plain Python functions decorated with
`@mcp.tool()`. The function docstring becomes the tool description; type hints
become the input schema. No manual schema registration.

Nine read tools, three write tools. Stdio transport for local demo;
Streamable HTTP transport for remote access. Tool descriptions are written
for a non-technical user, not a developer. `vendor` is an optional parameter
on every tool.

### Action dispatcher — new

Single file. Receives a structured payload from a write tool and routes to the
configured integration target. Writes a `recommendations` record to SQLite on
every write action. Payloads are always structured dicts — never formatted
strings — so the Phase 2 execution agent can consume them without parsing.

---

## The Only Change to Existing Code

**`processing/context_builder.py`** — add an in-process cache keyed on
`(vendor, version)` with a one-minute TTL. `build_context` checks the cache
before calling services. Prevents duplicate service calls when an agent chains
multiple tool calls in one session.

```python
_context_cache: dict[tuple, tuple[ProcessingContext, datetime]] = {}
CACHE_TTL_SECONDS = 60

def build_context(vendor=None, version=None) -> ProcessingContext:
    key = (vendor, version)
    cached, cached_at = _context_cache.get(key, (None, None))
    if cached and (datetime.now(timezone.utc) - cached_at).seconds < CACHE_TTL_SECONDS:
        return cached
    ctx = _build_fresh_context(vendor=vendor, version=version)
    _context_cache[key] = (ctx, datetime.now(timezone.utc))
    return ctx
```

The existing `build_context` body moves to `_build_fresh_context`. Signature
and return type are unchanged. All existing tests pass without modification.

---

## FastAPI REST Layer

### `api/main.py`

App setup. Mounts all routers. Context middleware builds `ProcessingContext`
once per request and stores it on `request.state.ctx`. CORS enabled for local
demo.

```python
@app.middleware("http")
async def context_middleware(request: Request, call_next):
    vendor = request.query_params.get("vendor")
    request.state.ctx = build_context(vendor=vendor, version=None)
    return await call_next(request)
```

### Routers

| File | Endpoints |
|---|---|
| `api/routers/trueup.py` | `GET /trueup/exposure?vendor=` · `GET /trueup/breakdown?vendor=&sku=&seat_type=` |
| `api/routers/ghost.py` | `GET /ghost/summary?vendor=` · `GET /ghost/detail?vendor=&department=` |
| `api/routers/reclamation.py` | `GET /reclamation?vendor=&department=&min_score=` |
| `api/routers/utilization.py` | `GET /utilization?vendor=` |
| `api/routers/renewal.py` | `GET /renewal-pressure?vendor=` |
| `api/routers/forecast.py` | `GET /forecast/demand?vendor=&department=&months=` · `GET /forecast/momentum?vendor=&months=` |
| `api/routers/health.py` | `GET /health` |

**`GET /health`** returns `audit_date`, `active_vendors`, and `fetched_at`.
The MCP server calls this first at session start so the agent can orient
itself to the data currency before making any tool calls.

### `api/schemas/responses.py`

Pydantic models mirroring existing dataclasses in `schemas/proc_results.py`
and `schemas/proc_forecast_results.py`. Field names are unchanged. Every
response model includes `computed_at`. `ForecastUnavailableResult` maps to a
response with `available=False` and a `reason` string — the endpoint returns
HTTP 200, not 4xx, so the agent can handle it gracefully.

```python
class TrueUpExposureResponse(BaseModel):
    vendor: str
    sku: str
    seat_type: str
    exposure_seats: int
    exposure_amount_annual: float
    shelfware_seats: int
    shelfware_amount_annual: float
    computed_at: str

class ForecastUnavailableResponse(BaseModel):
    available: bool = False
    reason: str
    computed_at: str
```

---

## MCP Server

### `mcp_server/server.py`

FastMCP app setup. Tools are imported from `mcp_server/tools.py` and
registered via the `@mcp.tool()` decorator — no manual schema definition.
Transport is selected at run time via the `FASTMCP_TRANSPORT` environment
variable (`stdio` for local, `streamable-http` for remote).

```python
from fastmcp import FastMCP
from mcp_server import tools  # noqa: F401 — registers all @mcp.tool decorators

mcp = FastMCP(
    "saas-spend-mcp",
    instructions=(
        "SaaS spend management assistant. Call get_health first to confirm "
        "data currency. Use vendor= to scope any tool to a single vendor. "
        "Omit vendor= for portfolio-wide results."
    ),
)

if __name__ == "__main__":
    import os
    transport = os.getenv("FASTMCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
    else:
        mcp.run()  # stdio — default for Claude Desktop
```

### `mcp_server/tools.py`

All tool definitions. FastMCP derives the tool name from the function name,
the description from the docstring, and the input schema from type hints.
No schema dict is written by hand.

Two rules enforced on every tool:

1. Docstring written for a non-technical user — no Python function names,
   no schema jargon. First sentence is the tool description the agent sees.
2. `vendor` is `Optional[str]` on every tool. Omitting it returns
   portfolio-level results across all active vendors.

```python
from fastmcp import FastMCP
from typing import Optional
from processing.context_builder import build_context
from processing.trueup_processor import get_trueup_exposure

mcp = FastMCP("saas-spend-mcp")

@mcp.tool()
def get_trueup_exposure(vendor: Optional[str] = None) -> list[dict]:
    """Shows which vendors are over-provisioned beyond contract and the
    annual cost of that exposure. Omit vendor to see all vendors."""
    ctx = build_context(vendor=vendor, version=None)
    results = get_trueup_exposure(ctx, vendor=vendor)
    return [vars(r) for r in results]
```

All nine read tools and three write tools follow this exact pattern.
The `confirmed: bool = False` parameter on write tools is declared as a
normal type-hinted argument — FastMCP includes it in the generated schema
automatically.

### Read Tools — Nine Total

| Tool name | Maps to processor | Description (user-facing) |
|---|---|---|
| `get_trueup_exposure` | `get_trueup_exposure` | Shows which vendors are over-provisioned beyond contract and the annual cost of that exposure |
| `get_trueup_breakdown` | `get_trueup_breakdown` | Breaks down true-up exposure by SKU and seat type for a specific vendor |
| `get_ghost_summary` | `get_ghost_summary` | Shows licenses still assigned to employees who have left the company, grouped by vendor |
| `get_ghost_detail` | `get_ghost_detail` | Lists the individual ghost license holders for a vendor and optional department |
| `get_reclamation_candidates` | `get_reclamation_candidates` | Returns licenses recommended for reclamation ranked by score, with estimated savings |
| `get_utilization_summary` | `get_utilization_summary` | Shows active usage rates, shelfware, and dormant license counts per vendor |
| `get_renewal_pressure` | `get_renewal_pressure` | Shows which vendor contracts are approaching notice deadlines or have already expired |
| `get_license_demand_forecast` | `get_license_demand_forecast` | Forecasts how many licenses will be needed over the next N months based on confirmed hires |
| `get_procurement_momentum_forecast` | `get_procurement_momentum_forecast` | Forecasts procurement volume trends per vendor using historical activation data |

### Write Tools — Three Total

All write tools follow the same confirmation pattern:

1. Tool calls the processor and summarises what it found.
2. Returns a confirmation prompt to the agent: what was found, what action
   will be taken, and what the estimated impact is.
3. Agent presents this to the user and waits for approval.
4. On approval, the tool calls `actions.dispatch_*` and writes a
   `recommendations` record.

The confirmation step happens inside the agent conversation loop, not in
backend code. The tool returns a structured summary dict on the first call.
A second call with `confirmed=True` fires the action.

| Tool name | Action | Integration target |
|---|---|---|
| `trigger_reclamation_review` | Surfaces reclamation candidates above `min_score`, formats ticket body | Jira |
| `trigger_renewal_alert` | Surfaces contracts within `days_threshold` of notice deadline | Slack |
| `trigger_ghost_ticket` | Surfaces ghost license list for vendor + department, formats ticket body | Jira |

**`trigger_reclamation_review` parameters:**
- `vendor: Optional[str]`
- `department: Optional[str]`
- `min_score: float = 0.7`
- `confirmed: bool = False`

**`trigger_renewal_alert` parameters:**
- `vendor: Optional[str]`
- `days_threshold: int = 30`
- `confirmed: bool = False`

**`trigger_ghost_ticket` parameters:**
- `vendor: str` (required — ticket must be scoped to one vendor)
- `department: Optional[str]`
- `confirmed: bool = False`

---

## Action Dispatcher

**`mcp_server/actions.py`** — single file, three integration targets for V1.

```python
def dispatch_jira(payload: dict) -> dict
def dispatch_slack(payload: dict) -> dict
def dispatch_csv(payload: dict) -> dict
```

### Payload contract

Every payload passed to a dispatcher is a structured dict with these keys:

```python
{
    "vendor": str,
    "action_type": str,          # "reclamation" | "renewal_alert" | "ghost_review"
    "seat_delta": int,           # negative = seats to reclaim
    "dollar_impact": float,      # annual savings or exposure
    "affected_records": list,    # list of dicts — one per license or employee
    "recommended_action": str,   # "reclaim" | "alert" | "deprovision_review"
}
```

`affected_records` is always a list of dicts, never a formatted string. This
is what the Phase 2 execution agent will consume when it picks up a
`recommendations` record. Do not change this schema without a migration.

### Integration targets — V1

| Target | What is sent | Failure behaviour |
|---|---|---|
| Jira | Ticket with summary, description, and affected records table | Log error, return `{"status": "failed", "reason": str(e)}` — do not raise |
| Slack | Message with vendor name, dollar impact, and action link | Same |
| CSV | File written to `./exports/{action_type}_{vendor}_{timestamp}.csv` | Same |

Jira and Slack credentials read from environment variables:
`JIRA_BASE_URL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`,
`SLACK_WEBHOOK_URL`.

If credentials are absent, dispatchers log a warning and return a mock
confirmation so the demo runs without live integrations configured.

---

## Recommendations Table

**`db/recommendations_table.py`** — DDL and insert/read helpers.

### DDL

```sql
CREATE TABLE IF NOT EXISTS recommendations (
    id                  TEXT PRIMARY KEY,
    vendor              TEXT NOT NULL,
    action_type         TEXT NOT NULL,
    seat_delta          INTEGER NOT NULL,
    dollar_impact       REAL NOT NULL,
    affected_records    TEXT NOT NULL,   -- JSON blob
    recommended_action  TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'pending',
    created_at          TEXT NOT NULL,
    updated_at          TEXT
);
```

### `action_type` values — Phase 1D

`reclamation` · `renewal_alert` · `ghost_review`

Phase 2 will add: `contract_expansion` · `contract_downsell` · `contract_renewal`

### `status` values

| Value | Owner | Meaning |
|---|---|---|
| `pending` | Phase 1D (this phase) | Record written, no execution agent has picked it up |
| `in_progress` | Phase 2 | Execution agent has claimed the record |
| `completed` | Phase 2 | Workflow finished successfully |
| `escalated` | Phase 2 | Workflow could not complete — requires human review |

Phase 1D only writes `pending` records. Do not implement status transitions
here — that belongs to the execution agent in Phase 2.

### Helpers

```python
def insert_recommendation(payload: dict) -> str:
    """Write a pending recommendation. Returns the generated id."""

def get_pending_recommendations(vendor: Optional[str] = None) -> list[dict]:
    """Read pending records. Phase 2 execution agent uses this to claim work."""

def get_recommendation_by_id(id: str) -> Optional[dict]:
    """Read a single record by id."""
```

---

## Public API — Complete Endpoint Map

```
GET  /health
GET  /trueup/exposure
GET  /trueup/breakdown
GET  /ghost/summary
GET  /ghost/detail
GET  /reclamation
GET  /utilization
GET  /renewal-pressure
GET  /forecast/demand
GET  /forecast/momentum
```

All endpoints accept `vendor: Optional[str]` as a query parameter. Omitting
it returns portfolio-level results. All responses include `computed_at`.
All responses return HTTP 200 — processor errors and
`ForecastUnavailableResult` are represented as structured response bodies,
not HTTP error codes, so the agent can reason about them without exception
handling.

---

## Test Plan

Target: **160+ tests passing** at end of phase. Existing 127 tests untouched.

### New test files

| File | What it covers |
|---|---|
| `tests/test_api_trueup.py` | Exposure and breakdown endpoints — vendor filter, portfolio, field completeness |
| `tests/test_api_ghost.py` | Summary and detail endpoints — ghost count sanity check against 6,828 total |
| `tests/test_api_reclamation.py` | min_score filter, score ordering, candidate count range |
| `tests/test_api_utilization.py` | Active rate ~55.0%, row count = 27 |
| `tests/test_api_renewal.py` | Expired Nexaflow and Cloudora contracts present, urgency field |
| `tests/test_api_forecast.py` | Demand returns 216 rows, momentum returns 27, ForecastUnavailableResult handled |
| `tests/test_api_health.py` | audit_date, active_vendors, fetched_at present |
| `tests/test_mcp_tools.py` | FastMCP tool list returns 12 tools · all read tools have `vendor` as optional · all write tools have `confirmed` in schema · docstrings non-empty on all tools |
| `tests/test_actions.py` | dispatch_jira/slack/csv with missing credentials return mock confirmation, not exception |
| `tests/test_recommendations_table.py` | insert returns id, get_pending returns records with status=pending, JSON blob round-trips |

### Test gate for context cache

Add one test to `tests/test_context_builder.py`:

```python
def test_build_context_returns_cached_result_within_ttl():
    ctx1 = build_context(vendor=None, version=None)
    ctx2 = build_context(vendor=None, version=None)
    assert ctx1.fetched_at == ctx2.fetched_at   # same object returned from cache
```

---

## Demo CLI

**`demo/cli.py`** — a thin interactive shell that calls FastMCP tools
in-process. No HTTP server required, no Claude Desktop required. The MCP
server is imported as a library and `mcp.call_tool()` is called directly,
so the CLI exercises the exact same tool definitions and confirmation pattern
that Claude Desktop will use when that integration is enabled.

### How it works

```python
from mcp_server.server import mcp   # FastMCP instance with all tools registered
import asyncio, json

async def call(tool: str, **kwargs):
    result = await mcp.call_tool(tool, kwargs)
    return result

def run():
    print("SaaS Spend CLI — type 'tools' to list, 'quit' to exit")
    while True:
        line = input("\n> ").strip()
        if line == "quit":
            break
        if line == "tools":
            tools = asyncio.run(mcp.get_tools())
            for t in tools:
                print(f"  {t.name:40s} {t.description.splitlines()[0]}")
            continue
        # parse: tool_name key=value key=value ...
        parts = line.split()
        tool_name = parts[0]
        kwargs = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
        result = asyncio.run(call(tool_name, **kwargs))
        print(json.dumps(result, indent=2, default=str))
```

Write tools behave identically to how the agent uses them. Calling
`trigger_ghost_ticket vendor=Veloxa` without `confirmed=true` returns the
summary and impact. Calling it again with `confirmed=true` fires the
dispatcher and writes the recommendations record. This is the same two-step
pattern the agent uses — the CLI is just the human driving it manually.

### Run

```powershell
py -3 demo/cli.py
```

### Sample session

```
> tools
  get_trueup_exposure      Shows which vendors are over-provisioned...
  get_ghost_summary        Shows licenses still assigned to employees...
  ...

> get_ghost_summary
[{"vendor": "Veloxa", "ghost_count": 1948, ...}, ...]

> get_ghost_summary vendor=Atlassify
[{"vendor": "Atlassify", "ghost_count": 1817, ...}]

> get_reclamation_candidates vendor=Databridge min_score=0.8
[{"license_id": "LIC-...", "score": 0.91, ...}, ...]

> trigger_ghost_ticket vendor=Atlassify department=Engineering
{"preview": true, "vendor": "Atlassify", "department": "Engineering",
 "ghost_count": 312, "dollar_impact": 18240.0,
 "message": "Found 312 ghost licenses in Engineering at Atlassify worth
             $18,240/yr. Call again with confirmed=true to create Jira ticket."}

> trigger_ghost_ticket vendor=Atlassify department=Engineering confirmed=true
{"status": "dispatched", "integration": "jira", "ticket_id": "MOCK-001",
 "recommendation_id": "rec-abc123", "db_status": "pending"}
```

The CLI is not a test harness — it is the demo surface. It is also the
proof that the MCP server works end-to-end before Claude Desktop is
configured.

### Future Claude Desktop handoff

When Claude Desktop integration is enabled, point `claude_desktop_config.json`
at `mcp_server/server.py` with `FASTMCP_TRANSPORT=stdio`. The tools, the
confirmation pattern, and the recommendations write path are unchanged. The
only difference is the conversation loop is Claude instead of the CLI prompt.

---

## Build Order

Do not begin step N+1 until step N's gate passes.

| Step | File(s) | Gate |
|---|---|---|
| 1 | `processing/context_builder.py` — add cache | `test_build_context_returns_cached_result_within_ttl` passes · all 127 existing tests still pass |
| 2 | `db/recommendations_table.py` | `test_recommendations_table.py` all pass · insert → get_pending round-trip confirmed |
| 3 | `api/schemas/responses.py` | Pydantic models import cleanly · `ForecastUnavailableResponse` has `available=False` default |
| 4 | `api/main.py` + `api/routers/health.py` | `GET /health` returns 200 with `audit_date`, `active_vendors`, `fetched_at` |
| 5 | `api/routers/trueup.py` + `test_api_trueup.py` | Exposure total ≥ $216,270 · breakdown rows = 20 |
| 6 | `api/routers/ghost.py` + `test_api_ghost.py` | Ghost total = 4,287 across summary rows |
| 7 | `api/routers/reclamation.py` + `test_api_reclamation.py` | Candidates returned at `min_score=0.45` |
| 8 | `api/routers/utilization.py` + `test_api_utilization.py` | `active_usage_rate` ≈ 0.5132 at portfolio level |
| 9 | `api/routers/renewal.py` + `test_api_renewal.py` | Nexaflow and Cloudora flagged as expired |
| 10 | `api/routers/forecast.py` + `test_api_forecast.py` | Demand = 216 rows · momentum = 27 rows · Prismly returns `ForecastUnavailableResponse` |
| 11 | `mcp_server/actions.py` + `test_actions.py` | All three dispatchers return mock confirmation when credentials absent |
| 12 | `mcp_server/server.py` + `mcp_server/tools.py` + `test_mcp_tools.py` | `mcp.get_tools()` returns 12 tools · `vendor` optional on all read tools · `confirmed` in schema on all write tools · `mcp.run()` starts without error |
| 13 | `demo/cli.py` | `py -3 demo/cli.py` starts without error · `tools` command lists all 12 · a read tool call returns structured output · a write tool call without `confirmed=true` returns preview · same call with `confirmed=true` writes a recommendations record |

---

## File List — Complete

```
processing/context_builder.py           ← modify only, add cache

api/__init__.py
api/main.py
api/routers/__init__.py
api/routers/trueup.py
api/routers/ghost.py
api/routers/reclamation.py
api/routers/utilization.py
api/routers/renewal.py
api/routers/forecast.py
api/routers/health.py
api/schemas/__init__.py
api/schemas/responses.py

mcp_server/__init__.py
mcp_server/server.py
mcp_server/tools.py
mcp_server/actions.py

db/recommendations_table.py

demo/cli.py

tests/test_api_trueup.py
tests/test_api_ghost.py
tests/test_api_reclamation.py
tests/test_api_utilization.py
tests/test_api_renewal.py
tests/test_api_forecast.py
tests/test_api_health.py
tests/test_mcp_tools.py
tests/test_actions.py
tests/test_recommendations_table.py
```

---

## Manual Entry Points

After completing the build, verify with:

```powershell
py -3 -m pytest
py -3 -m uvicorn api.main:app --reload
```

Run the demo CLI (calls FastMCP tools in-process, no server needed):

```powershell
py -3 demo/cli.py
```

Run the MCP server in stdio mode (Claude Desktop):

```powershell
py -3 mcp_server/server.py
```

Run the MCP server in HTTP mode (remote clients, shareable demo):

```powershell
set FASTMCP_TRANSPORT=streamable-http
py -3 mcp_server/server.py
# Listening on http://0.0.0.0:8001
```

Inspect registered tools without a live client:

```powershell
py -3 -c "from mcp_server.server import mcp; import asyncio; print(asyncio.run(mcp.get_tools()))"
```

For Claude Desktop integration, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "saas-spend": {
      "command": "py",
      "args": ["-3", "mcp_server/server.py"],
      "cwd": "C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment",
      "env": {
        "FASTMCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

---

## What Does Not Change

- `db/connection.py` — no changes
- `db/schema.py` — no changes
- `services/` — no changes
- `schemas/proc_results.py` — no changes
- `schemas/proc_forecast_results.py` — no changes
- `processing/` (all processors) — no changes
- `processing/context_builder.py` — cache addition only, no signature changes
- `config/vendor_rules.py` — no changes
- `pytest.ini` — no changes
- All existing 127 tests — untouched

---

## Environment Variables — New in Phase 1D

Add to `.env`:

```
JIRA_BASE_URL=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=
SLACK_WEBHOOK_URL=
RECOMMENDATION_EXPORT_PATH=./exports
FASTMCP_TRANSPORT=stdio
```

`FASTMCP_TRANSPORT` controls how the MCP server runs. Use `stdio` for Claude
Desktop and local development. Use `streamable-http` when the MCP server
runs on a separate machine or you need a shareable demo endpoint. All other
variables are optional for local demo — dispatchers fall back to mock
confirmations if absent.

---

## Phase 2 Scope Boundary — Do Not Build Now

| Feature | Reason deferred |
|---|---|
| Email sending and rightsizing campaigns | Requires async workflow engine |
| Reply tracking per recipient | Requires async state and webhook receiver |
| Execution agent | Picks up `pending` recommendations from Phase 1D |
| Demand planning feedback loop | Requires aggregated reply data from execution agent |
| Contract creation triggers | Requires execution agent outcome as input |
| `ml_forecasts` DDL and forecast persistence | Deferred from Forecasting V1, still deferred |
| Exit model for demand forecasting | Requires planned exit date data not in current HR model |

Phase 2 picks up from the `recommendations` table. When a `pending` record
exists, the execution agent claims it and owns everything that follows.
The demand identification layer's job ends at `status = 'pending'`.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| v1 (this file) | 2026-05-14 | Initial spec. FastAPI layer, FastMCP server, action dispatcher, and recommendations table defined. Write tools scoped to three triggers. Context cache specified. Phase 2 boundary drawn at recommendations table. |
| v2 (this file) | 2026-05-14 | MCP server implementation switched from raw MCP SDK to FastMCP. `@mcp.tool()` decorator pattern documented. `server.py` setup updated. Transport selection via `FASTMCP_TRANSPORT` env var. Claude Desktop config updated. Tool inspection command added to manual entry points. |
| v3 (this file) | 2026-05-14 | Demo CLI added. `demo/cli.py` calls FastMCP tools in-process via `mcp.call_tool()`. Two-step confirmation pattern documented for write tools. Sample session added. Claude Desktop handoff note added. Build step 13 added. |

---

*Phase 1D API Layer, FastMCP Server, and Agent Triggers v3 · Audit Date: 2026-05-01*  
*Depends on: Phase 1C + Forecasting V1 (127 tests passing) · Target: 160+ tests*  
*MCP via FastMCP · demo/cli.py calls tools in-process · stdio for Claude Desktop · streamable-http for remote*  
*Sync boundary enforced · No async state · No email workflows · No execution agent*  
*Recommendations table is the Phase 2 handoff point · Status: pending only*
