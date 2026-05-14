# Case 2 Code Implementation Plan v3

## Purpose

This file is the implementation spec for the next Case 2 build.

The target is no longer only a chat-only procurement recommender. The next
session should build toward a Python-based Strategic Sourcing Workspace using:
- Streamlit
- Plotly
- CSV and JSON-backed data assets

The implementation must stay aligned with the current Case 2 direction:
- keep Case 2 independent from `license_data_v9_20000.csv`
- use the scaled HR base in [hr_data_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\hr_data_v1.csv)
- preserve vendor-motion logic such as:
  - `vendor_3` net-new vendor adoption
  - `vendor_2 Enterprise` as a new tier on an existing vendor

## Verified Blueprint Review

The supplied TRD is directionally strong, but it needs a few adjustments to fit
the current workspace.

### What already fits
- HR demand should come from `hr_data_v1.csv`
- department-aware filtering is correct
- role and level matching is correct
- vendor pricing and benchmark comparisons belong in the data layer
- the Plotly dashboard structure is a good match for Case 2

### What does not exist yet
- normalized derivative files generated from the canonical Case 2 CSVs:
  - `matching_logic.json`
  - `vendor_benchmarks.csv`
- a Streamlit Case 2 workspace module
- a unified enriched Case 2 analytics table

### Important alignment note

The TRD uses:
- `Standard`
- `Pro`
- `Premium`

Current Case 2 data uses:
- `Viewer`
- `Editor`
- `Full`
- `Developer`
- `Enterprise`

We should not silently replace the existing tier system.

Recommended handling:
- keep the source-of-truth tiers as they exist today
- add a normalization layer that maps source tiers to UI-friendly tier groups

Suggested UI grouping:
- `Standard` <- `Viewer`, `Editor`
- `Pro` <- `Full`, `Developer`
- `Premium` <- `Enterprise`

## Current Assets

### Application files
- [rag_engine_v4.py](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\rag_engine_v4.py)
- [app_v3.py](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\app_v3.py)

### Current Case 2 datasets
- [hr_data_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\hr_data_v1.csv)
- [case2_vendor_catalog_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_vendor_catalog_v1.csv)
- [case2_role_license_mapping_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_role_license_mapping_v1.csv)

### Planning docs
- [Case2_Demand_planning.docx](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\Case2_Demand_planning.docx)
- [case2_plan_v1.md](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_plan_v1.md)

## New Build Objective

Implement a Case 2 Strategic Sourcing Workspace that can:
- isolate active vs future demand
- map employees to recommended vendor SKU and tier
- estimate annual spend with tiered pricing logic
- compare proposed pricing vs market benchmarks
- power an interactive Streamlit + Plotly workspace
- still support chat-based procurement responses where useful

## Updated Implementation Strategy

Build this in 6 layers:

1. Data asset completion layer
2. Data loading layer
3. Enrichment and pricing layer
4. Streamlit workspace layer
5. Plotly visualization layer
6. Optional chat/routing layer

## Layer 1: Data Asset Completion

### Objective

Create the missing assets required by the TRD.

### Required new files
- `matching_logic.json`
- `vendor_benchmarks.csv`
- `case2_workspace_v1.py`

### `matching_logic.json`

This file should be generated from the canonical role mapping dataset:
- [case2_role_license_mapping_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_role_license_mapping_v1.csv)

It is a normalized runtime artifact, not a separate hand-maintained source of truth.

Minimum keys per rule:
- `pillar_dept`
- `job_role`
- `job_level`
- `recommended_tier_group`
- `recommended_source_tier`
- `primary_vendor`
- `primary_vendor_sku`
- `procurement_motion`
- `fit_score`
- `rationale`

Important:
- include `pillar_dept` as a matching key
- preserve the current vendor-motion logic already encoded in `case2_role_license_mapping_v1.csv`
- treat this JSON as the normalized UI-serving logic artifact

### `vendor_benchmarks.csv`

