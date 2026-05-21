# Phase 1E — Patch P1 v2 (Corrected)

**Version:** patch-p1-v2 (replaces patch-p1)  
**Date:** 2026-05-17  
**Depends on:** Phase 1E v2 · Phase 2A/1F (Pipeline) · FORECASTING implemented · 171 tests passing  
**Scope:** Primarily frontend. Two small backend trigger endpoints required (see section A).

---

## Issues Fixed vs patch-p1

| # | Issue in patch-p1 | Fix in this file |
|---|---|---|
| 1 | `TwoActionBanner` in RenewalView used wrong trigger types (`ghost_ticket` + `reclamation`) | Changed to `renewal_alert` + `ghost_ticket` |
| 2 | `renewal_alert` and `reclamation_review` trigger types entirely absent from spec | Added backend endpoints + all frontend wiring |
| 3 | `PipelineView.jsx` (Phase 2A) has no Sidebar nav item, no VIEWS map entry, no health-query invalidation | Added pipeline nav, VIEWS entry, invalidation note |
| 4 | ForecastView demand table missing `rate_grain_applied` column | Added column to table spec |
| 5 | `by_department` in forecast rows has no expansion hook | Added expansion hook note |

---

## Phase 2A Impact on This Patch

Phase 2A is **non-breaking** for everything in this patch with two notes:

1. **Dynamic vendor discovery.** `ACTIVE_VENDORS` is now updated by the pipeline at runtime.
   The TopBar already derives vendors from `useHealth()` — this is correct. No change needed.
   However: after a successful pipeline run, the health query must be invalidated so the
   vendor dropdown picks up newly discovered vendors without a page reload.

   ```js
   // In PipelineView.jsx — after a run completes with status "completed":
   queryClient.invalidateQueries({ queryKey: ["health"] });
   ```

   Add this one line to the existing `PipelineView.jsx` success handler.

2. **Ghost detector and true-up fixes** (Phase 2A corrected `future_hires` filtering and
   `MAX(of_id)` for true-up). These change the numbers the frontend displays — they do not
   change any field names or response shapes. No frontend code changes needed.

---

## Root Cause Summary (complete — all 12 gaps)

| # | Gap | Root cause |
|---|---|---|
| 1 | Renewal banners duplicated per SKU | Processor returns one row per contract. Spec rendered one banner per row. |
| 2 | Renewal table missing SKU/seat-type/exposure/pressure columns | Fields exist on `RenewalPressureResult` but were never spec'd for the table. |
| 3 | Renewal true-up forecast not shown | `exposure_seats`, `hires_before_deadline`, `pressure_score`, `pressure_classification` computed but not surfaced. |
| 4 | Ghost accumulation chart missing | `exit_date` on `GhostDetailResult` is the time axis. Never spec'd. |
| 5 | Department dropdown not vendor-scoped | Departments were hardcoded. `by_department` on summary response is the correct source. |
| 6 | No year-on-year filter | `exit_date` on ghost detail rows enables client-side year derivation. Never spec'd. |
| 7 | No SKU / seat-type filters on charts | `sku` and `seat_type` exist on all relevant rows. Client-side filter. Never spec'd. |
| 8 | True-Up view missing | Omitted from v2 spec nav and views/ list entirely. |
| 9 | `renewal_alert` trigger type missing everywhere | MCP tool `trigger_renewal_alert` exists but no backend endpoint, no frontend type, no client mapping. |
| 10 | `reclamation_review` trigger type missing | MCP tool `trigger_reclamation_review` (Jira) exists but absent from spec. `reclamation` type was mapped to CSV only. |
| 11 | PipelineView has no nav item | Phase 2A implemented the view but the Sidebar was never updated. |
| 12 | ForecastView demand table missing `rate_grain_applied` | Field exists in all demand rows. Explains why some months show 0 demand. |

---

## Data Source Reference

### `GET /ghost/detail`

```
license_id, vendor, sku, seat_type, employee_id, email,
department, job_level, exit_date (ISO or ""), exit_type,
days_orphaned (int), monthly_cost, cost_at_risk, annual_cost,
days_since_last_active, computed_at
```

Vendor scoped by middleware. `department` is an optional query param.
`sku` and `seat_type` are NOT query params — filter client-side.

