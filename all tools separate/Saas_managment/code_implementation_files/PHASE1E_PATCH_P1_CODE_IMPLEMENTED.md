# Phase 1E Patch P1 v2 — Code Implemented

**Project:** SaaS Spend Management Platform  
**Patch:** `PHASE1E_PATCH_P1_V2.md` + follow-up (global SKU / seat-type filters)  
**Date:** 2026-05-17  
**Depends on:** Phase 1E v2 · Phase 2A/1F · Forecasting · 171 tests (pre-patch)

---

## What Was Implemented and Why

### Backend — renewal and reclamation triggers

Added `POST /triggers/renewal-alert` and `POST /triggers/reclamation-review` to the existing triggers router so the dashboard and chat can dispatch Slack renewal alerts and Jira reclamation review tickets using the same preview/confirm pattern as ghost, CSV, and rightsizing flows. `renewal_alert` calls `get_renewal_pressure` directly (processor independence). `reclamation_review` reuses `_reclamation_rows` and the same `insert_recommendation` payload shape as other write triggers.

### Frontend — trigger wiring

Extended `triggerClient.js`, Zustand store, and `chat.js` planner/validator to recognize `renewal_alert` and `reclamation_review`. Reclamation view gained a fourth action button; renewal banners now use the corrected action pair (`renewal_alert` + `ghost_ticket`).

### Frontend — True-Up view and navigation

Introduced `TrueUpView` with exposure KPIs, SKU-filtered bar chart, and breakdown table via `GET /trueup/breakdown`. Sidebar and `App.jsx` `VIEWS` map now include `trueup` and `pipeline` (10 dashboard routes). Pipeline completion invalidates the `health` query so vendor discovery updates without reload.

### Frontend — filters, ghost accumulation, renewal table

Added `fmt.js`, `deriveFilters.js`, and `FilterBar` for client-side filtering without new API params. Ghost view shows a cumulative exit-date chart. TopBar departments come from ghost summary `by_department`; year filter appears when two or more calendar years exist in detail data. Renewal view deduplicates banners per vendor and exposes the full 14-column contract table plus summary KPI strip.

### Frontend — forecast demand table

Demand table adds `rate_grain_applied` with quality coloring and a `by_department` expansion hook (hidden while arrays are empty).

### Follow-up — remove Pipeline nav tab

Removed **Pipeline** from the sidebar and `VIEWS` map. Ingestion still opens via **Re-run pipeline** in the sidebar footer (`enterDashboard: false` → `PipelineView`). QuickPrompts `pipeline` chips removed.

### Follow-up — reclamation excludes ghosts (active employees only)

**Reclamation is for rightsizing active licenses**, not ghost cleanup.

| Layer | Change |
|-------|--------|
| `processing/reclamation_detector.py` | Removed `ghost` from allowed `license_status`; removed auto `1.0` score for ghosts |
| `ReclamationView.jsx` | Client-side `active` / `over_tier` only; default min score **0.7**; **Usage** column; banner text |
| `chat.js` | Planner rules: ghost → `ghost_ticket`; reclamation → active low-utilization only |
| `mcp_server/tools.py` | Tool docstrings updated |

Smoke: reclamation candidates **79** (was ~4300+ when ghosts were included).

### Follow-up — reclamation min-score UX

Min score is a **lower bound** (`score >= min_score`). UI labels slider **Min score (show ≥)** and shows **Score range** KPI.

### Follow-up — global SKU and seat-type filters (all tabs)

**Problem:** Utilization charts on Overview (and Utilization tab) showed repeated `Atlassify` on the x-axis because every series row shares the same vendor; SKU/seat-type filters existed only inside individual views.

**Solution:** Moved SKU and seat-type filters to the **TopBar** as global Zustand state (`selectedSku`, `selectedSeatType`) so they persist when switching tabs. Options are derived from merged utilization + ghost detail rows. Vendor change resets department, SKU, and seat type to `"All"`.

Added shared helpers in `deriveFilters.js`:

- `filterBySkuSeat(rows, sku, seatType)` — client-side filter; never sends `"All"` to the API  
- `seriesLabel(row, vendorFilter)` — chart labels: `Vendor — SKU · seat_type` (portfolio) or `SKU · seat_type` (single vendor)  
- `mergeFilterRows(...sources)` — distinct rows for TopBar option lists  

**Views updated to use global filters:**

| View | Behavior |
|------|----------|
| Overview | Filtered KPIs, ghost-by-dept, utilization chart (`chartLabel`), renewal table (+ SKU columns) |
| Utilization | Filtered KPIs, chart, table (+ SKU / seat type columns) |
| Ghost | Removed per-view FilterBar; KPIs/chart/dept table respect global filters |
| True-Up | Removed per-view FilterBar; chart uses `chartLabel`; breakdown uses global SKU/seat |
| Renewal | Removed per-view FilterBar; KPIs + table use global filters |
| Reclamation | Filtered candidates/KPIs; table shows SKU + seat type |
| Forecast | Filtered demand rows and momentum series |

