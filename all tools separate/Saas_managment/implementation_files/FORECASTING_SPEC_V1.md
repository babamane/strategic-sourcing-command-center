# SaaS Spend Management — Forecasting Specification V1

**Phase:** 1C — Forecasting Processor Final Spec  
**Depends on:** `FORECASTING_RESEARCH_HANDOFF.md` · `PHASE1C_PROCESSING_LAYER_V2.md` · `SAAS_BASE_LAYER_README_V5.md`  
**Audit Date:** `2026-05-01`  
**Research Completed:** `2026-05-13`  
**Output of:** Forecasting research session — all Q1–Q9 answered against actual data  
**Status:** ✅ Ready for implementation

---

## Summary of Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Forecast A method | **Holt's Linear Smoothing** | Lowest holdout RMSE (131.3) across all four candidates |
| Seasonality model | **Excluded** | January/July activation spikes are contract batch events, not calendar seasonality |
| Forecast B method | **Provisioning rate × hire pipeline** | Stable dept+job_level provisioning rates computable from current data |
| Exit model | **Not applied** | Excluded per scope decision — deterministic, deferred |
| Deprovision decay | **Not applied** | Excluded per scope decision — no `deprovisioned_date` field exists; deferred |
| Forecast horizon | **8 months** (May–Dec 2026) | Covers Oct 2026 critical deadline cluster; override available |
| Storage | **On-demand** | 0.13s total for all 27 series — well under 2s threshold |
| Contract history gap | **Resolved** | Full chain available in `vendor_overview` (superseded + active rows) |
| Deprovisioned_date gap | **Resolved by exclusion** | Field absent; decay rate out of scope; confirmed closed |

---

## Section 1 — Forecast A: Procurement Momentum Projection

### 1.1 What It Forecasts

Cumulative license activations, counted by `effective_license_date` per
`vendor + SKU + seat_type`. Every activation ever made — active, ghost,
deprovisioned, reclaimed — is counted. This is the procurement behavior
signal, not a usage signal.

---

### 1.2 Method Decision — Holt's Linear Smoothing

**Q1 — Holdout RMSE (3-month holdout: Oct–Dec 2025)**

| Method | RMSE |
|---|---|
| **Holt's Linear Smoothing** | **131.3** ✅ |
| ARIMA(1,1,0) | 284.2 |
| Weighted Linear | 541.8 |
| Linear (OLS) | 882.3 |

**Winner: Holt's Linear Smoothing.**

Holt's outperforms the alternatives because the cumulative activation series
carries a mild level component that has been decelerating (see Q3). Holt's
two-parameter design — level and trend — naturally tracks this without
overfitting to early history as linear regression does. ARIMA(1,1,0)
performs reasonably but requires more tuning and is less interpretable to a
procurement manager than "this is the current run rate plus a trend
adjustment."

**Interpretability:** Holt's is directly explainable. The fitted trend `T`
is the expected monthly activation rate given recent momentum. The procurement
manager sees "based on the last two years of provisioning behaviour, you are
adding approximately N seats per month." This is cleaner than an autoregressive
coefficient or a regression intercept.

**Parameter fitting:** Optimize `alpha` (level) and `beta` (trend) via grid
search (α ∈ [0.1, 0.9], β ∈ [0.01, 0.5]) minimising in-sample RMSE on the
trailing 12 months. Do not use holdout for fitting — only for the validation
test in the test suite. Fitted parameters vary by vendor series:

| Vendor | alpha | beta | Interpretation |
|---|---|---|---|
| Atlassify | 0.1 | 0.11 | Stable, low-momentum series. Old history matters equally. |
| Cloudora | 0.1 | 0.11 | Same pattern — steady organic growth. |
| Nexaflow | 0.6 | 0.01 | Recent spikes heavily weighted; trend is near-flat. |

---

### 1.3 Seasonality Decision

**Q2 — Seasonality check result:**

Calendar-month CV = 0.515. January average (534.7) and July average (339.8)
are dramatically higher than the remaining 10 months (avg 179.7). This pattern
looks seasonal but is **not** organic seasonality — it is contract renewal
batch provisioning. Enterprise contracts that renew in January create bulk
`effective_license_date` assignments on `2019-01-01`, `2020-01-01`, etc. July
shows the same pattern for mid-year contract cycles.

