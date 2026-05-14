"""
Case 2 Vendor and Matching Data Generator v2
============================================

Builds a simplified Case 2 foundation that is intentionally independent from
the legacy license inventory dataset.

Outputs:
1. Vendor catalog with current portfolio signals
2. Role/job-level matching table with vendor/tier motion guidance
3. Matching logic JSON derived from the canonical role mapping CSV
4. Vendor benchmarks CSV derived from the canonical vendor catalog CSV
"""

import csv
import json
import random
from collections import Counter, defaultdict


RANDOM_SEED = 42
HR_INPUT_FILE = "hr_data_v1.csv"
VENDOR_OUTPUT_FILE = "case2_vendor_catalog_v1.csv"
ROLE_MAPPING_OUTPUT_FILE = "case2_role_license_mapping_v1.csv"
MATCHING_JSON_OUTPUT_FILE = "matching_logic.json"
BENCHMARK_OUTPUT_FILE = "vendor_benchmarks.csv"

random.seed(RANDOM_SEED)


VENDOR_SKUS = [
    {
        "vendor_name": "vendor_1",
        "sku_id": "V1-COL-VWR",
        "license_tier": "Viewer",
        "sku_name": "Workspace Viewer",
        "sku_family": "Collaboration",
        "capability_description": "Read-only access to shared workspaces, dashboards, and team documentation.",
        "normalized_keywords": "viewer read-only dashboards docs collaboration",
        "unit_price_quote": 12,
        "market_avg_price": 13,
        "competitor_alt": "Confluence Viewer",
        "volume_discount_tiers": "1-49:0%;50-199:6%;200-499:11%;500+:16%",
        "default_department_fit": "Sales, Marketing, Operations",
        "min_job_level": "L1",
        "max_job_level": "L3",
        "current_portfolio_status": "Active_Portfolio",
    },
    {
        "vendor_name": "vendor_1",
        "sku_id": "V1-COL-EDT",
        "license_tier": "Editor",
        "sku_name": "Workspace Editor",
        "sku_family": "Collaboration",
        "capability_description": "Core editing, workflow participation, and collaborative content management.",
        "normalized_keywords": "editor edit collaborate workflow content",
        "unit_price_quote": 31,
        "market_avg_price": 33,
        "competitor_alt": "Atlassian Standard",
        "volume_discount_tiers": "1-49:0%;50-199:8%;200-499:13%;500+:18%",
        "default_department_fit": "Engineering, Product, Marketing",
        "min_job_level": "L1",
        "max_job_level": "L5",
        "current_portfolio_status": "Active_Portfolio",
    },
    {
        "vendor_name": "vendor_1",
        "sku_id": "V1-COL-FUL",
        "license_tier": "Full",
        "sku_name": "Workspace Full",
        "sku_family": "Collaboration",
        "capability_description": "Advanced authoring, workflow automation, and admin-lite collaboration controls.",
        "normalized_keywords": "full authoring workflow automation collaboration",
        "unit_price_quote": 46,
        "market_avg_price": 49,
        "competitor_alt": "Atlassian Premium",
        "volume_discount_tiers": "1-49:0%;50-199:9%;200-499:15%;500+:21%",
        "default_department_fit": "Engineering, Product, Marketing",
        "min_job_level": "L2",
        "max_job_level": "L7",
        "current_portfolio_status": "Active_Portfolio",
    },
    {
        "vendor_name": "vendor_1",
        "sku_id": "V1-ENG-DEV",
        "license_tier": "Developer",
        "sku_name": "Engineering Studio Developer",
        "sku_family": "Engineering",
        "capability_description": "Developer-grade workflows for source integrations, pipelines, runbooks, and release automation.",
        "normalized_keywords": "developer engineering pipelines source-control runbooks devops",
        "unit_price_quote": 65,
        "market_avg_price": 68,
        "competitor_alt": "GitLab Ultimate Seat",
        "volume_discount_tiers": "1-49:0%;50-199:10%;200-499:16%;500+:23%",
        "default_department_fit": "Engineering",
        "min_job_level": "L3",
        "max_job_level": "L7",
        "current_portfolio_status": "Active_Portfolio",
    },
    {
        "vendor_name": "vendor_2",
        "sku_id": "V2-OPS-VWR",
        "license_tier": "Viewer",
        "sku_name": "Operations Viewer",
        "sku_family": "Operations",
        "capability_description": "View-only access to workflows, approvals, finance records, and operating dashboards.",
        "normalized_keywords": "operations viewer approvals finance legal dashboards",
        "unit_price_quote": 11,
        "market_avg_price": 12,
        "competitor_alt": "Smartsheet Viewer",
        "volume_discount_tiers": "1-49:0%;50-199:5%;200-499:10%;500+:15%",
        "default_department_fit": "Finance, Legal, Operations",
        "min_job_level": "L1",
        "max_job_level": "L3",
        "current_portfolio_status": "Active_Portfolio",
    },
    {
        "vendor_name": "vendor_2",
        "sku_id": "V2-OPS-EDT",
        "license_tier": "Editor",
        "sku_name": "Operations Editor",
        "sku_family": "Operations",
        "capability_description": "Editable workflows, approvals, reporting, and operational record management.",
        "normalized_keywords": "operations editor approvals workflows records reporting",
        "unit_price_quote": 28,
        "market_avg_price": 30,
        "competitor_alt": "Smartsheet Pro",
        "volume_discount_tiers": "1-49:0%;50-199:7%;200-499:12%;500+:18%",
        "default_department_fit": "Finance, Legal, Operations",
        "min_job_level": "L1",
        "max_job_level": "L5",
        "current_portfolio_status": "Active_Portfolio",
    },
    {
        "vendor_name": "vendor_2",
        "sku_id": "V2-OPS-FUL",
        "license_tier": "Full",
        "sku_name": "Operations Manager",
        "sku_family": "Operations",
        "capability_description": "Advanced process ownership, cross-functional reporting, and admin controls for business teams.",
        "normalized_keywords": "operations full admin reporting process ownership",
        "unit_price_quote": 42,
        "market_avg_price": 45,
        "competitor_alt": "ServiceNow Business Seat",
        "volume_discount_tiers": "1-49:0%;50-199:8%;200-499:13%;500+:19%",
        "default_department_fit": "Finance, Legal, Operations",
        "min_job_level": "L2",
        "max_job_level": "L7",
        "current_portfolio_status": "Active_Portfolio",
    },
    {
        "vendor_name": "vendor_2",
        "sku_id": "V2-LEG-ENT",
        "license_tier": "Enterprise",
        "sku_name": "Compliance Enterprise",
        "sku_family": "Compliance",
        "capability_description": "Audit-grade controls, contract workflows, compliance governance, and policy automation.",
        "normalized_keywords": "enterprise compliance legal contract audit governance",
        "unit_price_quote": 79,
        "market_avg_price": 84,
        "competitor_alt": "Ironclad Enterprise",
        "volume_discount_tiers": "1-49:0%;50-199:9%;200-499:15%;500+:22%",
        "default_department_fit": "Legal, Compliance, Procurement",
        "min_job_level": "L4",
        "max_job_level": "L7",
        "current_portfolio_status": "Upgrade_Target_Not_Yet_Bought",
    },
    {
        "vendor_name": "vendor_3",
        "sku_id": "V3-INS-VWR",
        "license_tier": "Viewer",
        "sku_name": "Insight Viewer",
        "sku_family": "Analytics",
        "capability_description": "View-only analytics access for shared dashboards and guided reporting.",
        "normalized_keywords": "analytics viewer dashboards reports read-only",
        "unit_price_quote": 18,
        "market_avg_price": 20,
        "competitor_alt": "Power BI Free",
        "volume_discount_tiers": "1-49:0%;50-199:5%;200-499:9%;500+:14%",
        "default_department_fit": "Sales, Product, Finance",
        "min_job_level": "L1",
        "max_job_level": "L3",
        "current_portfolio_status": "Net_New_Vendor",
    },
    {
        "vendor_name": "vendor_3",
        "sku_id": "V3-ANA-EDT",
        "license_tier": "Editor",
        "sku_name": "Insight Analyst",
        "sku_family": "Analytics",
        "capability_description": "Analyst workspace for dashboards, pipeline analysis, scenario modeling, and collaborative reporting.",
        "normalized_keywords": "analytics editor scenario-modeling analyst reporting",
        "unit_price_quote": 34,
        "market_avg_price": 36,
        "competitor_alt": "Power BI Pro",
        "volume_discount_tiers": "1-49:0%;50-199:7%;200-499:12%;500+:18%",
        "default_department_fit": "Sales, Product, Finance",
        "min_job_level": "L2",
        "max_job_level": "L5",
        "current_portfolio_status": "Net_New_Vendor",
    },
    {
        "vendor_name": "vendor_3",
        "sku_id": "V3-ANA-FUL",
        "license_tier": "Full",
        "sku_name": "Insight Pro",
        "sku_family": "Analytics",
        "capability_description": "Advanced analytics, shared semantic metrics, and cross-functional decision support.",
        "normalized_keywords": "analytics full semantic metrics reporting decision support",
        "unit_price_quote": 54,
        "market_avg_price": 57,
        "competitor_alt": "Power BI Premium Per User",
        "volume_discount_tiers": "1-49:0%;50-199:8%;200-499:14%;500+:20%",
        "default_department_fit": "Sales, Product, Finance, Operations",
        "min_job_level": "L3",
        "max_job_level": "L7",
        "current_portfolio_status": "Net_New_Vendor",
    },
    {
        "vendor_name": "vendor_3",
        "sku_id": "V3-AI-ENT",
        "license_tier": "Enterprise",
        "sku_name": "Strategic Copilot Enterprise",
        "sku_family": "AI",
        "capability_description": "High-trust enterprise copilots for decision support, policy-aware automation, forecasting, and executive workflows.",
        "normalized_keywords": "ai enterprise copilot forecasting automation executive",
        "unit_price_quote": 92,
        "market_avg_price": 98,
        "competitor_alt": "Microsoft 365 Copilot",
        "volume_discount_tiers": "1-49:0%;50-199:9%;200-499:15%;500+:22%",
        "default_department_fit": "Product, Finance, Operations, Leadership",
        "min_job_level": "L4",
        "max_job_level": "L7",
        "current_portfolio_status": "Net_New_Vendor",
    },
]