### `GET /ghost/summary`

```
vendor, ghost_license_count, total_cost_at_risk_monthly,
total_cost_at_risk_annual, avg_days_orphaned, max_days_orphaned,
by_department: [{department, ghost_count, monthly_cost}],
computed_at
```

`by_department` is the source for vendor-scoped department lists in TopBar.

### `GET /renewal-pressure`

```
vendor, sku, seat_type, of_id,
contract_expiry, notice_deadline, days_until_notice_deadline,
renewal_urgency (expired|critical|high|medium|ok),
auto_renewal (bool), true_down_rights (bool),
current_provisioned, effective_total_seats, exposure_seats,
hires_before_deadline, hires_by_department,
urgency_score, growth_score, exposure_score,
pressure_score, pressure_classification (critical|at-risk|ok),
exit_model_applied, computed_at
```

One row per contract (vendor + sku + seat_type). One vendor may have N rows.

### `GET /forecast/demand`

```
vendor, sku, seat_type, forecast_month,
expected_new_licenses (float), pipeline_data_available (bool),
by_department: [{department, expected_licenses}]   ← currently [] but field exists,
rate_grain_applied ("dept_level" | "dept_only" | "portfolio"),
exit_model_applied (bool), computed_at
```

`by_department` is currently always `[]`. The ForecastView must handle this gracefully
and be built to display it when the forecasting processor is upgraded to sub-department
grain. See expansion hook in ForecastView section.

### `GET /trueup/exposure` and `GET /trueup/breakdown`

```
vendor, sku, seat_type,
exposure_seats, exposure_amount_annual,
shelfware_seats, shelfware_amount_annual,
computed_at
```

---

## A. Backend Additions (two new endpoints)

Add to `api/routers/triggers.py`. No new file — extend the existing router.
Register nothing new in `main.py` — `triggers.router` is already registered.

### `POST /triggers/renewal-alert`

```python
@router.post("/renewal-alert", response_model=TriggerResponse)
def renewal_alert(req: TriggerRequest):
    ctx  = build_context(vendor=req.vendor)
    rows = get_renewal_pressure(ctx)

    expired_rows  = [r for r in rows if r.renewal_urgency == "expired"]
    critical_rows = [r for r in rows if r.pressure_classification == "critical"
                     and r.renewal_urgency != "expired"]
    total_exposure = sum(r.exposure_seats for r in rows)
    count = len(expired_rows) + len(critical_rows)

    if not req.confirmed:
        return TriggerResponse(
            preview=True, vendor=req.vendor, department=req.department,
            count=count, dollar_impact=float(total_exposure),
            message=(f"{len(expired_rows)} expired and {len(critical_rows)} critical "
                     f"contracts for {req.vendor}. {total_exposure} seats over entitlement. "
                     "Confirm to send Slack alert."),
        )

    result = dispatch_slack({
        "vendor":          req.vendor,
        "expired_count":   len(expired_rows),
        "critical_count":  len(critical_rows),
        "total_exposure":  total_exposure,
    })
    rec_id = insert_recommendation({
        "type": "renewal_alert", "vendor": req.vendor,
        "department": None, "affected_records": [],
        "dollar_impact": float(total_exposure),
    })
    return TriggerResponse(
        preview=False, vendor=req.vendor, department=req.department,
        count=count, dollar_impact=float(total_exposure),
        message=result.get("message", "Slack alert dispatched."),
        status="dispatched", integration=result.get("integration"),
        recommendation_id=rec_id, db_status="pending",
    )
```

Import `get_renewal_pressure` from `processing.renewal_pressure_forecaster`.

### `POST /triggers/reclamation-review`

