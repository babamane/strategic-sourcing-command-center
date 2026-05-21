# SaaS Spend Management — Forecasting Research & Finalization Handoff

**Session type:** Research & design finalization — no code in this session  
**Depends on:** Phase 1C architecture finalized (PHASE1C_PROCESSING_LAYER_V2.md)  
**Output of this session:** `FORECASTING_SPEC_V1.md` — finalized forecasting
processor spec ready to implement  
**Audit Date:** `2026-05-01`

---

## Why This Session Exists

The forecasting processor (`license_demand_forecaster.py` and the forecasting
dimension of `renewal_pressure_forecaster.py`) is the most complex and
research-dependent part of Phase 1C. The other six processors — ghost detector,
reclamation detector, trueup, breakdown enricher, utilization aggregator — are
deterministic joins and aggregations. They can be built directly from the spec.

Forecasting is different. It requires decisions on:

- Which time-series method to use for procurement momentum projection
- How to handle sparse data at the department+job_level grain
- Whether to build a multi-line model or a single composite line
- How confidence intervals are expressed and carried through to the chatbot
- How the forecast output is stored and versioned for reuse

These decisions need to be made once, clearly, before implementation. This
document is the input to that research session.

---

## What We Are Trying to Show

The dashboard image and the discussion in this session established a 3-layer
license state decomposition model. Every line is derived from the same
provisioning history but viewed through a different operational filter.

---

### The 3 Core Views

All derived from `effective_license_date` plus state transitions.

---

#### View 1 — Procurement Momentum (Cumulative Activations)

**Question it answers:** How many licenses has procurement historically
accumulated and where is that heading?

**What is included:**
- active licenses
- ghost licenses
- deprovisioned licenses
- reclaimed licenses

**Why:** Every activation was once a provisioning decision. Deprovisioned seats
still represent procurement behavior — they were bought. Including them gives
the true procurement expansion signal.

**Construction:** `cumulative_activations(month)` using `effective_license_date`
only. Count every license ever activated, bucketed by its effective start month.

**Forecast:** Yes — project forward using historical activation slope /
cumulative trend. This is procurement behavior forecasting, not usage
forecasting.

---

#### View 2 — Vendor-Billed Active (Financial Liability)

**Question it answers:** What is the vendor actually billing us for right now
and historically?

**What is included:**
- productive active licenses
- ghost licenses

**What is excluded:**
- deprovisioned licenses

**Why:** Ghosts are still billed. Deprovisioned are not. This is the financial
liability line.

**Formula:** `license_status != 'deprovisioned'`

**Forecast:** Soft only — derived from the difference between procurement
momentum and expected deprovisionings. Not independently forecasted. The
dashboard can project it as a follower of the procurement momentum line with
a deprovision decay applied.

**Key threshold comparison:**
```
vendor_billed_active vs contracted_capacity → true-up exposure
```

---

#### View 3 — Productive Active Usage (Real Utilization)

**Question it answers:** What seats are actually being used by active employees?

**What is included:**
- active employee licenses only

**What is excluded:**
- ghost licenses
- deprovisioned licenses

**Formula:**
```
employee_status = 'active'
AND license_status != 'ghost'
AND license_status != 'deprovisioned'
```

**Forecast:** Yes — project forward using future hire pipeline
(`get_future_hires()`) plus provisioning rate applied per
`department + job_level`. This is demand forecasting from known headcount.

**Key threshold comparison:**
```
productive_active vs contracted_capacity → operational efficiency gap
```

---

#### View 4 — Ghost Accumulation (Leakage Trend)

**Question it answers:** How much financial leakage is accumulating from
deprovisioning failures?

**Construction:** At each employee exit, one seat transitions from
productive_active to ghost. Ghost accumulation is the running total of
unlicensed-but-billed seats that have not been deprovisioned.

**Ghost detection logic (confirmed):**
A license is a ghost if and only if BOTH conditions are true:
```
license_status = 'ghost'
AND employee exit_date IS NOT NULL
```
Both conditions required — belt and suspenders. Later iterations can relax
this but for now both must be present to confirm a ghost.