This file should be generated from the canonical vendor catalog dataset:
- [case2_vendor_catalog_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_vendor_catalog_v1.csv)

It is a normalized runtime artifact, not a separate hand-maintained source of truth.

Minimum columns:
- `vendor_name`
- `sku_id`
- `license_tier`
- `tier_group`
- `proposed_unit_price`
- `market_avg_price`
- `best_competitor_vendor`
- `best_competitor_sku`
- `best_competitor_price`
- `volume_band_min`
- `volume_band_max`

### Data generation dependency

The canonical CSVs already contain most of the logic we need.

Required next step:
- extend the generator so it emits normalized derivatives for the UI/runtime

Derived artifact responsibilities:
- role mapping CSV -> `matching_logic.json`
- vendor catalog CSV -> `vendor_benchmarks.csv`

## Layer 2: Data Loading

### Objective

Load all Case 2 assets into a reusable engine layer.

### Create
- `case2_engine_v1.py`

### Add loaders
- `load_hr_data()`
- `load_vendor_catalog()`
- `load_role_mapping()`
- `load_matching_logic()`
- `load_vendor_benchmarks()`

### Expected behavior
- read CSVs with `pandas`
- read JSON with `json`
- cache outputs after first load
- raise clean errors for missing files

## Layer 3: Enrichment And Pricing

### Objective

Build the single enriched dataframe that powers the KPI header, charts, and
insight text.

### Required logic

#### A. HR demand status logic

From `hr_data_v1.csv`, derive:
- `employee_status`
  - `Active`
  - `Future_Hire`
- `demand_scope`
  - `current_demand`
  - `projected_demand`

#### B. Matching join

Join keys:
- `pillar_dept`
- `job_role`
- `job_level`

Join source:
- `matching_logic.json`

Join outputs:
- `recommended_tier_group`
- `recommended_source_tier`
- `primary_vendor`
- `primary_vendor_sku`
- `procurement_motion`

#### C. Vendor pricing logic

Use `vendor_benchmarks.csv` to resolve price by demand volume.

Required helper:
- `resolve_tiered_price(sku_id: str, demand_count: int) -> float`

Example:
- if demand for a SKU exceeds `1000`, choose the lower volume-band price

#### D. Enriched analytics table

Build a dataframe such as `case2_workspace_view` with at least:
- `employee_id`
- `pillar_dept`
- `job_role`
- `job_level`
- `employee_status`
- `recommended_tier_group`
- `recommended_source_tier`
- `primary_vendor`
- `primary_vendor_sku`
- `procurement_motion`
- `proposed_unit_price`
- `market_avg_price`
- `best_competitor_price`
- `projected_annual_cost`

### KPI helpers

Add:
- `get_total_project_demand()`
- `get_future_hire_count()`
- `get_estimated_annual_spend()`
- `get_negotiation_delta()`

Definition:
- `negotiation_delta = total_proposed_spend - total_market_avg_spend`

## Layer 4: Streamlit Workspace

### Objective

Create the Case 2 sourcing UI.

### Create
- `case2_workspace_v1.py`

### Layout requirements

#### Global sidebar filter
- `pillar_dept` single-select dropdown
- changing this filter must update all charts

#### Role discovery filter
- `job_role` multi-select
- default selection must be Top 4 roles by headcount within the current filter
- all non-selected roles must aggregate into `Others`

#### KPI header
- Total Project Demand
- Future Hire Demand
- Estimated Annual Spend
- Negotiation Delta

## Layer 5: Plotly Visuals

### Objective

Render the four required charts with cost-aware hover details.

### Chart 1: Aggregated Demand And Cost
- dual axis
- X: total project or current filtered scope
- Y1 bars: headcount stacked by `employee_status`
- Y2 line: total cost

### Chart 2: Departmental Persona Mix
- donut chart
- segments: `job_role`
- values: employee count
- reacts to `pillar_dept`