```python
@router.post("/reclamation-review", response_model=TriggerResponse)
def reclamation_review(req: TriggerRequest):
    ctx        = build_context(vendor=req.vendor)
    candidates = get_reclamation_candidates(ctx)
    if req.department:
        candidates = [c for c in candidates if c.get("department") == req.department]

    count         = len(candidates)
    dollar_impact = sum(float(c.get("annual_value", 0)) for c in candidates)

    if not req.confirmed:
        return TriggerResponse(
            preview=True, vendor=req.vendor, department=req.department,
            count=count, dollar_impact=dollar_impact,
            message=(f"Found {count} reclamation candidates worth "
                     f"${dollar_impact:,.0f}/yr. Confirm to create Jira review ticket."),
        )

    result = dispatch_jira({
        "vendor":           req.vendor,
        "candidate_count":  count,
        "dollar_impact":    dollar_impact,
        "type":             "reclamation_review",
        "department":       req.department,
    })
    rec_id = insert_recommendation({
        "type": "reclamation_review", "vendor": req.vendor,
        "department": req.department,
        "affected_records": candidates[:50],   # cap to avoid huge DB rows
        "dollar_impact": dollar_impact,
    })
    return TriggerResponse(
        preview=False, vendor=req.vendor, department=req.department,
        count=count, dollar_impact=dollar_impact,
        message=result.get("message", "Jira review ticket created."),
        status="dispatched", integration=result.get("integration"),
        ticket_id=result.get("ticket_id"),
        recommendation_id=rec_id, db_status="pending",
    )
```

Import `get_reclamation_candidates` from `processing.reclamation_scorer`
(or whichever module the existing `/reclamation` endpoint already imports from —
use the same import).

### Tests

Add to `tests/test_api_triggers.py`:

- `POST /triggers/renewal-alert` `confirmed=false` → `preview: true`, `count >= 0`
- `POST /triggers/renewal-alert` `confirmed=true` → `status: "dispatched"`
- `POST /triggers/reclamation-review` `confirmed=false` → `preview: true`, `count > 0`
- `POST /triggers/reclamation-review` `confirmed=true` → `status: "dispatched"`, `recommendation_id` not None

4 new tests → total **175 passed**.

---

## B. Frontend — Wiring New Trigger Types

The following must be updated before the views that use these types can work.

### `api/triggerClient.js` — add two new paths

```js
const TYPE_TO_PATH = {
  ghost_ticket:       "/triggers/ghost-ticket",
  reclamation:        "/triggers/reclamation",       // CSV export, kept as-is
  reclamation_review: "/triggers/reclamation-review", // ← new: Jira review ticket
  rightsizing:        "/triggers/rightsizing",
  renewal_alert:      "/triggers/renewal-alert",     // ← new: Slack alert
};
```

### `store/useAppStore.js` — widen `PendingConfirm.type`

```ts
// The type discriminator now has 6 values:
type TriggerType =
  | "ghost_ticket"
  | "reclamation"
  | "reclamation_review"   // ← new
  | "rightsizing"
  | "renewal_alert"        // ← new
  | "churn_mail";
```

### `components/shared/InsightBanner.jsx` — widen triggerType union

```ts
triggerType: "ghost_ticket" | "reclamation" | "reclamation_review"
           | "rightsizing"  | "renewal_alert" | "churn_mail" | null;
```

Same change in `TwoActionBanner.jsx`.

### `api/chat.js` — add to planner system prompt

In `buildPlannerSystem`, the available triggers block currently lists 4 types.
Add the two new ones:

```
- renewal_alert(vendor)
    → sends Slack alert for expired/critical contracts; use when user asks to alert,
      notify, or escalate a renewal situation.
- reclamation_review(vendor, department?)
    → creates a Jira review ticket for high-scoring reclamation candidates;
      use when user asks to raise a ticket specifically for reclamation review
      (distinct from ghost_ticket which is for ghost license cleanup).
```

---

## 1. `src/utils/fmt.js` — unchanged from patch-p1

*(no changes — see patch-p1 for full content)*

---

## 2. `src/utils/deriveFilters.js` — unchanged from patch-p1

*(no changes — see patch-p1 for full content)*

---

## 3. `src/store/useAppStore.js` — add `selectedYear` + widen `PendingConfirm.type`

```js
selectedYear: "All",
setYear: y => set({ selectedYear: y }),
```

`PendingConfirm.type` widened as per section B above.

---

## 4. `src/components/shared/FilterBar.jsx` — unchanged from patch-p1

---

## 5. `src/hooks/useTrueUp.js` — unchanged from patch-p1

---

## 6. `src/views/TrueUpView.jsx` — unchanged from patch-p1

---

## 7. `src/components/layout/Sidebar.jsx` — add `trueup` + `pipeline` nav items

