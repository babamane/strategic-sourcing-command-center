import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd


BASE_DIR               = Path(__file__).resolve().parent
DATA_DIR               = BASE_DIR / "data"
HR_PATH                = DATA_DIR / "hr_data_v1.csv"
ROLE_MAPPING_PATH      = DATA_DIR / "case2_role_license_mapping_v1.csv"
VENDOR_CATALOG_PATH    = DATA_DIR / "case2_vendor_catalog_v1.csv"
MATCHING_LOGIC_PATH    = DATA_DIR / "matching_logic.json"
VENDOR_BENCHMARKS_PATH = DATA_DIR / "vendor_benchmarks.csv"
WORKSPACE_CONTEXT_PATH = DATA_DIR / "case2_workspace_context.json"

KNOWN_VENDORS = ["vendor_1", "vendor_2", "vendor_3"]
CASE2_KEYWORDS = [
    "license",
    "licenses",
    "licence",
    "demand",
    "need",
    "procure",
    "purchase",
    "buy",
    "upgrade",
    "vendor_3",
    "tooling",
    "workspace",
]

_CACHE = {}


def _load_csv_cached(key: str, path: Path) -> pd.DataFrame:
    if key not in _CACHE:
        _CACHE[key] = pd.read_csv(path)
    return _CACHE[key].copy()


def _load_json_cached(key: str, path: Path) -> dict:
    if key not in _CACHE:
        with open(path, "r", encoding="utf-8") as json_file:
            _CACHE[key] = json.load(json_file)
    return json.loads(json.dumps(_CACHE[key]))


def load_hr_data() -> pd.DataFrame:
    return _load_csv_cached("hr", HR_PATH)


def load_role_mapping() -> pd.DataFrame:
    return _load_csv_cached("role_mapping", ROLE_MAPPING_PATH)


def load_vendor_catalog() -> pd.DataFrame:
    return _load_csv_cached("vendor_catalog", VENDOR_CATALOG_PATH)


def load_matching_logic() -> dict:
    return _load_json_cached("matching_logic", MATCHING_LOGIC_PATH)


def load_vendor_benchmarks() -> pd.DataFrame:
    return _load_csv_cached("vendor_benchmarks", VENDOR_BENCHMARKS_PATH)


def is_case2_sourcing_request(message: str, history: list | None = None) -> bool:
    msg = message.lower()
    has_vendor = any(v in msg for v in KNOWN_VENDORS)
    has_case2_keyword = any(k in msg for k in CASE2_KEYWORDS)
    demand_phrase = any(
        phrase in msg
        for phrase in [
            "what would be my demand",
            "need licenses",
            "need license",
            "new licenses",
            "buy licenses",
            "upgrade to",
            "upgrade license",
        ]
    )
    return (has_vendor and has_case2_keyword) or demand_phrase


def _extract_vendor(message: str, history: list | None = None) -> str | None:
    msg = message.lower()
    for vendor in KNOWN_VENDORS:
        if vendor in msg:
            return vendor
    history = history or []
    for turn in reversed(history):
        content = turn.get("content", "").lower()
        for vendor in KNOWN_VENDORS:
            if vendor in content:
                return vendor
    return None


def _extract_count(message: str) -> int | None:
    match = re.search(r"\b(\d+)\b", message)
    return int(match.group(1)) if match else None


def _extract_level(message: str) -> str | None:
    match = re.search(r"\bL([1-7])\b", message, flags=re.IGNORECASE)
    return f"L{match.group(1)}" if match else None


def _extract_tier(message: str) -> str | None:
    tiers = ["enterprise", "developer", "premium", "standard", "viewer", "editor", "full", "pro"]
    msg = message.lower()
    for tier in tiers:
        if re.search(rf"\b{re.escape(tier)}\b", msg):
            return tier.title()
    return None


def _extract_role(message: str, hr_df: pd.DataFrame) -> str | None:
    msg = message.lower()
    roles = sorted(hr_df["job_role"].dropna().unique(), key=len, reverse=True)
    for role in roles:
        if role.lower() in msg:
            return role
    return None


def _extract_department(message: str, hr_df: pd.DataFrame) -> str | None:
    msg = message.lower()
    departments = sorted(hr_df["pillar_dept"].dropna().unique(), key=len, reverse=True)
    for dept in departments:
        if dept.lower() in msg:
            return dept
    return None