Per-view `FilterBar` instances for SKU/seat were removed where redundant; filters now live only in TopBar (consistent across tabs).

---

## File Index

### New files

| Path |
|------|
| `frontend/src/utils/fmt.js` |
| `frontend/src/utils/deriveFilters.js` |
| `frontend/src/components/shared/FilterBar.jsx` |
| `frontend/src/views/TrueUpView.jsx` |

### Changed files — Patch P1 v2

| Area | Files |
|------|--------|
| Backend | `api/routers/triggers.py`, `tests/test_api_triggers.py` |
| API / hooks | `frontend/src/api/triggerClient.js`, `frontend/src/api/endpoints.js`, `frontend/src/api/chat.js`, `frontend/src/hooks/useTrueUp.js` |
| Store / layout | `frontend/src/store/useAppStore.js`, `frontend/src/components/layout/Sidebar.jsx`, `frontend/src/components/layout/TopBar.jsx`, `frontend/src/App.jsx` |
| Views | `frontend/src/views/GhostView.jsx`, `RenewalView.jsx`, `ReclamationView.jsx`, `ForecastView.jsx`, `PipelineView.jsx` |
| Chat | `frontend/src/components/chat/QuickPrompts.jsx` |

### Changed files — global filter follow-up

| Area | Files |
|------|--------|
| Utils | `frontend/src/utils/deriveFilters.js` (`filterBySkuSeat`, `seriesLabel`, `mergeFilterRows`) |
| Store / layout | `frontend/src/store/useAppStore.js`, `frontend/src/components/layout/TopBar.jsx` |
| Views | `OverviewView.jsx`, `UtilizationView.jsx`, `GhostView.jsx`, `TrueUpView.jsx`, `RenewalView.jsx`, `ReclamationView.jsx`, `ForecastView.jsx` |
| Nav | `Sidebar.jsx`, `App.jsx`, `QuickPrompts.jsx` (pipeline tab removed) |

---

## How to Run

```powershell
# Backend (use 8010 if 8000 is busy)
cd C:\Users\PallantiAsrithVatsal\Desktop\Saas_managment
py -3 -m uvicorn api.main:app --host 127.0.0.1 --port 8010

# Frontend — dev script is under frontend/, not repo root
cd C:\Users\PallantiAsrithVatsal\Desktop\Saas_managment\frontend
npm.cmd run dev
```

Optional `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8010
```

---

## Verification Output

### Trigger tests

```text
py -3 -m pytest tests/test_api_triggers.py -q
10 passed
```

### Processing smoke

```text
py -3 processing_smoke_test.py
procurement_momentum: 27
demand_forecast: 216
renewal_pressure: 27
```

### Frontend build

```text
cd frontend
npm.cmd run build
✓ built (~11–14s, chunk-size warning acceptable)
```

### `buildAccumulationSeries` gate

```text
[{"month":"2024-03","cumulative":1}, {"month":"2024-04","cumulative":2}, {"month":"2025-01","cumulative":3}]
```

### Full pytest (informational)

```text
py -3 -m pytest tests/ -q
178 passed, 5 failed, 7 errors (pre-existing pipeline/license fixtures; not introduced by this patch)
```

---

## Intentional Deviations

| Item | Reason |
|------|--------|
| `insert_recommendation` uses `action_type` / `seat_delta` / `recommended_action` | Matches existing DB layer, not abbreviated spec dict |
| `reclamation_review` uses `_reclamation_rows` + `annual_cost` | Aligns with `ReclamationResult` dataclasses |
| Global filters in TopBar vs per-view `FilterBar` | User request: same filters on all tabs; avoids duplicate controls |
| SKU/seat dropdowns hidden when only `"All"` exists | `options.length > 1` guard in TopBar |
| Sidebar badges on ghost/reclamation/renewal | UX enhancement using existing hooks |

---

## Notes for Next Session

- `PHASE1E_PATCH_P1.md` was never in the repo; initial utils/views were built from v2 gates + data shapes.
- **Dev command:** run `npm.cmd run dev` from `frontend/`, not repo root.
- Pipeline view inside dashboard still uses Phase 2A full-screen styling inside `AppShell`.
- True-Up sidebar badge deferred (Patch P2 per spec).
- Refresh `tests/test_svc_license.py` / pipeline check tests when SQLite promotion counts stabilize.
- `FilterBar.jsx` remains available for view-specific controls (e.g. reclamation min-score slider); SKU/seat are global only.