SKU_LOOKUP = {row["sku_id"]: row for row in VENDOR_SKUS}
LEVEL_TO_NUM = {f"L{i}": i for i in range(1, 8)}
CURRENT_PORTFOLIO_TIERS = {
    "vendor_1": {"Viewer", "Editor", "Full", "Developer"},
    "vendor_2": {"Viewer", "Editor", "Full"},
    "vendor_3": set(),
}
COMPETITOR_PRICE_FACTOR = {
    "Confluence Viewer": 1.08,
    "Atlassian Standard": 1.06,
    "Atlassian Premium": 1.05,
    "GitLab Ultimate Seat": 1.07,
    "Smartsheet Viewer": 1.09,
    "Smartsheet Pro": 1.07,
    "ServiceNow Business Seat": 1.08,
    "Ironclad Enterprise": 1.06,
    "Power BI Free": 1.00,
    "Power BI Pro": 1.06,
    "Power BI Premium Per User": 1.05,
    "Microsoft 365 Copilot": 1.04,
}


def read_hr_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2)


def price_band(vendor_name, tier):
    base_prices = {
        ("vendor_1", "Viewer"): "low",
        ("vendor_1", "Editor"): "medium",
        ("vendor_1", "Full"): "medium",
        ("vendor_1", "Developer"): "high",
        ("vendor_2", "Viewer"): "low",
        ("vendor_2", "Editor"): "medium",
        ("vendor_2", "Full"): "medium",
        ("vendor_2", "Enterprise"): "high",
        ("vendor_3", "Viewer"): "medium",
        ("vendor_3", "Editor"): "medium",
        ("vendor_3", "Full"): "high",
        ("vendor_3", "Enterprise"): "high",
    }
    return base_prices.get((vendor_name, tier), "medium")