def _extract_license_placeholder(message: str) -> str | None:
    match = re.search(r"license\s+([a-zA-Z0-9_\-]+)", message, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _extract_requested_sku(message: str, vendor_name: str | None) -> dict:
    """
    Resolve explicit SKU intent from message using vendor catalog entries.
    """
    msg = message.lower()
    catalog = load_vendor_catalog().copy()
    if vendor_name:
        catalog = catalog[catalog["vendor_name"].str.lower() == vendor_name.lower()]
    if catalog.empty:
        return {"requested_sku_id": None, "requested_sku_name": None}

    # Prefer exact sku_name phrase matches (longest first), then sku_id token matches.
    candidates = []
    for _, row in catalog.iterrows():
        sku_name = str(row.get("sku_name", "")).strip()
        sku_id = str(row.get("sku_id", "")).strip()
        if sku_name and sku_name.lower() in msg:
            candidates.append((len(sku_name), sku_id, sku_name))
        elif sku_id and sku_id.lower() in msg:
            candidates.append((len(sku_id), sku_id, sku_name))

    if not candidates:
        return {"requested_sku_id": None, "requested_sku_name": None}

    candidates.sort(reverse=True)
    _, resolved_id, resolved_name = candidates[0]
    return {"requested_sku_id": resolved_id or None, "requested_sku_name": resolved_name or None}


def extract_case2_request(message: str, history: list | None = None) -> dict:
    hr_df = load_hr_data()
    vendor_name = _extract_vendor(message, history)
    requested_sku = _extract_requested_sku(message, vendor_name)
    return {
        "vendor_name": vendor_name,
        "requested_count": _extract_count(message),
        "job_level": _extract_level(message),
        "requested_tier": _extract_tier(message),
        "job_role": _extract_role(message, hr_df),
        "pillar_dept": _extract_department(message, hr_df),
        "license_placeholder": _extract_license_placeholder(message),
        "requested_sku_id": requested_sku["requested_sku_id"],
        "requested_sku_name": requested_sku["requested_sku_name"],
        "message": message,
    }


def build_case2_workspace_view() -> pd.DataFrame:
    hr_df = load_hr_data()
    role_df = load_role_mapping()
    benchmarks_df = load_vendor_benchmarks()

    merged = hr_df.merge(
        role_df,
        on=["pillar_dept", "job_role", "job_level"],
        how="left",
    )
    merged["employee_status"] = merged["is_active"].replace({
        "Active": "Active",
        "Future_Hire": "Future_Hire",
    })

    demand_counts = (
        merged.groupby("target_sku_id")
        .size()
        .reset_index(name="total_project_demand")
    )
    merged = merged.merge(demand_counts, on="target_sku_id", how="left")

    benchmark_choice = benchmarks_df[
        (benchmarks_df["volume_band_min"] <= benchmarks_df["volume_band_max"])
    ].copy()
    benchmark_choice = benchmark_choice.rename(columns={"sku_id": "target_sku_id"})
    merged = merged.merge(
        benchmark_choice,
        on="target_sku_id",
        how="left",
        suffixes=("", "_benchmark"),
    )

    eligible = (
        (merged["total_project_demand"] >= merged["volume_band_min"])
        & (merged["total_project_demand"] <= merged["volume_band_max"])
    )
    merged = merged[eligible].copy()
    merged["resolved_unit_price"] = merged["resolved_unit_price"].fillna(merged["proposed_unit_price"])
    merged["projected_annual_cost"] = merged["resolved_unit_price"] * 12
    merged["market_avg_annual_cost"] = merged["market_avg_price"] * 12
    merged["competitor_annual_cost"] = merged["best_competitor_price"] * 12
    return merged


def filter_workspace_view(df: pd.DataFrame, request: dict) -> pd.DataFrame:
    filtered = df.copy()
    if request.get("vendor_name"):
        filtered = filtered[filtered["target_vendor"] == request["vendor_name"]]
    if request.get("requested_sku_id"):
        filtered = filtered[filtered["target_sku_id"] == request["requested_sku_id"]]
    elif request.get("requested_sku_name"):
        filtered = filtered[
            filtered["target_sku_name"].str.lower().eq(str(request["requested_sku_name"]).lower())
        ]
    if request.get("pillar_dept"):
        filtered = filtered[filtered["pillar_dept"] == request["pillar_dept"]]
    if request.get("job_role"):
        filtered = filtered[filtered["job_role"] == request["job_role"]]
    if request.get("job_level"):
        filtered = filtered[filtered["job_level"] == request["job_level"]]
    if request.get("requested_tier"):
        source_tier = request["requested_tier"]
        filtered = filtered[
            filtered["target_license_tier"].str.lower().eq(source_tier.lower())
            | filtered["tier_group"].str.lower().eq(source_tier.lower())
        ]
    return filtered


def build_case2_workspace_payload(request: dict) -> dict:
    workspace_df = build_case2_workspace_view()
    filtered = filter_workspace_view(workspace_df, request)
    if filtered.empty:
        filtered = workspace_df[workspace_df["target_vendor"] == request.get("vendor_name")] if request.get("vendor_name") else workspace_df

    top_roles = (
        filtered.groupby("job_role")
        .size()
        .sort_values(ascending=False)
        .head(4)
        .index.tolist()
    )

    sku_summary = (
        filtered.groupby(
            ["target_vendor", "target_sku_id", "target_sku_name", "target_license_tier", "tier_group"],
            dropna=False,
        )
        .agg(
            mapped_users=("employee_id", "count"),
            active_users=("employee_status", lambda s: int((s == "Active").sum())),
            future_hires=("employee_status", lambda s: int((s == "Future_Hire").sum())),
            resolved_unit_price=("resolved_unit_price", "first"),
            market_avg_price=("market_avg_price", "first"),
            best_competitor_price=("best_competitor_price", "first"),
        )
        .reset_index()
        .sort_values(["mapped_users", "target_sku_id"], ascending=[False, True])
    )
    if sku_summary.empty:
        sku_summary = pd.DataFrame([{
            "target_vendor": request.get("vendor_name"),
            "target_sku_id": None,
            "target_sku_name": None,
            "target_license_tier": request.get("requested_tier"),
            "tier_group": None,
            "mapped_users": 0,
            "active_users": 0,
            "future_hires": 0,
            "resolved_unit_price": 0.0,
            "market_avg_price": 0.0,
            "best_competitor_price": 0.0,
        }])

    lead_row = sku_summary.iloc[0]
    explicit_sku_focus = bool(request.get("requested_sku_id") or request.get("requested_sku_name"))

    if explicit_sku_focus:
        requested_count = request.get("requested_count") or int(lead_row["mapped_users"] or 0)
        requested_count = max(requested_count, 1)
        annual_spend = float(lead_row["resolved_unit_price"]) * requested_count * 12
        negotiation_delta = (
            float(lead_row["resolved_unit_price"]) - float(lead_row["market_avg_price"])
        ) * requested_count * 12
    else:
        annual_spend = float(
            (
                sku_summary["mapped_users"]
                * sku_summary["resolved_unit_price"]
                * 12
            ).sum()
        )
        negotiation_delta = float(
            (
                (sku_summary["resolved_unit_price"] - sku_summary["market_avg_price"])
                * sku_summary["mapped_users"]
                * 12
            ).sum()
        )

    payload = {
        "request": request,
        "workspace_defaults": {
            "vendor_name": request.get("vendor_name") or lead_row["target_vendor"],
            "pillar_dept": request.get("pillar_dept"),
            "job_role": request.get("job_role"),
            "job_level": request.get("job_level"),
            "top_roles": top_roles,
            "focus_sku_id": request.get("requested_sku_id") if explicit_sku_focus else None,
            "focus_sku_name": request.get("requested_sku_name") if explicit_sku_focus else None,
            "lock_to_requested_license": explicit_sku_focus,
        },
        "kpis": {
            "total_project_demand": int(filtered["employee_id"].count()),
            "future_hire_demand": int((filtered["employee_status"] == "Future_Hire").sum()),
            "estimated_annual_spend": round(annual_spend, 2),
            "negotiation_delta": round(negotiation_delta, 2),
        },
        "recommended_sku": {
            "vendor_name": lead_row["target_vendor"],
            "sku_id": lead_row["target_sku_id"],
            "sku_name": lead_row["target_sku_name"],
            "license_tier": lead_row["target_license_tier"],
            "tier_group": lead_row["tier_group"],
            "mapped_users": int(lead_row["mapped_users"]),
            "active_users": int(lead_row["active_users"]),
            "future_hires": int(lead_row["future_hires"]),
            "resolved_unit_price": float(lead_row["resolved_unit_price"]),
            "market_avg_price": float(lead_row["market_avg_price"]),
            "best_competitor_price": float(lead_row["best_competitor_price"]),
        },
    }
    return payload


def _infer_defaults_from_data(request: dict, workspace_df: pd.DataFrame) -> dict:
    """
    Preserve user-requested scope for filters.
    Do not force department/role/level defaults when user did not ask for them.
    """
    return dict(request)


def save_workspace_context(payload: dict) -> None:
    with open(WORKSPACE_CONTEXT_PATH, "w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2)


# -------------------------------
# Streamlit auto-launcher
# -------------------------------
STREAMLIT_PORT = 8585
_streamlit_proc = None


def _launch_streamlit() -> str:
    """Start case2_workspace_v1.py via Streamlit if not already running.
    Returns the local URL."""
    global _streamlit_proc
    workspace_file = BASE_DIR / "case2_workspace_v1.py"
    # Check if process is still alive
    if _streamlit_proc is None or _streamlit_proc.poll() is not None:
        _streamlit_proc = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run",
                str(workspace_file),
                "--server.port", str(STREAMLIT_PORT),
                "--server.headless", "true",
            ],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return f"http://localhost:{STREAMLIT_PORT}"


def handle_case2_query(message: str, history: list | None = None, session_id: str = "default") -> str:
    request = extract_case2_request(message, history or [])
    if not request.get("vendor_name"):
        return "For this sourcing workspace flow, tell me which vendor you want to analyze, for example `vendor_3`."

    base_workspace = build_case2_workspace_view()
    enriched_request = _infer_defaults_from_data(request, base_workspace)
    payload = build_case2_workspace_payload(enriched_request)
    save_workspace_context(payload)

    sku  = payload["recommended_sku"]
    kpis = payload["kpis"]
    vendor_exists     = not base_workspace[base_workspace["target_vendor"] == request.get("vendor_name")].empty
    license_requested = bool(request.get("license_placeholder") or request.get("requested_sku_name") or request.get("requested_sku_id"))
    license_found     = bool(request.get("requested_sku_name") or request.get("requested_sku_id"))

    if not vendor_exists:
        status_message = (
            "Vendor context update:\n"
            "- This appears to be a new vendor not currently available in our active environment.\n"
            "- Proceeding with an initial demand workspace using available baseline mappings.\n\n"
        )
    elif license_requested and not license_found:
        status_message = (
            "Catalog context update:\n"
            "- Vendor exists in current environment, but the requested license is not present in the active catalog.\n"
            "- Proceeding with closest-fit demand analysis and baseline sourcing recommendations.\n\n"
        )
    else:
        status_message = (
            "Sourcing context update:\n"
            "- Vendor and requested context are recognized in current environment.\n"
            "- Proceeding with demand workspace initialization.\n\n"
        )

    # Launch Streamlit in the background and get the URL
    workspace_url = _launch_streamlit()

    return (
        "Case 2 Strategic Sourcing route selected.\n\n"
        + status_message
        + f"Request focus:\n"
        + f"- Vendor: {payload['workspace_defaults']['vendor_name']}\n"
        + f"- Procurement SKU focus: {payload['workspace_defaults'].get('focus_sku_name') or 'All vendor capabilities'}\n"
        + f"- Department: {payload['workspace_defaults'].get('pillar_dept') or 'All'}\n"
        + f"- Role: {payload['workspace_defaults'].get('job_role') or 'All'}\n"
        + f"- Level: {payload['workspace_defaults'].get('job_level') or 'All'}\n\n"
        + f"Initial sourcing view:\n"
        + f"- Top recommended SKU: {sku['sku_name']} ({sku['sku_id']})\n"
        + f"- Tier: {sku['license_tier']} / {sku['tier_group']}\n"
        + f"- Mapped demand: {sku['mapped_users']} users\n"
        + f"- Future hires: {sku['future_hires']}\n"
        + f"- Estimated annual spend: ${kpis['estimated_annual_spend']:,.2f}\n"
        + f"- Negotiation delta vs market average: ${kpis['negotiation_delta']:,.2f}\n\n"
        + f"[Open Demand Discovery Workspace]({workspace_url})"
    )
