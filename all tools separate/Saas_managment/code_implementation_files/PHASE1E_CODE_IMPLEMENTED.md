# Phase 1E Code Implemented

## Scope

Implemented `PHASE1E_FRONTEND_SPEC_V2.md` against the current Phase 1D API/MCP layer.

## Backend Additions

New files:

- `services/mail_service.py`
- `api/schemas/triggers.py`
- `api/schemas/mail.py`
- `api/routers/triggers.py`
- `api/routers/mail.py`

Changed files:

- `api/main.py`
  - Registers `triggers.router`
  - Registers `mail.router`
- `mcp_server/tools.py`
  - Adds `send_churn_notification`
- `tests/test_mcp_tools.py`
  - Adds the new MCP tool to inventory expectations
- `tests/test_actions.py`
  - Avoids pytest `tmp_path` because this Windows workspace had temp ACL issues
- `tests/test_recommendations_table.py`
  - Avoids pytest `tmp_path` for the same reason and closes SQLite handles before cleanup

New tests:

- `tests/test_mail_service.py`
- `tests/test_api_triggers.py`
- `tests/test_api_mail.py`

## Frontend Additions

New `frontend/` Vite React app:

- Vite 5, React 18, Tailwind 3
- TanStack React Query hooks
- Zustand app state
- Axios API client
- Recharts dashboards
- Lucide icons
- Chat drawer using `/llm/api/chat` through Vite proxy
- Confirm modal for `ghost_ticket`, `reclamation`, `rightsizing`, and `churn_mail`
- Seven views:
  - Overview
  - Ghost Licenses
  - Reclamation
  - Utilization
  - Renewal Pressure
  - Demand Forecast
  - Recommendations

Local frontend proxy is configurable:

- `VITE_API_BASE_URL`, default `http://localhost:8000`
- `VITE_LLM_BASE_URL`, default `http://127.0.0.1:11434`

In this workspace, port `8000` reported a Windows bind conflict, so `.env.local`
sets `VITE_API_BASE_URL=http://127.0.0.1:8010` for local verification.

## Verification

Backend:

```powershell
py -3 -m pytest
```

Result:

- `171 passed`

Smoke:

```powershell
py -3 processing_smoke_test.py
```

Result:

- `procurement_momentum: 27`
- `demand_forecast: 216`
- `renewal_pressure: 27`

Frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run build
```

Result:

- Vite production build succeeded
- Vite emitted a chunk-size warning because the V1 app is bundled as one desktop app. No functional build failure.
- `npm install` reported 2 moderate audit findings in transitive packages; no `npm audit fix --force` was applied because it can make broad version changes outside the spec.

## Local Run Notes

Backend verified at:

- `http://127.0.0.1:8010/health`

Frontend verified at:

- `http://127.0.0.1:5175`

The spec default remains `:8000`; use `:8010` only if local Windows port binding conflicts persist.