**Forecast:** No. Future ghosting is operationally unpredictable —
it depends on future offboarding failures which have no leading indicator.
Ghost line is historical only. Stops at audit date.

---

### The Two Threshold Comparisons the Chart Must Support

| Comparison | Formula | What it reveals |
|---|---|---|
| A — Financial exposure | vendor_billed_active vs contracted_capacity | True-up risk |
| B — Operational efficiency | productive_active vs contracted_capacity | Utilisation gap |

Both comparisons must be computable at any filter grain:
`vendor + SKU + seat_type + department + job_level`.

---

### The Executive Story the 4 Lines Tell Together

| Line | Meaning | Forecasted? |
|---|---|---|
| Procurement Momentum | How aggressively seats are provisioned | Yes — activation slope |
| Vendor-Billed Active | What vendor charges for | Soft — derived |
| Productive Active | What employees truly use | Yes — hire pipeline |
| Ghost Accumulation | Financial leakage | No — historical only |
| Contracted Capacity | True-up threshold | No — stepwise on contract events |

The gap between **Productive Active** and **Vendor-Billed Active** = waste
(ghosts).
The gap between **Vendor-Billed Active** and **Contracted Capacity** = true-up
exposure.
The gap between **Procurement Momentum** and **Productive Active** =
provisioning inefficiency.

These three gaps are the core procurement intelligence this platform exists to
surface.

---

## What the Forecasting Processor Must Produce

Two distinct forecast outputs are needed. They are different in method,
grain, and consumer.

---

### Forecast Output A — Procurement Momentum Projection

**What it is:** A forward projection of cumulative license activations based
on historical provisioning behavior.

**Method family:** Time-series extrapolation on cumulative activation counts.
Candidate methods to evaluate during research:

- **Linear trend** — simplest, interpretable, works well if activation rate
  is stable. Baseline to beat.
- **Weighted linear trend** — recent months weighted more heavily. Better if
  procurement pace is accelerating.
- **Holt's linear smoothing (double exponential)** — handles trend without
  seasonality. Reasonable default for SaaS provisioning which typically has
  no seasonal pattern.
- **ARIMA(1,1,0)** or **ARIMA(0,1,1)** — handles autocorrelation in
  cumulative series. Worth evaluating but may be overfit for a 2-year
  history.

**Research question A1:** Which method produces the most stable and
interpretable forecast on the existing activation history? Run all four on
the actual data and compare residuals and forecast intervals.

**Research question A2:** What is the right forecast horizon? The dashboard
shows through Dec 2026 (~8 months forward from audit date). Is this the right
default? Consider: notice deadlines are typically 30–90 days. Renewal cycles
are 12 months. An 8–12 month horizon appears correct but confirm.

**Input data:** `effective_license_date` for every license ever activated —
all statuses. Bucket by month. Build the cumulative series.

**Output grain:** Monthly forecast values at the portfolio level. Then broken
down by `vendor + SKU + seat_type` for filtered views. Department-level
procurement momentum is secondary — useful but not required for V1.

**Confidence expression:** Upper and lower band at 80% confidence. The
dashboard renders these as a shaded region around the dashed forecast line.
The chatbot expresses this as a range: "between 195 and 231 seats by December
2026."

---

### Forecast Output B — Productive Active Demand Projection

**What it is:** A forward projection of expected productive license usage
driven by the known pre-hire pipeline plus historical provisioning rates.

**Method:** Deterministic with a stochastic component — not pure time-series.

**Two-component model:**

Component 1 — **Hire-driven demand** (deterministic):
```
for each pre-hire in get_future_hires():
    expected_new_licenses += provisioning_rate[
        vendor, sku, seat_type, department, job_level
    ]
```
This is the `license_demand_forecaster` output already defined in Phase 1C.
Fully deterministic from known hire pipeline. No uncertainty beyond the
provisioning rate estimate.

Component 2 — **Baseline trend continuation** (stochastic):
Beyond the pre-hire window (post-July 2026), extend using the historical
productive active growth rate. This is where the time-series method applies.
Candidate: weighted linear extrapolation of the last 6 months of productive
active growth. Simple and defensible.