def tier_group_for(source_tier):
    if source_tier in {"Viewer", "Editor"}:
        return "Standard"
    if source_tier in {"Full", "Developer"}:
        return "Pro"
    return "Premium"


def competitor_price(vendor_row):
    factor = COMPETITOR_PRICE_FACTOR.get(vendor_row["competitor_alt"], 1.06)
    return round(vendor_row["market_avg_price"] * factor, 2)


def parse_volume_discount_tiers(tier_string):
    rows = []
    for chunk in tier_string.split(";"):
        band, discount = chunk.split(":")
        if "-" in band:
            min_part, max_part = band.split("-")
            volume_band_min = int(min_part)
            volume_band_max = 999999 if max_part.endswith("+") else int(max_part)
        else:
            volume_band_min = int(band.rstrip("+"))
            volume_band_max = 999999
        discount_pct = float(discount.rstrip("%"))
        rows.append({
            "volume_band_min": volume_band_min,
            "volume_band_max": volume_band_max,
            "discount_percent": discount_pct,
        })
    return rows


def choose_current_state(dept, role, level):
    level_num = LEVEL_TO_NUM[level]

    if dept == "Engineering":
        if role in {"Software Engineer", "Data Engineer"}:
            sku_id = "V1-COL-EDT" if level_num <= 2 else "V1-COL-FUL"
        elif role in {"DevOps", "SRE"}:
            sku_id = "V1-COL-FUL"
        else:
            sku_id = "V1-COL-FUL"
    elif dept == "Marketing":
        sku_id = "V1-COL-EDT" if level_num <= 2 else "V1-COL-FUL"
    elif dept == "Product":
        sku_id = "V1-COL-EDT" if role == "Product Analyst" and level_num <= 2 else "V1-COL-FUL"
    elif dept == "Sales":
        sku_id = "V1-COL-VWR" if role == "Sales Development Representative" and level_num <= 2 else "V1-COL-EDT"
    elif dept == "Operations":
        sku_id = "V2-OPS-VWR" if level_num == 1 else "V2-OPS-EDT" if level_num <= 3 else "V2-OPS-FUL"
    elif dept == "Finance":
        sku_id = "V2-OPS-VWR" if level_num == 1 else "V2-OPS-EDT" if level_num <= 3 else "V2-OPS-FUL"
    elif dept == "Legal":
        sku_id = "V2-OPS-EDT" if level_num <= 3 else "V2-OPS-FUL"
    else:
        sku_id = "V1-COL-FUL"

    sku = SKU_LOOKUP[sku_id]
    return {
        "current_vendor": sku["vendor_name"],
        "current_license_tier": sku["license_tier"],
        "current_sku_id": sku_id,
        "current_sku_name": sku["sku_name"],
    }