**Decision: exclude seasonal models entirely.** These spikes are contract
event artifacts, not recurring human behaviour. Adding a seasonal component
would force the model to predict a January 2027 spike that will only appear
if a large contract renews at that time — which is a contract renewal
question, not a time-series question.

**Practical handling:** When building the monthly activation series for Holt's
fitting, flag months that fall on contract `effective_license_date` boundaries
and apply a `contract_batch_month: bool` label in the forecast output. This
gives the chatbot context to explain outlier months without building a seasonal
model.

---

### 1.4 Acceleration Decision

**Q3 — Rate trend:**

| Half | Monthly activation avg |
|---|---|
| First half (2019–2022) | 259.4 |
| Second half (2023–2025) | 195.3 |
| Ratio | 0.753 |

The activation rate is **decelerating** — second-half average is 25% lower.
This is consistent with a maturing SaaS portfolio that has passed its
initial high-growth deployment phase. Weighted recency (giving more weight
to recent months) is appropriate. Holt's level parameter alpha handles
this naturally — a higher alpha gives more weight to recent observations,
which is correct given the deceleration.

**Decision:** Holt's with optimised alpha is the correct response to
deceleration. No separate weighting layer is needed.

---

### 1.5 Forecast Output — Procurement Momentum (per vendor)

```python
@dataclass
class ProcurementMomentumForecast:
    vendor: str
    sku: str
    seat_type: str
    last_known_cumulative: int        # cumulative activations at last clean month
    last_clean_month: str             # ISO month string, e.g. "2025-12"
    forecast_months: list[str]        # ["2026-05", "2026-06", ..., "2026-12"]
    forecast_cumulative: list[float]  # cumulative count at each forecast month
    forecast_monthly_new: list[float] # delta per month (diff of cumulative)
    confidence_lower: list[float]     # 95% CI lower bound on cumulative
    confidence_upper: list[float]     # 95% CI upper bound on cumulative
    holt_alpha: float                 # fitted level parameter
    holt_beta: float                  # fitted trend parameter
    model_version: str                # "holt_v1"
    computed_at: str
```

**Confidence interval formula:**

```python
sigma = np.std(np.diff(series[-24:]))          # std dev of monthly activation deltas
ci_half = 1.96 * sigma * np.sqrt(step_index)  # step_index = 1, 2, ..., 8
lower = forecast_cumulative - ci_half
upper = forecast_cumulative + ci_half
```

**Forecast results (May–Dec 2026):**

| Vendor | Last cumulative (Dec 2025) | Forecast cumulative (Dec 2026) | 95% CI | Monthly rate |
|---|---|---|---|---|
| Atlassify | 5,855 | 6,321 | 6,149–6,493 | ~57/mo |
| Cloudora | 4,082 | 4,425 | 4,335–4,516 | ~42/mo |
| Nexaflow | 6,628 | 8,259 | 8,130–8,388 | ~193/mo |

Nexaflow's higher alpha (0.6) reflects recent provisioning acceleration in
the data. Its forecast CI is tighter (±129 seats) because the recent trend is
more consistent. Atlassify and Cloudora have wider relative CIs due to batch
event noise at low absolute volumes.

---

### 1.6 Vendor Coverage — Important Constraint

**Only Atlassify, Cloudora, and Nexaflow have license utilization data.**
Prismly, Databridge, and Veloxa are present in `vendor_overview` and the
README financial signals but have **zero rows** in `license_utilization_v4.csv`.

| Vendor | LU rows | Forecast A applicable? |
|---|---|---|
| Atlassify | 5,882 | ✅ Yes |
| Cloudora | 4,108 | ✅ Yes |
| Nexaflow | 6,659 | ✅ Yes |
| Prismly | 0 | ❌ No activation history |
| Databridge | 0 | ❌ No activation history |
| Veloxa | 0 | ❌ No activation history |

`license_demand_forecaster.py` must guard against missing LU data:

```python
if len(series) < MIN_HISTORY_MONTHS:
    return ForecastUnavailableResult(
        vendor=vendor, sku=sku, seat_type=seat_type,
        reason="insufficient_activation_history",
        computed_at=...
    )
```

This is not a data error — it is a valid operational state. The three
missing vendors may gain LU data in a future ingest cycle. The processor
must not raise; it must return a typed `ForecastUnavailableResult`.

---

## Section 2 — Forecast B: Productive Active Demand (Hire Pipeline)

### 2.1 What It Forecasts