**Combining the two components:**
```
forecast_productive_active(month) =
    current_productive_active
    + hire_driven_additions(through month)
    - expected_deprovision_rate × months_elapsed   ← see research Q B2
    + baseline_trend(month)                         ← post-hire-window only
```

**Research question B1:** What is the right deprovision rate to apply?
Historical data shows how many seats get deprovisioned per month on average.
Use that rate as a decay factor on the productive active line going forward.
Confirm whether this rate is stable or varies by vendor.

**Research question B2:** How to handle the `exit_model_applied: False` gap?
Currently the forecast does not subtract expected future exits. Two options:
- Keep `exit_model_applied: False` and document the upward bias explicitly
- Derive a rough exit rate from historical exit data in `hr_headcount_v2` and
  apply it as a soft decay. This would set `exit_model_applied: True` with
  `exit_model: "historical_rate_proxy"`.
Recommend option 2 — the data to compute a historical exit rate already
exists. It reduces the upward bias and makes the forecast more honest.

**Output grain:** Monthly forecast values at `vendor + SKU + seat_type` level.
Department breakdown available for the filtered view. Must support
`before_date` filter to narrow to a specific renewal window.

**Confidence expression:** Narrower confidence band than Forecast A because
the hire-driven component is deterministic. The stochastic component (baseline
trend) still gets an 80% confidence band but it applies only to the
post-hire-window portion.

---

## Scope Boundary for This Session

**In scope — decide in this session:**

- Which time-series method for Forecast A (procurement momentum)
- Whether to apply the historical exit rate proxy for Forecast B
- Deprovision decay rate derivation approach
- Forecast horizon default (confirm 8–12 months)
- Confidence interval width (confirm 80%)
- Monthly vs weekly granularity (monthly appears right — confirm)
- How forecast outputs are stored for chatbot reuse (in-memory vs persisted)

**Out of scope — decided, do not reopen:**

- The 3-view decomposition model — confirmed above, do not change
- Ghost detection dual-condition logic — confirmed (`license_status = 'ghost'`
  AND `exit_date IS NOT NULL`)
- The `ProcessingContext` facade pattern — confirmed in Phase 1C spec
- The other five processors — deterministic, no forecasting involved

**Explicitly deferred to a later phase:**

- ML-based churn prediction per license
- Confidence intervals using bootstrapped simulation
- Seasonality modeling (no evidence of seasonality in SaaS provisioning data)
- Vendor-level optimization recommendations
- Exit model trained on demographic or tenure signals

---

## What the Dashboard Tests (Not What It Ships)

The dashboard built during Phase 1C/1D is a **testing instrument** for the
processing output. It exists to verify the forecasting processor is producing
correct, coherent lines before any production consumer (chatbot, API, reports)
is built on top.

The dashboard must render:
1. All 4 historical lines correctly bucketed by month
2. The 2 forecast lines with confidence bands
3. The contracted capacity threshold as a stepwise horizontal line
4. KPI cards for: contracted capacity, vendor-billed active, productive active,
   ghost count, true-up exposure seats
5. Filters: vendor, SKU, seat type, department, job level
6. A current snapshot panel showing the 3 gap calculations

The dashboard does NOT need to be production-quality in this phase. It is a
debugging and validation tool. Style and UX are secondary to correctness.

---

## Data Requirements for the Forecasting Processor

The forecasting processor needs data that is not currently fetched in the
`ProcessingContext`. These fields must be confirmed as available before
implementation begins.

| Data needed | Source | Currently in context? | Notes |
|---|---|---|---|
| Monthly activation counts | `effective_license_date` from `ctx.licenses` | Yes — derivable | Bucket by month in the processor |
| All-time license history (incl. deprovisioned) | `ctx.licenses` with no status filter | Yes — `build_context()` fetches all | Confirm `get_raw_licenses()` returns deprovisioned rows when no status filter |
| Employee exit dates for exit rate derivation | `ctx.exited_employees` | Yes — `exit_date` field present | |
| Pre-hire pipeline with hire dates | `ctx.future_hires` | Yes | |
| Contract start/end history for capacity line | `ctx.active_contracts` | Partial — active contracts only | **Gap:** need historical contract capacity changes too. If a contract went from 120 → 155 seats, the threshold line must step up at that point. Confirm whether `get_contract_history()` provides this or if it needs to be added to the context. |
| Deprovision dates | Not currently tracked as a date field | **Gap** | `license_status = 'deprovisioned'` exists but is there a `deprovisioned_date` field? If not, the deprovision decay rate must be derived from the gap between `effective_license_date` and the current status. Needs confirmation against actual schema. |