Full updated nav order:

```js
const NAV = [
  { id: "overview",        label: "Overview",         icon: "LayoutDashboard" },
  { id: "ghost",           label: "Ghost Licenses",   icon: "Ghost",     badge: ghostTotal },
  { id: "reclamation",     label: "Reclamation",      icon: "RefreshCw", badge: candidateCount },
  { id: "trueup",          label: "True-Up Exposure", icon: "BarChart2"  },
  { id: "utilization",     label: "Utilization",      icon: "PieChart"   },
  { id: "renewal",         label: "Renewal Pressure", icon: "Zap",       badge: expiredCount },
  { id: "forecast",        label: "Demand Forecast",  icon: "TrendingUp" },
  { id: "recommendations", label: "Recommendations",  icon: "Sparkles",  badge: pendingCount },
  { id: "pipeline",        label: "Pipeline",         icon: "GitBranch"  },  // ← new
];
```

`pipeline` is placed last. No badge for V1.

---

## 8. `src/App.jsx` — add `trueup` + `pipeline` to VIEWS map

```js
import TrueUpView    from "./views/TrueUpView";
// PipelineView already exists — just needs to be in the map
import PipelineView  from "./views/PipelineView";

const VIEWS = {
  overview:        OverviewView,
  ghost:           GhostView,
  reclamation:     ReclamationView,
  trueup:          TrueUpView,         // ← new
  utilization:     UtilizationView,
  renewal:         RenewalView,
  forecast:        ForecastView,
  recommendations: RecommendationsView,
  pipeline:        PipelineView,       // ← Phase 2A already implemented
};
```

---

## 9. `src/views/PipelineView.jsx` — one-line addition (health invalidation)

Phase 2A already implemented this view. Only one line needs to be added:
in the success handler where a completed pipeline run is detected, invalidate
the health query so the vendor dropdown in TopBar picks up any newly discovered
vendors without a page reload.

```js
// Add inside the "run completed" success handler in PipelineView.jsx:
queryClient.invalidateQueries({ queryKey: ["health"] });
```

No other changes to `PipelineView.jsx`.

---

## 10. `src/components/layout/TopBar.jsx` — vendor-scoped dept + year filter

Unchanged from patch-p1 logic. Reproduced here for completeness because the
agent needs the `useEffect` for dept reset, which was in patch-p1 but easy to miss.

```jsx
// Department reset when vendor changes:
useEffect(() => {
  setDepartment("All");
}, [vendor]);
```

```jsx
// Only render year select when there are at least 2 years of data:
{availableYears.length > 2 && (
  <select value={selectedYear} onChange={e => setYear(e.target.value)} ...>
    {availableYears.map(y => <option key={y} value={y}>{y === "All" ? "All Years" : y}</option>)}
  </select>
)}
```

---

## 11. `src/views/GhostView.jsx` — accumulation chart + FilterBar

Unchanged from patch-p1. See patch-p1 for full implementation detail.

---

## 12. `src/views/RenewalView.jsx` — banner dedup + correct action types + columns

### Fix 1: Banner grouping (unchanged from patch-p1)

See patch-p1 section 7 "Fix 1" for the `vendorBannerData` derivation logic.
No changes to that code.

### Fix 2 (CORRECTED from patch-p1): TwoActionBanner action types

**patch-p1 was wrong here.** It used `ghost_ticket` + `reclamation` as banner actions.
The correct actions for an expired/critical renewal contract are:

```jsx
// CORRECT:
<TwoActionBanner
  title={`${v.vendor} — ${v.isExpired ? "contract EXPIRED" : "critical renewal pressure"}`}
  body={`${v.totalExposure} seats over entitlement · ${v.totalHires.toFixed(0)} projected hires
         before deadline · pressure score ${(v.maxPressureScore * 100).toFixed(0)}%`}
  actions={[
    {
      label: "Send Slack Alert",
      triggerType: "renewal_alert",          // ← Slack notification about the renewal risk
      data: { vendor: v.vendor },
    },
    {
      label: "Raise Ghost Ticket",
      triggerType: "ghost_ticket",           // ← clean up ghosts on this expired vendor
      data: { vendor: v.vendor },
    },
  ]}
/>
```