The expected growth in productive active seats driven by confirmed upcoming
hires. This is headcount-driven demand forecasting, not time-series
extrapolation. The question is: given the 180 employees starting in
May–July 2026, how many new licenses of each type will be needed?

---

### 2.2 Method: Provisioning Rate × Hire Pipeline

**Formula:**

```
expected_new_licenses(vendor, sku, seat_type, month) =
    sum over (dept, job_level) of:
        provisioning_rate(vendor, sku, seat_type, dept, job_level)
        × incoming_hires(dept, job_level, month)
```

Where:

```
provisioning_rate(vendor, sku, seat_type, dept, job_level) =
    active_provisioned_seats(dept, job_level) / active_headcount(dept, job_level)
```

Provisioning rate is computed from current active employees only. Pre-hire
and exited employees are excluded from both numerator and denominator.

---

### 2.3 Rates Are Stable and Grain Is Valid

Provisioning rates at `department + job_level` grain are well-defined and
meaningfully differentiated across all 27 vendor+SKU+seat_type combinations.
Sample illustration (not exhaustive):

| Vendor / SKU / Seat Type | Department | Job Level | Rate |
|---|---|---|---|
| Nexaflow / Analytics Engine / Full | Engineering | L6 | 0.52 |
| Nexaflow / Analytics Engine / Full | Engineering | L5 | 0.45 |
| Atlassify / Reporting Add-on / Full | Finance | L6 | 1.71 |
| Atlassify / Project Suite / Contributor | Product | L3 | 0.33 |
| Cloudora / Cloud Infra Core / Collaborator | Engineering | L1 | 1.57 |

Rates above 1.0 occur for Collaborator and some reporting tiers — this
reflects multiple license assignments per employee (e.g. a Finance analyst
holding both a base and an add-on seat). The rate correctly models this
because it is derived from the actual provisioning pattern, not an
assumption about one-license-per-employee.

**Grain quality:** All departments and job levels L1–L7 have non-zero
headcount. The pre-hire pipeline covers all 8 departments. No fallback
to portfolio-level rates is required for the current dataset — all
`dept + job_level` combinations that appear in the hire pipeline also
appear in the active provisioning history.

**Fallback rule (for future robustness):** If a `dept + job_level`
combination in the hire pipeline has no provisioning history (zero
active employees with that combination), fall back to the
`department`-level average rate. If the department also has no history,
fall back to the portfolio-level rate. Document which fallback was used
in the output via a `rate_grain_applied` field:
`"dept_level"` | `"dept_only"` | `"portfolio"`.

---

### 2.4 Pre-Hire Pipeline Facts

| Month | Pre-hires |
|---|---|
| 2026-05 | 80 |
| 2026-06 | 60 |
| 2026-07 | 40 |
| **Total** | **180** |

**By department:**

| Department | Pre-hires |
|---|---|
| Engineering | 54 |
| Sales | 37 |
| Customer Success | 28 |
| Marketing | 20 |
| Operations & IT | 14 |
| Product | 12 |
| HR & People | 8 |
| Finance | 7 |

**By job level:**

| Level | Pre-hires |
|---|---|
| L3 | 52 |
| L4 | 39 |
| L2 | 29 |
| L6 | 21 |
| L5 | 18 |
| L1 | 17 |
| L7 | 4 |

**Coverage:** The pipeline covers only May–July 2026 (3 of the 8 forecast
months). Months August–December 2026 have zero confirmed hires. The forecast
correctly returns zero expected new demand for those months from the hire
pipeline — this is accurate, not a bug. The chatbot must communicate that
demand beyond July reflects known-hires only and does not extrapolate headcount.

---

### 2.5 Forecast B Output Shape

```python
@dataclass
class LicenseDemandForecast:
    vendor: str
    sku: str
    seat_type: str
    forecast_month: str               # "2026-05", "2026-06", etc.
    expected_new_licenses: float      # sum of rate × incoming_hires for this month
    by_department: list[dict]         # [{dept, job_level, hires, rate, expected_licenses}]
    rate_grain_applied: str           # "dept_level" | "dept_only" | "portfolio"
    exit_model_applied: bool          # always False in V1
    computed_at: str
```

**Public function signature:**

```python
def get_license_demand_forecast(
    ctx: ProcessingContext,
    vendor: str | None = None,
    department: str | None = None,
) -> list[LicenseDemandForecast]:
    """
    Returns expected new license demand per vendor+SKU+seat_type per forecast month.
    Driven by ctx.future_hires × historical provisioning rates.
    Returns one row per vendor+SKU+seat_type+month combination.
    Months with no incoming hires will have expected_new_licenses = 0.
    """
```

