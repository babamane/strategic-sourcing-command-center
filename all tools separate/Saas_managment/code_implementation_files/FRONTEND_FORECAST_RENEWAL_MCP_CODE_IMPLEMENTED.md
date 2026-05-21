# Frontend Forecast, Renewal, and MCP Updates Code Implemented

**Project:** SaaS Spend Management Platform  
**Status:** Implemented against the live SQLite-backed API  
**Depends on:** active-demand processor fixes and renewal-pressure semantic update

## Summary

This change set removes the dead procurement momentum frontend path, rebuilds
the forecast screen around the new `active-demand-series` API, updates renewal
labels to match the new backend meaning of `hires_before_deadline`, and aligns
the MCP tool surface with the processor refactor.

## Frontend Files Changed

- [frontend/src/views/ForecastView.jsx](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/frontend/src/views/ForecastView.jsx)
- [frontend/src/views/RenewalView.jsx](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/frontend/src/views/RenewalView.jsx)
- [frontend/src/views/OverviewView.jsx](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/frontend/src/views/OverviewView.jsx)
- [frontend/src/api/endpoints.js](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/frontend/src/api/endpoints.js)
- [frontend/src/hooks/useForecast.js](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/frontend/src/hooks/useForecast.js)
- [frontend/src/components/layout/TopBar.jsx](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/frontend/src/components/layout/TopBar.jsx)

## MCP Files Changed

- [mcp_server/tools.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/mcp_server/tools.py)
- [tests/test_mcp_tools.py](C:/Users/PallantiAsrithVatsal/Desktop/Saas_managment/tests/test_mcp_tools.py)

## Forecast View Changes

Removed:

- all procurement momentum endpoint usage
- all momentum chart logic
- all momentum labels and empty-state wording

Added:

- `useActiveDemandSeries(vendor)` React Query hook
- `getActiveDemandSeries(vendor)` API call
- chart model built from `GET /forecast/active-demand-series`

Implemented behavior:

- groups active-demand rows at `vendor + sku + seat_type`
- renders actual demand as a solid line
- renders forecast demand as a dashed line
- anchors the dashed line at the last historical month so the visual line does
  not jump at the join
- renders contracted capacity as a neutral step line
- renders projected over-capacity as a warning area only where positive
- keeps the demand forecast data table and adds:
  - `baseline_active`
  - `projected_active`
  - `contracted_capacity`
  - `projected_over_capacity`

The forecast horizon slider now also limits how far forward the active-demand
series is shown on the chart.

## Renewal View Changes

Updated labels only, without restructuring the screen:

- KPI subtext now says `projected active licenses at deadline`
- banner copy now says `projected active licenses at deadline`
- table column `Hires Before Deadline` became `Projected Active at Deadline`

The underlying API value remains `row.hires_before_deadline`.

## Overview View Change

No procurement momentum dependency existed in the current Overview screen.

One semantic label was updated so the renewal table reflects the new backend
meaning:

- `Projected Active at Deadline`

## TopBar Filter Source Update

Global SKU and seat-type option derivation now includes active-demand-series
rows in addition to utilization and ghost detail rows:

```javascript
mergeFilterRows(utilization.data, detail.data, activeDemandSeries.data)
```

This keeps forecast-driven SKU and seat-type combinations available in the
shared dropdowns without changing `deriveFilters.js`.

## MCP Tool Changes

Removed:

- the old procurement-momentum MCP tool surface

Added:

- `get_active_demand`

Implemented behavior:

- calls `get_active_demand_series(ctx, vendor=vendor)`
- returns joined historical and forecast active-demand rows
- exposes contracted capacity and over-capacity directly in the MCP result

Updated:

- `get_renewal_pressure` tool docstring now describes the deadline value as the
  projected active license count at notice deadline
- MCP tool inventory test now expects `get_active_demand`

## Verification

Frontend build:

```powershell
cd frontend
npm.cmd run build
```

Result:

- build passed
- only the pre-existing chunk-size warning remained

API route checks against the running local backend:

```powershell
GET /health
GET /forecast/active-demand-series
GET /forecast/demand
GET /renewal-pressure
```

Observed:

- `/health` returned `200`
- `/forecast/active-demand-series` returned `200` with `3024` rows
- `/forecast/demand` returned `200` with `216` rows and the new forecast fields
- `/renewal-pressure` returned `200` with `27` rows

MCP verification:

```powershell
py -3 -m pytest tests/test_mcp_tools.py -v
```

Result:

- `3 passed`
- tool inventory includes `get_active_demand`
- old momentum tool name is gone

Additional code checks:

- searched `frontend/src` for active code references to `momentum` and
  `procurement`
- no active frontend code paths remain on the removed momentum endpoint

## Notes

The local frontend dev server was started on:

- [http://127.0.0.1:5175](http://127.0.0.1:5175)

The backend API was started on:

- [http://127.0.0.1:8010](http://127.0.0.1:8010)

Browser automation tooling was not available in this workspace, so the visual
verification here is based on successful build output, live endpoint checks,
and source-level removal of the old momentum path.