**Why `renewal_alert` + `ghost_ticket`:**
- Expired contract → first action is to alert stakeholders via Slack (`renewal_alert`)
- Expired contract + ghost licenses → second action is Jira ghost cleanup (`ghost_ticket`)
- `reclamation` (CSV export) is not a renewal action — it lives on the Reclamation view

### Fix 3: SKU/seat-type FilterBar above table (unchanged from patch-p1)

### Fix 4: Updated DataTable columns (unchanged from patch-p1)

*(see patch-p1 section 7 "Fix 3" for the full 14-column table spec)*

### Fix 5: Summary KPI strip (unchanged from patch-p1)

---

## 13. `src/views/ReclamationView.jsx` — add Raise Jira Review button

Add a fourth action button to the existing three-button row:

```jsx
// BEFORE (3 buttons):
// Export CSV | Send Confirmation Emails | Send Churn Notification

// AFTER (4 buttons):
<button onClick={() => setPendingConfirm({ type:"reclamation",        vendor, department })}>
  Export CSV
</button>
<button onClick={() => setPendingConfirm({ type:"reclamation_review", vendor, department })}>
  Raise Jira Review      {/* ← new */}
</button>
<button onClick={() => setPendingConfirm({ type:"rightsizing",        vendor, department })}>
  Send Confirmation Emails
</button>
<button onClick={() => setPendingConfirm({ type:"churn_mail",         vendor, department })}>
  Send Churn Notification
</button>
```