**Action items before implementation:**
1. Confirm `get_raw_licenses()` with no filter returns deprovisioned rows
2. Confirm or add `get_contract_history()` to context for capacity stepwise line
3. Confirm whether a `deprovisioned_date` field exists in license data
4. If no `deprovisioned_date`, define how deprovision rate is derived

---

## Ghost Detector Simplification (Confirmed This Session)

Ghost detection uses a dual-condition check. Both must be true:

```python
license_status == 'ghost'
AND
exit_date IS NOT NULL
```

**Why both:** The `license_status = 'ghost'` flag is set by the ingestion
pipeline. The `exit_date IS NOT NULL` check independently confirms the employee
has actually left. This prevents false positives from any ingestion error that
incorrectly marks a license as ghost while the employee is still active.

**This is the V1 logic.** It can be relaxed in a later iteration if the
ingestion pipeline proves reliable enough that the redundant check adds no
value. The flag is kept in the spec as `ghost_confirmed_by_exit_date: bool`
so the chatbot can distinguish between the two signals.

**This does not change the ghost detector processor spec** — it is a
filter condition addition, not a logic change.

---

## Other Processors — Confirmed Simple, Build Directly

The following processors are deterministic aggregations. No research required.
Build them directly from the Phase 1C V2 spec during implementation:

| Processor | Type | Notes |
|---|---|---|
| `trueup_processor` | Deterministic join + arithmetic | Build first — validation targets confirm correctness |
| `breakdown_enricher` | Deterministic group-by | Depends on trueup output grain |
| `ghost_detector` | Filtered join with dual condition | Add `exit_date IS NOT NULL` check per this session |
| `reclamation_detector` | Scored ranking | Scoring weights are a proposal — can tune after seeing output |
| `utilization_aggregator` | Group-by aggregation | Simplest processor — build last as a sanity check |

**Build order confirmed:** Build trueup first (has hard validation targets),
then ghost detector (add dual condition), then the remaining three. Forecasting
processors build last, after this research session produces a finalized spec.

---

## Questions to Answer in the Research Session

Carry these into the next session. Answer all before writing any forecasting
code.

### Method selection

**Q1.** Run linear trend, weighted linear trend, Holt's linear smoothing, and
ARIMA(1,1,0) on the cumulative activation history. Which produces the lowest
RMSE on a 3-month holdout? Which is most interpretable to a procurement
manager?

**Q2.** Is there any evidence of seasonality in the activation data? Plot
monthly activation deltas and check for recurring patterns. If none, exclude
seasonal models.

**Q3.** Does the activation rate appear to be accelerating, stable, or
decelerating? This determines whether weighted recency matters.

### Grain and horizon

**Q4.** At the `vendor + SKU + seat_type` grain, how many months of history
are available per series? If any series has fewer than 12 data points, the
time-series model will be unreliable at that grain. Define a minimum history
threshold — below which the processor falls back to portfolio-level rates.

**Q5.** Confirm the forecast horizon: 8 months forward from audit date
(through Dec 2026) as the default, with override available. Does this
cover all notice deadlines in the active contract set?

### Exit model

**Q6.** Compute the historical monthly exit rate from `hr_headcount_v2`:
```
monthly_exits = count(exit_date in month) / active_headcount_at_start_of_month
```
Is this rate stable month-over-month? If stable (coefficient of variation
< 20%), apply as a constant decay factor. If unstable, keep
`exit_model_applied: False`.

**Q7.** Does the exit rate vary significantly by department? If Engineering
exits at 2x the rate of Finance, the department-level productive active
forecast will be materially wrong if a flat rate is used.

### Storage and reuse

**Q8.** Should forecast outputs be stored in SQLite for chatbot reuse, or
computed on demand? Factors: computation time of the chosen method, frequency
of data updates, chatbot query volume. If computation is under 2 seconds for
the full portfolio, on-demand is fine. If over 2 seconds, store results.