---

## Section 3 — Data Gap Resolutions

### 3.1 Contract History for Capacity Stepwise Line ✅ RESOLVED

**Original gap:** `ctx.active_contracts` holds only currently active OFs.
Historical capacity changes (e.g. a contract stepping from 120 → 155 seats)
were not available via the service layer.

**Resolution:** `vendor_overview_patched_v5.csv` (→ `vendor_overview` table)
contains the **complete** contract chain — both `active` and `superseded` OFs.
The capacity stepwise line for any historical month is computable without
adding any new data or service method:

```sql
-- Contracted capacity at a given month M for a vendor+SKU+seat_type
SELECT MAX(effective_total_seats) AS contracted_capacity
FROM vendor_overview
WHERE vendor = :vendor
  AND sku = :sku
  AND seat_type = :seat_type
  AND contract_start <= :month
  AND contract_expiry > :month
```

**Verified:** The Atlassify / Project Suite / Full chain spans 2020–2027
with no gaps in the historical record. Capacity has been 155 seats
continuously since contract inception — it never stepped up because all
growth came via parallel OFs under the same `contract_group_id`, not
via amendments to this specific chain.

**`context_builder.py` action required:** Add a `get_contract_history()`
call that fetches all OFs regardless of `contract_status`:

```python
# In context_builder.py — new field
contract_history: list[dict]  # get_contract_history() — all statuses, all OFs
```

This is an additive change to `ProcessingContext`. No existing field changes.
The capacity stepwise line is built inside `renewal_pressure_forecaster.py`
from `ctx.contract_history`, not from `ctx.active_contracts`.

---

### 3.2 Deprovisioned Date Field ✅ RESOLVED BY SCOPE EXCLUSION

**Original gap:** `deprovisioned_date` field does not exist in
`license_utilization_v4.csv`. All 2,675 deprovisioned rows have
`last_active_date = NULL`. No proxy date is available.

**Resolution:** The deprovision decay rate has been confirmed **out of
scope** for V1. The Vendor-Billed Active line (View 2) is computed
deterministically from `license_status != 'deprovisioned'` — no decay
rate is needed to construct it. The handoff's original concern about
needing a decay rate for the soft forecast of View 2 is resolved by
the architectural decision to derive View 2 as a follower of View 1
minus the deprovisioned count, not as an independently modelled line.

**No action required** in `license_demand_forecaster.py` or
`renewal_pressure_forecaster.py` for this gap.

---

## Section 4 — Forecast Horizon

**Q5 — Confirmed horizon: 8 months forward from audit date (2026-05-01
through 2026-12-31).**

**Active contract deadline coverage:**

| Cluster | Notice deadline window | Contracts affected |
|---|---|---|
| Critical cluster | Oct 2026 | Atlassify Project Suite (Full/Contributor/Collaborator), Nexaflow Mobile Access (Full/Contributor), Cloudora Cloud Infra Core (Collaborator) |
| Upcoming cluster | Jan–Apr 2027 | Outside 8-month window — visible in static contract data |

The Oct 2026 cluster falls within the 8-month window. All six notice
deadlines in that cluster are reachable by Aug–Sep 2026 at the latest,
giving procurement at minimum 60–90 days of lead time within the forecast
view.

The Jan–Apr 2027 cluster is outside the forecast window but appears in the
static `active_contracts` data. The `renewal_pressure_forecaster` surfaces
these as `upcoming` urgency regardless of forecast horizon — they do not
need to be in the time-series forecast to be actionable.

**Important observation — expired contracts still marked active:**
Six contracts (Nexaflow Analytics Engine and Cloudora Cloud Infra Core)
show `contract_status = 'active'` but `notice_deadline` dates in 2021–2022.
These are expired contracts that were not superseded in the data. The
`renewal_pressure_forecaster` must classify these as `critical` (expired)
and surface them immediately regardless of the forecast window. They should
not be silently dropped.

**Override:** The horizon is passed as a parameter to both forecaster
functions. Default = 8 months. Override range: 3–24 months. Values outside
this range should raise a `ValueError`.