### Chart 3: Tier Optimization
- stacked bar
- X: Top 4 roles plus `Others`
- stack: `recommended_tier_group`
- tooltip must include stack cost

Formula:
- `stack_cost = count_in_segment * proposed_unit_price`

### Chart 4: Market Sourcing Analysis
- clustered bar
- X: `primary_vendor_sku`
- bars:
  - proposed price
  - market average
  - best competitor price

### Hovertemplate requirement

Every chart should use Plotly `hovertemplate` and expose:
- count
- unit price
- cost contribution where applicable

## Layer 6: Sourcing Insight Logic

### Objective

Generate a short narrative insight for the current filtered state.

### Required behavior

Show a `Sourcing Insight` text box that highlights whether the selected
department is over-indexed on Premium tiers versus the company average.

Required helper:
- `build_sourcing_insight(filtered_df, company_df) -> str`

Suggested logic:
- compute `% Premium` in filtered selection
- compute `% Premium` company-wide
- compare delta
- if delta exceeds a threshold such as 5 percentage points, flag the department

## Optional Chat / Routing Layer

### Objective

Preserve chat-based Case 2 handling where it complements the UI.

### Changes in `rag_engine_v4.py`
- keep procurement intent detection
- route requests to the new Case 2 engine
- allow chat responses to use the same enriched pricing and recommendation logic

Do not mix this with the old SQL fact-table reporting path.

## Missing Functionalities To Add In The Data Layer

These are the remaining gaps between the current canonical datasets and the new blueprint.

### Gap 1: No generated `matching_logic.json`
- required as a normalized runtime artifact
- should be generated directly from `case2_role_license_mapping_v1.csv`

### Gap 2: No generated `vendor_benchmarks.csv`
- required as a normalized runtime artifact for benchmark and pricing lookups
- should be generated directly from `case2_vendor_catalog_v1.csv`

### Gap 3: No tier-group normalization
- current data uses operational tiers
- UI spec expects `Standard` / `Pro` / `Premium`

### Gap 4: No explicit proposed-vs-market pricing model
- current catalog has quote and market average
- but not the final resolved volume-band output per SKU for dashboard use

### Gap 5: No explicit competitor benchmark price
- current catalog has competitor name only
- the dashboard needs a competitor price series

### Gap 6: No enriched workspace dataframe
- current assets are source tables only
- we still need one joined analytical table or equivalent cached view

### Gap 7: No Top 4 plus `Others` aggregation helper
- needed to prevent UI overload and make Chart 3 stable

### Gap 8: No company-average premium mix baseline
- required for the `Sourcing Insight` text box

## Validation Cases

Validate these cases after implementation:

1. `I need 25 vendor_3 licenses for Sales Operations`
- should classify as net-new vendor adoption
- should show pricing and benchmark context

2. `Upgrade vendor_2 to Enterprise for Legal Counsel`
- should classify as existing vendor new-tier upgrade
- should surface enterprise benchmark pricing

3. `Product department` selected in sidebar
- all four charts should update together

4. `job_role` filter left on default
- UI should show Top 4 roles and aggregate the rest into `Others`

5. department with high enterprise concentration
- sourcing insight should compare Premium mix vs company average

## Definition Of Done

The implementation is complete when:
- the missing data assets are created
- the Case 2 engine builds an enriched pricing-and-demand view
- the Streamlit workspace renders the 4 required charts
- all charts react to the unified `pillar_dept` filter
- role discovery defaults to Top 4 plus `Others`
- KPI header and sourcing insight are populated correctly
- chat-based Case 2 routing still works or is cleanly preserved for a later step

## Next Session Instruction

When this file is uploaded in the next session, the coding task should be:

`Implement the Case 2 Strategic Sourcing Workspace from case2_code_implementation_plan_v1.md. Start by creating matching_logic.json and vendor_benchmarks.csv, then build case2_engine_v1.py, then create the Streamlit + Plotly UI in case2_workspace_v1.py.`