def choose_target_state(dept, role, level):
    level_num = LEVEL_TO_NUM[level]

    if dept == "Engineering":
        if role == "Software Engineer":
            sku_id = "V1-COL-EDT" if level_num <= 2 else "V1-COL-FUL" if level_num <= 4 else "V1-ENG-DEV"
        elif role in {"Data Engineer", "DevOps", "SRE"}:
            sku_id = "V1-COL-FUL" if level_num <= 3 else "V1-ENG-DEV"
        else:
            sku_id = "V1-COL-FUL"
    elif dept == "Marketing":
        sku_id = "V1-COL-EDT" if level_num <= 2 else "V1-COL-FUL"
    elif dept == "Product":
        if role == "Product Manager":
            sku_id = "V1-COL-FUL" if level_num <= 4 else "V3-AI-ENT"
        else:
            sku_id = "V1-COL-EDT" if level_num <= 2 else "V3-ANA-FUL" if level_num <= 5 else "V3-AI-ENT"
    elif dept == "Sales":
        if role == "Sales Development Representative":
            sku_id = "V1-COL-VWR" if level_num == 1 else "V3-ANA-EDT"
        elif role == "Account Executive":
            sku_id = "V3-ANA-FUL" if level_num <= 5 else "V3-AI-ENT"
        else:
            sku_id = "V3-ANA-EDT" if level_num <= 3 else "V3-ANA-FUL"
    elif dept == "Operations":
        if role == "Business Operations Manager":
            sku_id = "V2-OPS-FUL" if level_num <= 4 else "V3-ANA-FUL"
        elif role == "Program Coordinator":
            sku_id = "V2-OPS-VWR" if level_num == 1 else "V2-OPS-EDT"
        else:
            sku_id = "V2-OPS-VWR" if level_num == 1 else "V2-OPS-EDT"
    elif dept == "Finance":
        if role == "Finance Manager":
            sku_id = "V2-OPS-FUL" if level_num <= 4 else "V3-AI-ENT"
        elif role == "Procurement Analyst":
            sku_id = "V2-OPS-EDT" if level_num <= 2 else "V3-ANA-FUL"
        else:
            sku_id = "V2-OPS-VWR" if level_num <= 2 else "V2-OPS-EDT"
    elif dept == "Legal":
        if role in {"Legal Counsel", "Contract Manager", "Compliance Analyst"}:
            sku_id = "V2-OPS-FUL" if level_num <= 4 else "V2-LEG-ENT"
        else:
            sku_id = "V2-OPS-EDT"
    else:
        sku_id = "V1-COL-FUL"

    sku = SKU_LOOKUP[sku_id]
    return {
        "target_vendor": sku["vendor_name"],
        "target_license_tier": sku["license_tier"],
        "target_sku_id": sku_id,
        "target_sku_name": sku["sku_name"],
        "price_band": price_band(sku["vendor_name"], sku["license_tier"]),
    }