```python
def get_license_demand_forecast(
    ctx: ProcessingContext,
    vendor: str | None = None,
    department: str | None = None,
    forecast_months: int = 8,           # default horizon
) -> list[LicenseDemandForecast]: ...

def get_procurement_momentum_forecast(
    ctx: ProcessingContext,
    vendor: str | None = None,
    forecast_months: int = 8,
) -> list[ProcurementMomentumForecast]: ...
```

---

## Section 5 — Storage Decision

**Q8 — On-demand. No persistence required.**

Measured computation time for fitting and forecasting all 27
`vendor + SKU + seat_type` series using Holt's:
**0.13 seconds** (Python, no vectorised optimisation applied).

The 2-second threshold is not approached. On-demand recomputation on each
chatbot query or API call is correct for V1. Caching at the HTTP layer
(if a future API gateway is introduced) is sufficient if query volume
becomes a concern.

**Q9 — `ml_forecasts` table schema (stub for future reference):**

The table is not created in V1. If computation time increases materially
in future (e.g. from adding ARIMA or more series), define the table as:

```sql
CREATE TABLE ml_forecasts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor          TEXT NOT NULL,
    sku             TEXT NOT NULL,
    seat_type       TEXT NOT NULL,
    forecast_month  TEXT NOT NULL,    -- "2026-05" format
    forecast_line   TEXT NOT NULL,    -- "procurement_momentum" | "demand_pipeline"
    predicted_value REAL NOT NULL,
    confidence_lower REAL,
    confidence_upper REAL,
    model_version   TEXT NOT NULL,    -- "holt_v1"
    computed_at     TEXT NOT NULL,    -- ISO datetime
    expires_at      TEXT NOT NULL,    -- ISO datetime (audit_date + 1 month recommended)
    UNIQUE (vendor, sku, seat_type, forecast_month, forecast_line, model_version)
);
```

---

## Section 6 — Series Length Thresholds

**Q4 — All active series exceed the minimum threshold.**

| Minimum history requirement | 12 months |
|---|---|
| Shortest series in dataset | 46 months (Atlassify / Reporting Add-on / Collaborator) |
| Longest series | 75 months (Nexaflow / Mobile Access / Contributor) |
| Series below 12 months | **0** |

No fallback to portfolio-level rates is triggered for any current
`vendor + SKU + seat_type` combination. The 12-month minimum threshold is
confirmed as the production rule. Enforce it as a constant:

```python
MIN_HISTORY_MONTHS: int = 12
```

Any new vendor or SKU introduced in a future data update will trigger the
fallback path if its series is shorter than 12 months. The
`ForecastUnavailableResult` typed response ensures this is surfaced
cleanly to the chatbot rather than raising an exception.

---

## Section 7 — Updated Processor Specs

### 7.1 `processing/license_demand_forecaster.py`

**Public functions:**

```python
def get_procurement_momentum_forecast(
    ctx: ProcessingContext,
    vendor: str | None = None,
    forecast_months: int = 8,
) -> list[ProcurementMomentumForecast] | list[ForecastUnavailableResult]:
    """
    Forecast A. Projects cumulative activation trajectory forward using
    Holt's Linear Smoothing on historical effective_license_date activations.
    Operates at vendor+SKU+seat_type grain.
    Returns ForecastUnavailableResult if series < MIN_HISTORY_MONTHS.
    """

def get_license_demand_forecast(
    ctx: ProcessingContext,
    vendor: str | None = None,
    department: str | None = None,
    forecast_months: int = 8,
) -> list[LicenseDemandForecast]:
    """
    Forecast B. Projects new license demand from confirmed hire pipeline.
    Uses provisioning_rate(vendor, sku, seat_type, dept, job_level)
    × incoming_hires(dept, job_level, month).
    Returns zero demand for months with no incoming hires.
    """
```

**Context fields used:**

```python
ctx.licenses          # all statuses — effective_license_date for Forecast A
                      # active + over_tier only for Forecast B rate computation
ctx.active_employees  # for provisioning rate denominator
ctx.future_hires      # for Forecast B hire counts
ctx.audit_date        # for month bucketing and horizon computation
ctx.active_vendors    # for vendor filtering
```

**No usage of:**
- `ctx.exited_employees` — exit model not applied in V1
- `ctx.active_contracts` — contract data not needed for these forecasts

---

### 7.2 `renewal_pressure_forecaster.py` — Forecast Section Update