Styling for "Raise Jira Review": amber filled (same level of urgency as Export CSV but
it's an active dispatch). Use `bg-amber text-black`.

---

## 14. `src/views/ForecastView.jsx` — add `rate_grain_applied` + `by_department` hook

### Demand table: add `rate_grain_applied` column

Updated demand table columns (was 5, now 6):

| Column | Source field | Notes |
|---|---|---|
| Month | `forecast_month` | |
| Vendor | `vendor` | |
| SKU | `sku` | |
| Seat Type | `seat_type` | |
| Expected Licenses | `expected_new_licenses` | 1 decimal |
| Pipeline Data | `pipeline_data_available` | "✓" / "–" in success/dim color |
| Rate Grain | `rate_grain_applied` | **new** — `dept_level`=green, `dept_only`=amber, `portfolio`=red |

Rate grain coloring communicates data quality to the user:
- `dept_level`: full department + job level data available → `text-success`
- `dept_only`: department-only fallback used → `text-amber`
- `portfolio`: portfolio-wide fallback only → `text-danger`

### `by_department` expansion hook

The `by_department` field on each demand row is currently always `[]`.
The ForecastView must be built so it can display this data when the forecasting
processor is upgraded to sub-department grain — without a rewrite.

Implementation: in the demand DataTable, add a `render` function for an
expansion column. When `by_department.length === 0`, render nothing.
When `by_department.length > 0`, render an expand chevron that toggles an
inline sub-row showing the dept breakdown.

```js
// In DataTable columns array for ForecastView:
{
  key: "by_department",
  label: "",
  width: "40px",
  render: (depts, row) => {
    if (!depts?.length) return null;
    // expansion toggle — managed by local state in ForecastView
    return <button onClick={() => toggleExpanded(row.forecast_month + row.sku)}>▾</button>;
  },
}
```

The expansion sub-row content: a small inline table with columns
`Department | Expected Licenses`. This requires a `expandedRows` local state:
```js
const [expandedRows, setExpandedRows] = useState(new Set());
const toggleExpanded = (key) =>
  setExpandedRows(prev => {
    const next = new Set(prev);
    next.has(key) ? next.delete(key) : next.add(key);
    return next;
  });
```

This hook is built but invisible until `by_department` has data. Zero UI change today,
zero code change needed when the processor upgrade arrives.

---

## 15. `src/components/chat/QuickPrompts.jsx` — add trueup + pipeline chips

```js
trueup: [
  "Show true-up exposure by SKU",
  "Which SKUs are over contracted capacity?",
  "Total shelfware cost across vendors",
],
pipeline: [
  "Show last pipeline run status",
  "Which vendors were discovered?",
],
```

---

## Build Order

| Step | Files | Gate |
|------|-------|------|
| 0a | Backend: `api/routers/triggers.py` add `renewal_alert` + `reclamation_review` | `tests/test_api_triggers.py` +4 tests → **175 passed** |
| 0b | Frontend: `api/triggerClient.js` add two new paths | `TYPE_TO_PATH["renewal_alert"]` resolves in console |
| 0c | Frontend: `useAppStore.js` widen `PendingConfirm.type` | TypeScript (or JSDoc) shows no error on new types |
| 0d | Frontend: `InsightBanner.jsx` + `TwoActionBanner.jsx` widen triggerType union | No prop-type warning when passing `renewal_alert` |
| 0e | Frontend: `chat.js` `buildPlannerSystem` add two new trigger descriptions | Done alongside 0b-0d, verify by reading the system prompt string |
| 1 | `src/utils/fmt.js` + `src/utils/deriveFilters.js` | `buildAccumulationSeries` with dummy data → correct cumulative |
| 2 | `src/store/useAppStore.js` add `selectedYear` | `getState().selectedYear === "All"` |
| 3 | `src/components/shared/FilterBar.jsx` | Renders selects with passed options |
| 4 | `src/hooks/useTrueUp.js` add `useTrueUpBreakdown` | Network tab: `GET /trueup/breakdown` on TrueUpView mount |
| 5 | `src/views/TrueUpView.jsx` | 3 KPIs, bar chart, breakdown table, SKU filter works |
| 6 | `src/components/layout/Sidebar.jsx` add `trueup` + `pipeline` items | Both appear in nav, clicking loads correct view |
| 7 | `src/App.jsx` VIEWS map (`trueup`, `pipeline`) | No-op if step 6 correct |
| 8 | `src/views/PipelineView.jsx` add health invalidation | After a completed run, vendor dropdown updates without reload |
| 9 | `src/views/GhostView.jsx` accumulation chart | Chart renders for Atlassify, empty state for vendor with no dated records |
| 10 | `src/components/layout/TopBar.jsx` dept scoping + year filter | Vendor switch → dept resets, dept options match vendor; year select appears when ≥2 years exist |
| 11 | `src/views/RenewalView.jsx` banner dedup + correct action types | Nexaflow → ONE banner; "Send Slack Alert" + "Raise Ghost Ticket" buttons visible |
| 12 | `src/views/RenewalView.jsx` columns + summary KPI strip | 14 columns visible, exposure danger-colored, summary KPIs above banners |
| 13 | `src/views/ReclamationView.jsx` add Raise Jira Review button | Four buttons visible, Raise Jira Review → ConfirmModal with preview |
| 14 | `src/views/ForecastView.jsx` `rate_grain_applied` + expansion hook | Rate grain column visible with color coding; expand chevron hidden when `by_department` is empty |
| 15 | `src/components/chat/QuickPrompts.jsx` trueup + pipeline chips | Correct chips for each view |
| 16 | Full integration pass | All 9 views render · renewal shows 1 banner per vendor with correct action types · reclamation has 4 buttons · trueup filters by SKU · pipeline health invalidation works · 175 tests pass |

---

## What Is NOT in This Patch

| Item | Reason |
|---|---|
| Sub-department level forecasting | Forecasting processor limitation — not a frontend gap. Frontend expansion hook is built (step 14) ready for when the processor is upgraded. |
| SKU filter as backend query param on `/ghost/detail` | Client-side filter is sufficient for V1 |
| True-Up Sidebar badge count | Needs stable query cache before Sidebar renders; Patch P2 |
| Forecast chart year filter | Lower priority; the demand table already shows all months |
| Accumulation chart for records with no `exit_date` | Cannot place on timeline without a date. Patch P2. |
| Per-vendor pressure sparklines on Overview | Phase 2 |

---

*Phase 1E Patch P1 v2 · Primarily frontend · Two backend trigger endpoints required*  
*Backend: `POST /triggers/renewal-alert` + `POST /triggers/reclamation-review` → 175 tests*  
*Frontend: TrueUp view · Pipeline nav · Ghost accumulation · Renewal banner dedup · Correct action types · Forecast rate_grain column · Vendor-scoped depts · Year filter · SKU filters*  
*Phase 2A non-breaking: health query invalidation after pipeline run is the only integration point*
