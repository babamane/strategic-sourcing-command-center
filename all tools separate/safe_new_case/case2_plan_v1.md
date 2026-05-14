# Case 2 Demand Planning Plan v2

## Direction

Case 2 should stay independent from the legacy license inventory dataset for now.

What we are optimizing for:
- a self-contained Case 2 HR base
- deterministic vendor and tier recommendation logic
- a Strategic Sourcing Workspace UI driven by Streamlit and Plotly
- clean answers to requests such as:
  - `I want 25 vendor_3 licenses`
  - `I want to upgrade vendor_2 to Enterprise`
  - `Which roles should switch from vendor_1 to vendor_3?`

What we are explicitly not doing in this version:
- no employee-to-license join
- no bridge back to legacy `license_data_v9_20000.csv`
- no employee-level recommendation file

## Current Case 2 Assets

- [hr_data_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\hr_data_v1.csv)
  - scaled Case 2 HR dataset
  - `13,344` active employees
  - `954` future hires for demand planning
- [case2_vendor_catalog_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_vendor_catalog_v1.csv)
  - vendor SKU catalog
  - current portfolio status by vendor and tier
  - baseline seat signals and future-demand signals
- [case2_role_license_mapping_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_role_license_mapping_v1.csv)
  - role and level based current-state to target-state mapping
  - vendor-switch and tier-upgrade guidance

## Verified Gaps Against The UI Blueprint

The new implementation blueprint is mostly compatible with our direction, but
these data assets are still missing:
- generated runtime artifacts:
  - `matching_logic.json`
  - `vendor_benchmarks.csv`

Canonical source-of-truth files for Case 2 should remain:
- [case2_role_license_mapping_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_role_license_mapping_v1.csv)
- [case2_vendor_catalog_v1.csv](C:\Users\PallantiAsrithVatsal\Desktop\safe_new_case\case2_vendor_catalog_v1.csv)

We also need these data-layer capabilities before the UI can be fully built:
- tier-group normalization from source tiers to `Standard` / `Pro` / `Premium`
- volume-band pricing lookup
- explicit competitor benchmark price
- one enriched workspace-ready analytical view
- Top 4 role aggregation plus `Others`
- company-average premium-mix baseline for sourcing insight

## Updated Model

### HR layer
- HR is the demand-side truth for Case 2.
- Keep it intentionally separate from the old 20k license dataset.
- Use active employees plus future hires to estimate where new demand is likely to appear.

### Vendor layer
- Each vendor row should show whether the tier is:
  - already active in the current portfolio
  - a new tier on an existing vendor
  - a net-new vendor motion
- This is what allows us to answer:
  - `vendor_3 x licenses`
  - `vendor_2 Enterprise upgrade`

### Matching layer
- Match by:
  - `pillar_dept`
  - `job_role`
  - `job_level`
- For each role/level row, store:
  - current vendor and tier
  - target vendor and tier
  - procurement motion
  - rationale
- Add a UI-serving normalization layer that can also expose:
  - `recommended_tier_group`
  - `primary_vendor_sku`
  - pricing and benchmark context

## Procurement Motions To Support

- `expand_existing_tier`
  - same vendor, same tier, more seats
- `upgrade_existing_vendor`
  - same vendor, higher tier already known in portfolio
- `upgrade_existing_vendor_new_tier`
  - same vendor, higher tier not yet bought
- `switch_existing_vendor`
  - move to another vendor already known in the broader stack
- `new_vendor_adoption`
  - bring in a net-new vendor such as `vendor_3`

## Immediate Build Plan

### Phase 1: HR reset
- regenerate HR with `13,344` active employees
- keep the future-hire pool scaled accordingly
- keep the role mix realistic across departments

### Phase 2: Vendor catalog reset
- keep the vendor catalog self-contained
- add portfolio-state columns so each vendor/tier can support procurement routing
- ensure `vendor_3` is represented as a net-new vendor option
- ensure `vendor_2 Enterprise` is represented as a new tier on an existing vendor
- add benchmark-ready pricing fields for sourcing comparison
- add volume-band structures usable for tiered price resolution

### Phase 3: Role-license matching reset
- remove legacy license-position bridge logic
- remove employee-level recommendation output
- generate only role-level motion guidance
- include current-state and target-state columns
- create `matching_logic.json` from the finalized matching rules
- treat `case2_role_license_mapping_v1.csv` as the canonical matching source

### Phase 4: Workspace analytics layer
- build one enriched Case 2 analytical view from HR + matching + benchmarks
- compute KPIs, role ranking, cost metrics, and sourcing insight baseline
- generate `vendor_benchmarks.csv` from the canonical vendor catalog

### Phase 5: Strategic Sourcing UI
- implement the Streamlit workspace
- add unified `pillar_dept` filtering
- add Plotly charts with cost-aware hover templates

## Decision

Proceed with:
- updated HR generation
- updated vendor catalog
- updated role-license matching data

Do not continue with:
- position bridge dataset
- employee recommendation dataset
- legacy license-data alignment for Case 2