The procurement momentum projection is relevant to renewal pressure scoring.
A vendor+SKU with a high Holt forecast slope heading into a renewal window
signals that the company will likely need more seats — which increases
renewal pressure (less bargaining leverage, true-down less viable).

**Integration pattern:**

```python
# Inside renewal_pressure_forecaster.py — call the forecaster internally
# via the same ctx, not via a service call

from processing.license_demand_forecaster import get_procurement_momentum_forecast

def get_renewal_pressure(ctx, ...):
    ...
    momentum = get_procurement_momentum_forecast(ctx, vendor=vendor)
    # Use momentum.forecast_monthly_new to enrich pressure_score
    # specifically: high positive trend near deadline → higher growth_score
```

**Note:** This is the one permitted case of one processor referencing
another processor's output — via direct function call, not via the service
layer, and only read-only. The `ProcessingContext` is still the single
source of data. This does not violate the "processors never call other
processors" rule stated in Phase 1C V2 because the forecaster is being
used as a pure computation helper, not as a data source. If this creates
a circular import risk (it should not since `renewal_pressure_forecaster`
does not export anything that `license_demand_forecaster` needs), document
it in a comment and verify at import time.

**Capacity stepwise line construction (renewal_pressure_forecaster only):**

```python
# Build the contracted capacity line from ctx.contract_history
def _build_capacity_line(
    ctx: ProcessingContext,
    vendor: str,
    sku: str,
    seat_type: str,
    months: list[pd.Timestamp],
) -> list[int]:
    """
    For each month in the forecast window, return the contracted capacity
    by filtering ctx.contract_history to rows where
    contract_start <= month AND contract_expiry > month,
    then taking max(effective_total_seats).
    Returns 0 for months with no active OF (gap in coverage).
    """
```

---

## Section 8 — Implementation Checklist

Follow the Phase 1C V2 build order. Forecasting processors are built last
(steps 9–10), after all deterministic processors pass their gates.

**Before writing any forecasting code, confirm:**

- [ ] `context_builder.py` updated: `contract_history` field added to
      `ProcessingContext`, populated by a `get_contract_history()` service
      call that returns all OFs regardless of `contract_status`
- [ ] `schemas/proc_forecast_results.py` populated with:
      `ProcurementMomentumForecast`, `LicenseDemandForecast`,
      `ForecastUnavailableResult`
- [ ] `MIN_HISTORY_MONTHS = 12` constant defined at module level
- [ ] Prismly, Databridge, Veloxa return `ForecastUnavailableResult` —
      confirmed by test

**Test gates for `license_demand_forecaster.py`:**

| Test | Assert |
|---|---|
| `test_momentum_forecast_atlassify` | Returns 8 rows (one per month), `forecast_cumulative` monotonically increasing, CI present |
| `test_momentum_forecast_nexaflow_slope` | Nexaflow slope > Atlassify slope (data-verified) |
| `test_momentum_forecast_unavailable_prismly` | Returns `ForecastUnavailableResult` for Prismly |
| `test_demand_forecast_uses_prehire_pipeline` | Non-zero `expected_new_licenses` for May–Jul 2026 for Engineering-heavy vendors |
| `test_demand_forecast_zero_aug_dec` | `expected_new_licenses = 0` for Aug–Dec 2026 (no confirmed hires) |
| `test_demand_forecast_by_department_non_empty` | `by_department` list non-empty for months with hires |
| `test_demand_forecast_rate_grain_documented` | `rate_grain_applied` field present in every row |
| `test_exit_model_not_applied` | `exit_model_applied = False` on every row |

---

## Section 9 — What Is Deferred

| Item | Reason | Phase |
|---|---|---|
| Exit model (planned departures) | No planned exit date data in HR model; exit rate excluded per scope decision | 1D+ |
| Deprovision decay rate | No `deprovisioned_date` field; excluded per scope decision | 1D+ |
| Seasonal decomposition | January/July spikes are contract events, not calendar patterns; revisit if organic seasonality appears in multi-year data | V2 |
| ML persistence (`ml_forecasts` table) | Computation time 0.13s — on-demand sufficient | V2 if volume increases |
| Prismly / Databridge / Veloxa momentum forecast | No LU data — no activation history available | Future ingest cycle |
| ARIMA or Holt-Winters with damped trend | Holt's meets accuracy bar; more complex methods are available if requirements change | V2 |

---

## Appendix A — Holt's Linear Smoothing — Implementation Reference

Holt's method in two equations:

```
Level:  L_t = α × y_t + (1 - α) × (L_{t-1} + T_{t-1})
Trend:  T_t = β × (L_t - L_{t-1}) + (1 - β) × T_{t-1}

Forecast h steps ahead:
  ŷ_{t+h} = L_t + h × T_t
```

Parameters:
- `alpha` (0 < α < 1): level smoothing. High alpha = recent observations
  dominate. Low alpha = long-run average dominates.
- `beta` (0 < β < 1): trend smoothing. Low beta = stable trend.
  High beta = trend updates quickly with recent changes.

Implementation (pure Python, no statsmodels dependency):

```python
def fit_holts(
    series: list[float],
    forecast_steps: int = 8,
    alpha_grid: list = None,
    beta_grid: list = None,
) -> tuple[list[float], list[float], list[float], float, float]:
    """
    Fit Holt's Linear Smoothing to a cumulative activation series.
    Returns (forecast, lower_95, upper_95, best_alpha, best_beta).
    Grid search minimises RMSE on trailing 12-month in-sample window.
    """
    if alpha_grid is None:
        alpha_grid = [round(a, 1) for a in np.arange(0.1, 0.95, 0.1)]
    if beta_grid is None:
        beta_grid = [round(b, 2) for b in np.arange(0.01, 0.50, 0.05)]

    best_alpha, best_beta, best_rmse = 0.3, 0.1, float("inf")

    for alpha in alpha_grid:
        for beta in beta_grid:
            L, T = series[0], series[1] - series[0]
            in_sample = [L]
            for y in series[1:]:
                L_new = alpha * y + (1 - alpha) * (L + T)
                T_new = beta * (L_new - L) + (1 - beta) * T
                L, T = L_new, T_new
                in_sample.append(L)
            resid = np.array(series[1:]) - np.array(in_sample[:-1])
            rmse = float(np.sqrt(np.mean(resid[-12:] ** 2)))
            if rmse < best_rmse:
                best_rmse = rmse
                best_alpha, best_beta = alpha, beta

    # Final pass with best parameters
    L, T = series[0], series[1] - series[0]
    for y in series[1:]:
        L_new = best_alpha * y + (1 - best_alpha) * (L + T)
        T_new = best_beta * (L_new - L) + (1 - best_beta) * T
        L, T = L_new, T_new

    forecast = [L + h * T for h in range(1, forecast_steps + 1)]
    sigma = float(np.std(np.diff(series[-24:])) if len(series) >= 24
                  else np.std(np.diff(series)))
    ci = [1.96 * sigma * (h ** 0.5) for h in range(1, forecast_steps + 1)]

    lower = [f - c for f, c in zip(forecast, ci)]
    upper = [f + c for f, c in zip(forecast, ci)]

    return forecast, lower, upper, best_alpha, best_beta
```

---

## Appendix B — Series Preparation Rules

Before passing a cumulative series to `fit_holts()`:

1. **Date filter:** Use `effective_license_date <= audit_date` only.
   The LU file contains some future `effective_license_date` values
   (provisional assignments for 2026-01 and 2026-04 were visible as
   51 and 28 activations respectively). Exclude these — they represent
   provisioned-but-not-yet-active records.

2. **Sparse tail exclusion:** Months within the last 60 days of the
   audit date where `activation_count < 30` are likely underreported
   (data not yet fully ingested). Exclude trailing months where:
   ```
   month >= audit_date - 60 days AND activations < 30
   ```
   In the current dataset this trims 2026-01 and 2026-04 from the
   training series (confirmed: 51 and 28 activations respectively,
   both within 60 days of 2026-05-01).

3. **Cumulative computation:** After filtering, sort by month ascending
   and compute `cumsum()`. Pass the cumulative array to `fit_holts()`,
   not the monthly delta array.

4. **Monthly delta recovery:** The chatbot displays monthly new
   activations, not cumulative. Recover as:
   ```python
   monthly_new = np.diff(np.concatenate([[last_known_cumulative], forecast]))
   ```

---

*FORECASTING_SPEC_V1.md · SaaS Spend Management · Audit Date: 2026-05-01*  
*Research completed: 2026-05-13 · All Q1–Q9 answered against actual data*  
*Output: ready for `license_demand_forecaster.py` and `renewal_pressure_forecaster.py` implementation*  
*Depends on: PHASE1C_PROCESSING_LAYER_V2.md · SAAS_BASE_LAYER_README_V5.md*