def procurement_motion(current_state, target_state):
    current_vendor = current_state["current_vendor"]
    current_tier = current_state["current_license_tier"]
    target_vendor = target_state["target_vendor"]
    target_tier = target_state["target_license_tier"]

    if current_vendor == target_vendor and current_tier == target_tier:
        return "expand_existing_tier"
    if current_vendor == target_vendor and target_tier in CURRENT_PORTFOLIO_TIERS[target_vendor]:
        return "upgrade_existing_vendor"
    if current_vendor == target_vendor:
        return "upgrade_existing_vendor_new_tier"
    if CURRENT_PORTFOLIO_TIERS[target_vendor]:
        return "switch_existing_vendor"
    return "new_vendor_adoption"


def portfolio_signal(motion):
    return {
        "expand_existing_tier": "same_vendor_same_tier",
        "upgrade_existing_vendor": "same_vendor_higher_tier_already_in_portfolio",
        "upgrade_existing_vendor_new_tier": "same_vendor_new_tier_not_yet_bought",
        "switch_existing_vendor": "different_vendor_existing_portfolio",
        "new_vendor_adoption": "different_vendor_net_new",
    }[motion]


def fit_score_for(level, motion):
    base = 0.9
    if motion == "new_vendor_adoption":
        base -= 0.05
    elif motion == "upgrade_existing_vendor_new_tier":
        base -= 0.02
    elif motion == "switch_existing_vendor":
        base -= 0.03

    if LEVEL_TO_NUM[level] >= 5:
        base += 0.02

    jitter = random.uniform(-0.015, 0.015)
    return round(max(0.78, min(0.98, base + jitter)), 2)


def build_rationale(dept, role, level, current_state, target_state, motion):
    motion_text = {
        "expand_existing_tier": "can stay on the current vendor and current tier",
        "upgrade_existing_vendor": "fits better as an upgrade inside the current vendor stack",
        "upgrade_existing_vendor_new_tier": "needs a new tier on an already-approved vendor",
        "switch_existing_vendor": "fits better on a different vendor that already exists in the broader stack",
        "new_vendor_adoption": "calls for a net-new vendor motion",
    }[motion]

    return (
        f"{role} in {dept} at {level} {motion_text}. "
        f"Current state is {current_state['current_vendor']} {current_state['current_license_tier']}; "
        f"recommended state is {target_state['target_vendor']} {target_state['target_license_tier']} "
        f"({target_state['target_sku_name']})."
    )


def build_switch_reason(current_state, target_state, motion):
    if motion == "expand_existing_tier":
        return "Requested seats align with an already active vendor/tier combination."
    if motion == "upgrade_existing_vendor":
        return "The use case needs a higher-capability tier that is already part of the current vendor footprint."
    if motion == "upgrade_existing_vendor_new_tier":
        return "The vendor is already in use, but this target tier has not been purchased yet."
    if motion == "switch_existing_vendor":
        return "The target workflow is better served by a different vendor already known to the organization."
    return "The target workflow introduces vendor_3 as a new category purchase."


def build_role_mapping(hr_rows):
    role_level_pairs = {}
    for row in hr_rows:
        key = (row["pillar_dept"], row["job_role"], row["job_level"])
        role_level_pairs[key] = row

    mapping_rows = []
    for dept, role, level in sorted(
        role_level_pairs.keys(),
        key=lambda item: (str(item[0]), str(item[1]), str(item[2])),
    ):
        current_state = choose_current_state(dept, role, level)
        target_state = choose_target_state(dept, role, level)
        motion = procurement_motion(current_state, target_state)

        mapping_rows.append({
            "pillar_dept": dept,
            "job_role": role,
            "job_level": level,
            "current_vendor": current_state["current_vendor"],
            "current_license_tier": current_state["current_license_tier"],
            "current_sku_id": current_state["current_sku_id"],
            "current_sku_name": current_state["current_sku_name"],
            "target_vendor": target_state["target_vendor"],
            "target_license_tier": target_state["target_license_tier"],
            "target_sku_id": target_state["target_sku_id"],
            "target_sku_name": target_state["target_sku_name"],
            "procurement_motion": motion,
            "portfolio_signal": portfolio_signal(motion),
            "fit_score": fit_score_for(level, motion),
            "price_band": target_state["price_band"],
            "switch_reason": build_switch_reason(current_state, target_state, motion),
            "match_rationale": build_rationale(dept, role, level, current_state, target_state, motion),
        })

    return mapping_rows