**Q9.** If stored — define the `ml_forecasts` table schema. At minimum:
`vendor`, `sku`, `seat_type`, `forecast_month`, `forecast_line`,
`predicted_value`, `confidence_lower`, `confidence_upper`, `model_version`,
`computed_at`, `expires_at`.

---

## What This Session Produces

The output of this research session is `FORECASTING_SPEC_V1.md` containing:

1. **Method decision** — chosen time-series method for Forecast A with
   justification and holdout RMSE
2. **Exit model decision** — whether historical rate proxy is stable enough
   to apply, with computed monthly exit rate
3. **Deprovision rate** — computed from historical data, confirmed available
4. **Confirmed data gaps resolved** — deprovisioned_date availability,
   contract history for capacity line
5. **Forecast horizon confirmed** — default months forward, override range
6. **Storage decision** — on-demand vs persisted, with schema if persisted
7. **Updated `license_demand_forecaster` spec** — incorporating all decisions
   above, ready to implement
8. **Updated `renewal_pressure_forecaster` forecast section** — incorporating
   procurement momentum projection where relevant

Once `FORECASTING_SPEC_V1.md` is signed off, implementation of the
forecasting processors can begin as the final step of Phase 1C.

---

## Files to Attach to the Research Session

Attach all of these when starting the research session:

| File | Why needed |
|---|---|
| `SAAS_BASE_LAYER_README_V5.md` | Schema reference, validation targets, financial figures |
| `PHASE1C_PROCESSING_LAYER_V2.md` | Full processing layer spec — forecasting processors defined |
| `FORECASTING_RESEARCH_HANDOFF.md` (this file) | Research questions and decisions to make |
| `hr_headcount_v2.csv` | For exit rate computation in Q6 and Q7 |
| `license_utilization_v4.csv` | For activation history, deprovision date check, series length check |
| `vendor_overview_patched_v5.csv` | For contract history and capacity line construction |

Do not attach `PHASE1B_CODE_IMPLEMENTED.md` or `PHASE1B_SERVICES_REDEFINED.md`
— those are service layer documents and are not relevant to the research
questions here.

---

## Current State Summary — What Is Done and What Is Not

### Done — do not revisit

| Item | Status |
|---|---|
| Phase 1A ingestion layer | Complete |
| Phase 1B service layer | Complete — 101 tests passing |
| `hr_headcount_v2.csv` — 180 pre-hire records | Complete |
| `SAAS_BASE_LAYER_README_V5.md` | Complete |
| Phase 1C architecture — ProcessingContext, facade pattern, typed schemas | Finalized in PHASE1C_PROCESSING_LAYER_V2.md |
| 3-view license decomposition model | Confirmed this session |
| Ghost detection dual-condition logic | Confirmed this session |
| 5 deterministic processors spec | Complete in PHASE1C_PROCESSING_LAYER_V2.md |

### In progress — this research session

| Item | Status |
|---|---|
| Time-series method selection for procurement momentum | Open — Q1–Q3 |
| Exit model decision | Open — Q6–Q7 |
| Deprovision rate and date field confirmation | Open — action items above |
| Contract history for capacity stepwise line | Open — action item above |
| Forecast storage decision | Open — Q8–Q9 |

### Not started — after research session

| Item | Depends on |
|---|---|
| `FORECASTING_SPEC_V1.md` | This session output |
| `license_demand_forecaster.py` implementation | FORECASTING_SPEC_V1.md |
| `renewal_pressure_forecaster.py` forecast section | FORECASTING_SPEC_V1.md |
| 5 deterministic processors implementation | Can start now — PHASE1C_PROCESSING_LAYER_V2.md |
| Dashboard (testing instrument) | Processing layer complete |
| Chatbot tool definitions | Processing layer complete |
| API endpoint wiring | Processing layer complete |

---

*Forecasting Research Handoff · SaaS Spend Management · Audit Date: 2026-05-01*  
*Attach this file + PHASE1C_PROCESSING_LAYER_V2.md + all 3 CSVs + README V5*  
*Output: FORECASTING_SPEC_V1.md · No code written in this session*