def build_vendor_catalog(hr_rows, role_rows):
    active_current_counts = defaultdict(int)
    active_target_counts = defaultdict(int)
    future_target_counts = defaultdict(int)

    role_lookup = {
        (row["pillar_dept"], row["job_role"], row["job_level"]): row
        for row in role_rows
    }

    for row in hr_rows:
        mapping = role_lookup[(row["pillar_dept"], row["job_role"], row["job_level"])]
        current_key = (mapping["current_vendor"], mapping["current_license_tier"])
        target_key = (mapping["target_vendor"], mapping["target_license_tier"])

        if row["is_active"] == "Active":
            active_current_counts[current_key] += 1
            if mapping["procurement_motion"] != "expand_existing_tier":
                active_target_counts[target_key] += 1
        else:
            future_target_counts[target_key] += 1

    catalog_rows = []
    for vendor_row in VENDOR_SKUS:
        key = (vendor_row["vendor_name"], vendor_row["license_tier"])
        active_current = active_current_counts[key]
        active_target = active_target_counts[key]
        future_target = future_target_counts[key]

        if vendor_row["current_portfolio_status"] == "Active_Portfolio":
            request_motion = "existing_tier_purchase"
        elif vendor_row["vendor_name"] == "vendor_2":
            request_motion = "existing_vendor_new_tier"
        else:
            request_motion = "net_new_vendor_purchase"

        catalog_rows.append({
            **vendor_row,
            "tier_group": tier_group_for(vendor_row["license_tier"]),
            "proposed_unit_price": vendor_row["unit_price_quote"],
            "best_competitor_vendor": vendor_row["competitor_alt"],
            "best_competitor_price": competitor_price(vendor_row),
            "baseline_active_seats": active_current,
            "active_upgrade_or_switch_candidates": active_target,
            "future_hire_demand_candidates": future_target,
            "case2_request_motion": request_motion,
        })

    return catalog_rows


def build_matching_logic(role_rows):
    rules = []
    for row in role_rows:
        rules.append({
            "pillar_dept": row["pillar_dept"],
            "job_role": row["job_role"],
            "job_level": row["job_level"],
            "recommended_tier_group": tier_group_for(row["target_license_tier"]),
            "recommended_source_tier": row["target_license_tier"],
            "primary_vendor": row["target_vendor"],
            "primary_vendor_sku": row["target_sku_id"],
            "primary_vendor_sku_name": row["target_sku_name"],
            "current_vendor": row["current_vendor"],
            "current_source_tier": row["current_license_tier"],
            "procurement_motion": row["procurement_motion"],
            "portfolio_signal": row["portfolio_signal"],
            "fit_score": row["fit_score"],
            "switch_reason": row["switch_reason"],
            "rationale": row["match_rationale"],
        })

    return {
        "metadata": {
            "source": "case2_role_license_mapping_v1.csv",
            "tier_group_mapping": {
                "Standard": ["Viewer", "Editor"],
                "Pro": ["Full", "Developer"],
                "Premium": ["Enterprise"],
            },
            "record_count": len(rules),
        },
        "rules": rules,
    }


def build_vendor_benchmarks(vendor_rows):
    benchmark_rows = []
    for vendor_row in vendor_rows:
        for volume_band in parse_volume_discount_tiers(vendor_row["volume_discount_tiers"]):
            discount_multiplier = 1 - (volume_band["discount_percent"] / 100.0)
            resolved_price = round(vendor_row["proposed_unit_price"] * discount_multiplier, 2)
            benchmark_rows.append({
                "vendor_name": vendor_row["vendor_name"],
                "sku_id": vendor_row["sku_id"],
                "license_tier": vendor_row["license_tier"],
                "tier_group": vendor_row["tier_group"],
                "sku_name": vendor_row["sku_name"],
                "current_portfolio_status": vendor_row["current_portfolio_status"],
                "case2_request_motion": vendor_row["case2_request_motion"],
                "proposed_unit_price": vendor_row["proposed_unit_price"],
                "market_avg_price": vendor_row["market_avg_price"],
                "best_competitor_vendor": vendor_row["best_competitor_vendor"],
                "best_competitor_sku": vendor_row["competitor_alt"],
                "best_competitor_price": vendor_row["best_competitor_price"],
                "volume_band_min": volume_band["volume_band_min"],
                "volume_band_max": volume_band["volume_band_max"],
                "discount_percent": volume_band["discount_percent"],
                "resolved_unit_price": resolved_price,
            })
    return benchmark_rows


def print_summary(hr_rows, vendor_rows, role_rows):
    status_counts = Counter(row["is_active"] for row in hr_rows)
    vendor_counts = Counter(row["vendor_name"] for row in vendor_rows)
    motion_counts = Counter(row["procurement_motion"] for row in role_rows)
    tier_status_counts = Counter(row["current_portfolio_status"] for row in vendor_rows)

    print("\nCase 2 Data Generation Summary")
    print("------------------------------")
    print(f"HR rows read                     : {len(hr_rows):,}")
    print(f"Active employees                 : {status_counts['Active']:,}")
    print(f"Future hires                     : {status_counts['Future_Hire']:,}")
    print(f"Vendor catalog rows              : {len(vendor_rows):,}")
    print(f"Role-level mapping rows          : {len(role_rows):,}")
    print("Vendor catalog coverage          :")
    for vendor_name in sorted(vendor_counts):
        print(f"  {vendor_name:<28} {vendor_counts[vendor_name]:,}")
    print("Vendor portfolio status          :")
    for status in sorted(tier_status_counts):
        print(f"  {status:<28} {tier_status_counts[status]:,}")
    print("Procurement motion breakdown     :")
    for motion in sorted(motion_counts):
        print(f"  {motion:<28} {motion_counts[motion]:,}")


def main():
    hr_rows = read_hr_rows(HR_INPUT_FILE)
    role_rows = build_role_mapping(hr_rows)
    vendor_rows = build_vendor_catalog(hr_rows, role_rows)
    matching_logic = build_matching_logic(role_rows)
    benchmark_rows = build_vendor_benchmarks(vendor_rows)

    write_csv(
        VENDOR_OUTPUT_FILE,
        vendor_rows,
        [
            "vendor_name",
            "sku_id",
            "license_tier",
            "sku_name",
            "sku_family",
            "capability_description",
            "normalized_keywords",
            "unit_price_quote",
            "market_avg_price",
            "competitor_alt",
            "volume_discount_tiers",
            "default_department_fit",
            "min_job_level",
            "max_job_level",
            "current_portfolio_status",
            "tier_group",
            "proposed_unit_price",
            "best_competitor_vendor",
            "best_competitor_price",
            "baseline_active_seats",
            "active_upgrade_or_switch_candidates",
            "future_hire_demand_candidates",
            "case2_request_motion",
        ],
    )
    write_csv(
        ROLE_MAPPING_OUTPUT_FILE,
        role_rows,
        [
            "pillar_dept",
            "job_role",
            "job_level",
            "current_vendor",
            "current_license_tier",
            "current_sku_id",
            "current_sku_name",
            "target_vendor",
            "target_license_tier",
            "target_sku_id",
            "target_sku_name",
            "procurement_motion",
            "portfolio_signal",
            "fit_score",
            "price_band",
            "switch_reason",
            "match_rationale",
        ],
    )
    write_json(MATCHING_JSON_OUTPUT_FILE, matching_logic)
    write_csv(
        BENCHMARK_OUTPUT_FILE,
        benchmark_rows,
        [
            "vendor_name",
            "sku_id",
            "license_tier",
            "tier_group",
            "sku_name",
            "current_portfolio_status",
            "case2_request_motion",
            "proposed_unit_price",
            "market_avg_price",
            "best_competitor_vendor",
            "best_competitor_sku",
            "best_competitor_price",
            "volume_band_min",
            "volume_band_max",
            "discount_percent",
            "resolved_unit_price",
        ],
    )

    print_summary(hr_rows, vendor_rows, role_rows)
    print(f"Written vendor catalog            : {VENDOR_OUTPUT_FILE}")
    print(f"Written role-level mapping        : {ROLE_MAPPING_OUTPUT_FILE}")
    print(f"Written matching logic            : {MATCHING_JSON_OUTPUT_FILE}")
    print(f"Written vendor benchmarks         : {BENCHMARK_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
