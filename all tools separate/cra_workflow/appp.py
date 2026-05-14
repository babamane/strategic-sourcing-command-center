import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
from dotenv import load_dotenv
from pandas.tseries.offsets import MonthBegin

# Load environment variables
load_dotenv()
DATA_DIR = os.getenv("DATA_DIR", "data")

st.set_page_config(layout="wide", page_title="Contract Renewal Agent", page_icon="🦋")

# ═══════════════════════════════════════════════════════════
# DESIGN TOKENS
# ═══════════════════════════════════════════════════════════
COLOR_GREEN      = "#22C55E"
COLOR_AMBER      = "#F59E0B"
COLOR_RED        = "#EF4444"
COLOR_BLUE       = "#3B82F6"
COLOR_INDIGO     = "#6366F1"
COLOR_GRAY       = "#94A3B8"
COLOR_GRAY_LIGHT = "#E2E8F0"
COLOR_TEXT       = "#0F172A"
COLOR_TEXT_MUTED = "#64748B"
COLOR_BG         = "#F8FAFC"
COLOR_CARD_BG    = "#FFFFFF"
COLOR_BORDER     = "#E2E8F0"

NAV_BG       = "#0F172A"
NAV_BORDER   = "#1E293B"
NAV_TEXT     = "#CBD5E1"
NAV_TEXT_DIM = "#64748B"

FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif"

# Chart layout — t=60 so horizontal legend at y=1.02 never clips the title
# b=44 gives enough room for -35-degree rotated x-labels
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    template     ="simple_white",
    showlegend   =True,
    xaxis=dict(showgrid=True,  gridcolor="#F1F5F9", zeroline=False, linecolor="#E2E8F0"),
    yaxis=dict(showgrid=True,  gridcolor="#F1F5F9", zeroline=False, linecolor="#E2E8F0"),
    font=dict(size=12, family=FONT, color=COLOR_TEXT),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0)", font=dict(size=11),
    ),
    margin=dict(l=16, r=16, t=60, b=44),
    hoverlabel=dict(bgcolor="white", font_size=12, font_family=FONT, bordercolor=COLOR_BORDER),
)

# Standardised chart heights — all paired charts share H_HALF so columns align
H_MAIN  = 400   # full-width charts
H_HALF  = 340   # side-by-side (both columns MUST use this value)
H_SMALL = 300   # secondary full-width charts

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except Exception:
    ExponentialSmoothing = None


# ═══════════════════════════════════════════════════════════
# GLOBAL CSS
# ═══════════════════════════════════════════════════════════
def inject_global_style() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* ── Base ── */
        html, body, .stApp {{
            font-family: {FONT};
            background: {COLOR_BG};
            color: {COLOR_TEXT};
        }}
        /* Zero out block-container padding — we control spacing per-column below */
        .block-container {{
            padding: 0 0 1.5rem 0 !important;
            max-width: 100% !important;
        }}
        h1, h2, h3, h4, h5, h6 {{ font-family: {FONT}; color: {COLOR_TEXT}; }}

        /* ── Nav column (first st.columns child) — dark shell ── */
        [data-testid="column"]:first-child {{
            background: {NAV_BG};
            border-right: 1px solid {NAV_BORDER};
            min-height: 100vh;
            padding: 0 !important;
        }}
        [data-testid="column"]:first-child label,
        [data-testid="column"]:first-child p,
        [data-testid="column"]:first-child .stMarkdown {{
            color: {NAV_TEXT} !important;
        }}
        [data-testid="column"]:first-child [data-baseweb="select"] > div,
        [data-testid="column"]:first-child [data-baseweb="input"] > div {{
            background: #1E293B !important;
            border-color: #334155 !important;
        }}
        [data-testid="column"]:first-child [data-baseweb="tag"] {{
            background: #334155 !important;
        }}
        [data-testid="column"]:first-child hr {{
            border-color: {NAV_BORDER} !important;
        }}
        /* Nav buttons */
        [data-testid="column"]:first-child .stButton > button {{
            background: transparent !important;
            border: 1px solid transparent !important;
            color: {NAV_TEXT} !important;
            border-radius: 7px !important;
            text-align: left !important;
            font-size: 0.82rem !important;
            padding: 0.4rem 0.85rem !important;
            width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        [data-testid="column"]:first-child .stButton > button:hover {{
            background: #1E293B !important;
            color: #E2E8F0 !important;
        }}

        /* ── Content column padding ── */
        [data-testid="column"]:not(:first-child) {{
            padding: 1.1rem 1.6rem 1.5rem 1.1rem !important;
        }}

        /* ── Metric cards ──
             font-size 1.4rem → long "$12,345,678" fits safely inside 4-column grid */
        [data-testid="metric-container"] {{
            background: {COLOR_CARD_BG};
            border: 1px solid {COLOR_BORDER};
            border-radius: 10px;
            padding: 0.8rem 1rem 0.75rem 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,.06);
            position: relative;
            overflow: hidden;
        }}
        [data-testid="metric-container"]::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, {COLOR_BLUE}, {COLOR_INDIGO});
            border-radius: 10px 10px 0 0;
        }}
        [data-testid="metric-container"] label {{
            color: {COLOR_TEXT_MUTED} !important;
            font-size: 0.67rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }}
        [data-testid="metric-container"] [data-testid="stMetricValue"] {{
            color: {COLOR_TEXT} !important;
            font-weight: 700 !important;
            font-size: 1.4rem !important;
            line-height: 1.2;
        }}
        [data-testid="metric-container"] [data-testid="stMetricDelta"] {{
            font-size: 0.7rem !important;
        }}

        /* ── Content-area buttons ── */
        [data-testid="column"]:not(:first-child) .stButton > button {{
            border-radius: 7px;
            border: 1px solid {COLOR_BORDER};
            color: {COLOR_TEXT};
            background: {COLOR_CARD_BG};
            font-weight: 500;
            font-size: 0.8rem;
            padding: 0.28rem 0.7rem;
            transition: all .15s ease;
        }}
        [data-testid="column"]:not(:first-child) .stButton > button:hover {{
            border-color: {COLOR_BLUE};
            background: #EFF6FF;
            color: {COLOR_BLUE};
        }}

        /* ── Download button ── */
        [data-testid="stDownloadButton"] > button {{
            background: {COLOR_BLUE} !important;
            color: white !important;
            border: none !important;
            border-radius: 7px !important;
            font-weight: 600 !important;
            font-size: 0.81rem !important;
            padding: 0.38rem 1.05rem !important;
        }}
        [data-testid="stDownloadButton"] > button:hover {{
            background: #2563EB !important;
        }}

        /* ── Alert boxes ── */
        [data-testid="stAlert"] {{
            border-radius: 8px;
            border-width: 1px;
            font-size: 0.81rem;
            padding: 0.5rem 0.85rem;
        }}

        /* ── Dataframe ── */
        [data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid {COLOR_BORDER};
        }}

        /* ── Dividers ── */
        hr {{ border-color: {COLOR_BORDER}; margin: 0.45rem 0; }}

        /* ── Page title ── */
        .page-title-block {{
            border-left: 4px solid {COLOR_BLUE};
            padding: 0.18rem 0 0.18rem 0.75rem;
            margin-bottom: 0.85rem;
        }}
        .page-title-block h1 {{
            font-size: 1.3rem;
            font-weight: 800;
            margin: 0 0 0.06rem 0;
            color: {COLOR_TEXT};
            line-height: 1.2;
        }}
        .page-title-block p {{
            font-size: 0.76rem;
            margin: 0;
            color: {COLOR_TEXT_MUTED};
        }}

        /* ── Section headers ── */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            /* reduced top margin so no double-spacing after st.divider() */
            margin: 0.75rem 0 0.4rem 0;
        }}
        .section-header .pill {{
            background: #EFF6FF;
            color: {COLOR_BLUE};
            font-size: 0.67rem;
            font-weight: 700;
            padding: 2px 9px;
            border-radius: 999px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            border: 1px solid #BFDBFE;
            white-space: nowrap;
        }}
        .section-header h3 {{
            margin: 0;
            font-size: 0.98rem;
            font-weight: 700;
            color: {COLOR_TEXT};
        }}

        /* ── Nav brand ── */
        .nav-brand {{
            padding: 1.1rem 0.9rem 0.8rem 0.9rem;
            border-bottom: 1px solid {NAV_BORDER};
            margin-bottom: 0.3rem;
        }}
        .nav-brand .brand-name {{
            font-size: 0.9rem;
            font-weight: 800;
            color: #F8FAFC;
        }}
        .nav-brand .brand-sub {{
            font-size: 0.62rem;
            color: {NAV_TEXT_DIM};
            margin-top: 2px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        /* ── Nav section labels ── */
        .nav-label {{
            font-size: 0.59rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: {NAV_TEXT_DIM};
            padding: 0.7rem 0.9rem 0.22rem 0.9rem;
        }}
        .nav-label-border {{
            border-top: 1px solid {NAV_BORDER};
            margin-top: 0.3rem;
        }}

        /* ── Butterfly rule rows ── */
        .rule-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.26rem 0.9rem;
        }}
        .rule-label {{ font-size: 0.71rem; color: {NAV_TEXT}; }}
        .rule-badge {{
            border-radius: 999px;
            padding: 1px 8px;
            font-size: 0.64rem;
            font-weight: 700;
            color: white;
            min-width: 20px;
            text-align: center;
        }}

        /* ── Legend row ── */
        .legend-row {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin: 3px 0 7px 0;
            font-size: 0.72rem;
            color: {COLOR_TEXT_MUTED};
        }}
        .legend-dot {{
            width: 8px; height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
            vertical-align: middle;
        }}

        /* ── View-level caption pill ── */
        .view-caption {{
            font-size: 0.71rem;
            color: {COLOR_TEXT_MUTED};
            margin-bottom: 0.5rem;
            padding: 0.28rem 0.55rem;
            background: #F1F5F9;
            border-radius: 6px;
            display: inline-block;
        }}

        /* ── Widget labels in content area ── */
        [data-testid="column"]:not(:first-child) .stSelectbox label,
        [data-testid="column"]:not(:first-child) .stMultiSelect label,
        [data-testid="column"]:not(:first-child) .stSlider label {{
            font-size: 0.71rem !important;
            font-weight: 600 !important;
            color: {COLOR_TEXT_MUTED} !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════
# DATA LOADING  (logic unchanged)
# ═══════════════════════════════════════════════════════════
@st.cache_data
def load_base_data() -> pd.DataFrame:
    csv_path = os.path.join(DATA_DIR, "merged_dataset_FINAL_fabricated_1341_util_adjusted.csv")
    df = pd.read_csv(csv_path)
    df["Start_Date"] = pd.to_datetime(df["Start_Date"], dayfirst=True, errors="coerce")
    df["End_Date"]   = pd.to_datetime(df["End_Date"],   dayfirst=True, errors="coerce")
    df["Stages"]     = df["Stages"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["Stages"]     = df["Stages"].replace({"Approval,": "Approval"})
    numeric_cols = [
        "Days_to_Renewal", "Total_Users", "Active_Users",
        "Avg_Utilization_Pct", "Total_Annual_Budget_USD",
        "Total_Actual_Spend_USD", "Spend%", "Total_True_Up_USD", "Max_Days_in_Stage",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def generate_sample_data(base_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    np.random.seed(42)
    n            = len(base_df)
    contract_ids = base_df["Contract_ID"].values

    uptime         = np.clip(np.random.normal(loc=99.5, scale=0.8, size=n), 95.0, 100.0)
    sla_breaches   = np.clip(np.random.poisson(lam=3, size=n), 0, 20)
    critical_ratio = np.round(np.random.uniform(0.0, 0.25, size=n), 2)
    score = (100.0 - (sla_breaches * 3) - (critical_ratio * 60)
             - np.maximum(0, (99.9 - uptime) * 10))
    performance_score   = np.clip(score, 20, 100).astype(int)
    performance_segment = np.where(
        performance_score >= 80, "Good",
        np.where(performance_score >= 60, "Average", "Poor"),
    )
    vendor_perf_df = pd.DataFrame({
        "Contract_ID"          : contract_ids,
        "uptime_pct"           : uptime.round(2),
        "sla_breaches"         : sla_breaches.astype(int),
        "critical_ticket_ratio": critical_ratio,
        "performance_score"    : performance_score,
        "performance_segment"  : performance_segment,
    })

    prev_cost     = base_df["Total_Annual_Budget_USD"] * np.random.uniform(0.85, 1.05, size=n)
    curr_cost     = base_df["Total_Actual_Spend_USD"]
    market_idx    = np.round(np.random.uniform(0.90, 1.15, size=n), 3)
    price_change  = np.round(((curr_cost - prev_cost) / prev_cost) * 100, 1)
    overpriced    = (curr_cost > (base_df["Total_Annual_Budget_USD"] * market_idx)).astype(int)
    contract_type = np.random.choice(["MSA", "Order Form", "Amendment"], size=n, p=[0.2, 0.6, 0.2])
    hist_df = pd.DataFrame({
        "Contract_ID"           : contract_ids,
        "previous_cost_per_unit": prev_cost.round(2),
        "current_cost_per_unit" : curr_cost.round(2),
        "price_change_pct"      : price_change,
        "market_price_index"    : market_idx,
        "overpriced_flag"       : overpriced,
        "contract_type"         : contract_type,
    })
    return vendor_perf_df, hist_df


# ═══════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════
def style_fig(fig: go.Figure) -> go.Figure:
    fig.update_layout(**CHART_LAYOUT)
    fig.update_traces(marker_line_width=0)
    return fig


def get_chart_subset(df: pd.DataFrame, max_items: int) -> pd.DataFrame:
    if len(df) <= max_items:
        return df.copy()
    return df.nsmallest(max_items, "Days_to_Renewal").copy()


# ═══════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════
def page_title(icon: str, title: str, subtitle: str = "") -> None:
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"<div class='page-title-block'><h1>{icon} {title}</h1>{sub}</div>",
        unsafe_allow_html=True,
    )


def section_header(label: str, pill: str = "") -> None:
    pill_html = f"<span class='pill'>{pill}</span>" if pill else ""
    st.markdown(
        f"<div class='section-header'>{pill_html}<h3>{label}</h3></div>",
        unsafe_allow_html=True,
    )


def render_butterfly_rule_legend() -> None:
    st.markdown(
        f"<div class='legend-row'>"
        f"<span><span class='legend-dot' style='background:{COLOR_AMBER}'></span>Under-utilized (<35%)</span>"
        f"<span><span class='legend-dot' style='background:{COLOR_RED}'></span>Over-utilized (>90%)</span>"
        f"<span><span class='legend-dot' style='background:{COLOR_GREEN}'></span>Balanced (35%-90%)</span>"
        "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════
# FORECASTING  (logic unchanged)
# ═══════════════════════════════════════════════════════════
def forecast_next_4_months(monthly_actual: pd.Series) -> pd.Series:
    monthly_actual = monthly_actual.sort_index()
    if len(monthly_actual) < 3:
        idx = pd.date_range(
            (monthly_actual.index.max() + MonthBegin(1)) if len(monthly_actual)
            else pd.Timestamp.today().to_period("M").to_timestamp() + MonthBegin(1),
            periods=4, freq="MS",
        )
        base = float(monthly_actual.iloc[-1]) if len(monthly_actual) else 0.0
        return pd.Series([base] * 4, index=idx)

    forecast_index = pd.date_range(monthly_actual.index.max() + MonthBegin(1), periods=4, freq="MS")
    if ExponentialSmoothing is not None and len(monthly_actual) >= 6:
        model = ExponentialSmoothing(
            monthly_actual.astype(float), trend="add", seasonal=None,
            initialization_method="estimated",
        )
        fit = model.fit(optimized=True)
        return pd.Series(fit.forecast(4).values, index=forecast_index)

    deltas    = monthly_actual.diff().dropna()
    avg_delta = float(deltas.tail(min(6, len(deltas))).mean()) if len(deltas) else 0.0
    start     = float(monthly_actual.iloc[-1])
    return pd.Series(
        [max(0.0, start + avg_delta * (i + 1)) for i in range(4)],
        index=forecast_index,
    )


# ═══════════════════════════════════════════════════════════
# RENEWAL ACTION  (logic unchanged)
# ═══════════════════════════════════════════════════════════
def renewal_action(row: pd.Series) -> str:
    if row["Days_to_Renewal"] <= 30:
        return "🔴 CRITICAL: Renew Immediately"
    if row["performance_score"] < 60 and row["overpriced_flag"] == 1:
        return "🔴 Renegotiate: Poor performance + overpriced"
    if row["Avg_Utilization_Pct"] < 70 and row["overpriced_flag"] == 1:
        return "🔴 Reduce + Renegotiate: Over-licensed + overpriced"
    if row["Avg_Utilization_Pct"] < 70:
        return "🟡 Right-size: Reduce license count before renewal"
    if row["overpriced_flag"] == 1:
        return "🟡 Negotiate: Price above market rate"
    if row["performance_score"] < 60:
        return "🟡 Review: Poor vendor performance — request SLA credits"
    if row["Budget_Status"] == "Exceeded":
        return "🟡 Audit: Spend exceeded budget"
    return "🟢 Renew: No issues flagged"


# ═══════════════════════════════════════════════════════════
# NAV PANEL  (left column)
# ═══════════════════════════════════════════════════════════
def build_left_panel(master_df: pd.DataFrame) -> tuple[pd.DataFrame, str, str, int]:
    collapsed = st.session_state.get("v5_nav_collapsed", False)

    # Brand header
    if not collapsed:
        st.markdown(
            "<div class='nav-brand'>"
            "<div class='brand-name'>🦋 CRA Platform</div>"
            "<div class='brand-sub'>Contract Renewal Agent</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='padding:0.9rem 0 0.4rem;text-align:center;font-size:1.25rem;'>🦋</div>",
            unsafe_allow_html=True,
        )

    # Toggle
    if collapsed:
        if st.button("▶", key="v5_nav_toggle_open", use_container_width=True):
            st.session_state["v5_nav_collapsed"] = False
            st.rerun()
    else:
        if st.button("◀  Dashboard", key="v5_nav_toggle_close", use_container_width=True):
            st.session_state["v5_nav_collapsed"] = True
            st.rerun()

    # Navigation
    if not collapsed:
        st.markdown("<div class='nav-label'>Navigation</div>", unsafe_allow_html=True)

    page_options = [
        ("📋 Actions Dashboard",  "📋"),
        ("🧩 License analysis",     "🧩"),
        ("💰 Budget Analysis",    "💰"),
        ("📈 Vendor Performance", "📈"),
    ]

    if "v5_page" not in st.session_state:
        st.session_state["v5_page"] = page_options[0][0]

    for page_name, short_name in page_options:
        label = short_name if collapsed else page_name
        if st.button(label, use_container_width=True, key=f"v5_nav_{page_name}"):
            st.session_state["v5_page"] = page_name
            st.rerun()

    page = st.session_state["v5_page"]

    # Filter keys
    owner_opts  = sorted(master_df["Owner"].dropna().unique().tolist())
    vendor_opts = sorted(master_df["Vendor"].dropna().unique().tolist())
    crit_opts   = sorted(master_df["Criticality"].dropna().unique().tolist())

    owner_key  = "v5_owner_sel";   vendor_key = "v5_vendor_sel"; crit_key = "v5_crit_sel"
    lic_key    = "v5_lic_sel";     con_key    = "v5_con_sel";    view_key = "v5_view_level"
    max_key    = "v5_max_items"

    if owner_key  not in st.session_state: st.session_state[owner_key]  = owner_opts
    if vendor_key not in st.session_state: st.session_state[vendor_key] = vendor_opts
    if crit_key   not in st.session_state: st.session_state[crit_key]   = crit_opts
    if view_key   not in st.session_state: st.session_state[view_key]   = "Vendor"
    if max_key    not in st.session_state: st.session_state[max_key]    = 20

    if not collapsed:
        st.markdown("<div class='nav-label nav-label-border'>Filters</div>", unsafe_allow_html=True)

        owner_sel  = st.multiselect("Owner",       owner_opts,  default=st.session_state[owner_key],  key=owner_key)
        vendor_sel = st.multiselect("Vendor",      vendor_opts, default=st.session_state[vendor_key], key=vendor_key)
        crit_sel   = st.multiselect("Criticality", crit_opts,   default=st.session_state[crit_key],   key=crit_key)

        vf       = master_df[master_df["Vendor"].isin(vendor_sel)]
        lic_opts = sorted(vf["License_Type"].dropna().unique().tolist())
        lic_sel  = st.multiselect(
            "License Type", lic_opts,
            default=[v for v in st.session_state.get(lic_key, lic_opts) if v in lic_opts],
            key=lic_key,
        )

        cf       = vf[vf["License_Type"].isin(lic_sel)]
        con_opts = sorted(cf["Contract_ID"].dropna().unique().tolist())
        con_sel  = st.multiselect(
            "Contract ID", con_opts,
            default=[v for v in st.session_state.get(con_key, con_opts) if v in con_opts],
            key=con_key,
        )

        view_level      = st.radio("View Level", ["Vendor", "Contract"], horizontal=True, key=view_key)
        max_chart_items = int(st.slider("Chart items", 5, 50, int(st.session_state[max_key]), 5, key=max_key))
    else:
        owner_sel       = st.session_state.get(owner_key,  owner_opts)
        vendor_sel      = st.session_state.get(vendor_key, vendor_opts)
        crit_sel        = st.session_state.get(crit_key,   crit_opts)
        lic_sel         = st.session_state.get(lic_key,    [])
        con_sel         = st.session_state.get(con_key,    [])
        view_level      = st.session_state.get(view_key,   "Vendor")
        max_chart_items = int(st.session_state.get(max_key, 20))

    # Butterfly rules
    if not collapsed:
        flt = master_df[
            master_df["Owner"].isin(owner_sel)
            & master_df["Vendor"].isin(vendor_sel)
            & master_df["Criticality"].isin(crit_sel)
            & (master_df["License_Type"].isin(lic_sel) if lic_sel else True)
            & (master_df["Contract_ID"].isin(con_sel)  if con_sel  else True)
        ]
        rules = [
            ("180-Day Alert",     ((flt["Days_to_Renewal"] <= 180) & (flt["Days_to_Renewal"] > 90)).sum(), COLOR_AMBER),
            ("90-Day Escalation", ((flt["Days_to_Renewal"] <= 90)  & (flt["Days_to_Renewal"] > 30)).sum(), COLOR_AMBER),
            ("30-Day Critical",   (flt["Days_to_Renewal"] <= 30).sum(),                                     COLOR_RED),
            ("Low Utilization",   (flt["Avg_Utilization_Pct"] < 70).sum(),                                  COLOR_RED),
            ("Budget Exceeded",   (flt["Budget_Status"] == "Exceeded").sum(),                               COLOR_RED),
            ("Poor Performance",  (flt["performance_score"] < 60).sum(),                                    COLOR_RED),
            ("Overpriced",        (flt["overpriced_flag"] == 1).sum(),                                      COLOR_AMBER),
        ]
        st.markdown("<div class='nav-label nav-label-border'>Butterfly Rules</div>", unsafe_allow_html=True)
        for lbl, cnt, clr in rules:
            st.markdown(
                f"<div class='rule-row'>"
                f"<span class='rule-label'>{lbl}</span>"
                f"<span class='rule-badge' style='background:{clr};'>{int(cnt)}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Master filter
    filtered = master_df[
        master_df["Owner"].isin(owner_sel)
        & master_df["Vendor"].isin(vendor_sel)
        & master_df["Criticality"].isin(crit_sel)
        & (master_df["License_Type"].isin(lic_sel) if lic_sel else True)
        & (master_df["Contract_ID"].isin(con_sel)  if con_sel  else True)
    ].copy()

    return filtered, page, view_level, max_chart_items


# ═══════════════════════════════════════════════════════════
# PAGE: ACTIONS DASHBOARD
# ═══════════════════════════════════════════════════════════
def render_actions_dashboard(df: pd.DataFrame, view_level: str, max_items: int) -> None:
    page_title("📋", "Actions Dashboard", "Unified contract risk signals and renewal recommendations")

    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("Total Contracts",    len(df))
    c2.metric("Contracts at Risk",  int(df["Renewal_Flag"].isin(["Warning", "Critical"]).sum()))
    c3.metric("Cap-Exceeded",       int((df["Budget_Status"] == "Exceeded").sum()))
    c4.metric("Avg Portfolio Util", f"{df['Avg_Utilization_Pct'].mean():.1f}%")

    subset = get_chart_subset(df, max_items)

    # ── Pillar 1 ──
    st.divider()
    section_header("License Utilization — Are we over-buying?", "Pillar 1 · Usage")
    usage = (
        subset.groupby("Vendor", as_index=False)["Avg_Utilization_Pct"].mean()
              .sort_values("Avg_Utilization_Pct")
        if view_level == "Vendor"
        else subset.sort_values("Avg_Utilization_Pct")[
            ["Contract_ID", "Avg_Utilization_Pct"]
        ].rename(columns={"Contract_ID": "Vendor"})
    )
    usage["color"] = np.where(
        usage["Avg_Utilization_Pct"] < 35, COLOR_AMBER,
        np.where(usage["Avg_Utilization_Pct"] > 90, COLOR_RED, COLOR_GREEN),
    )
    fig1 = go.Figure(go.Bar(
        x=usage["Avg_Utilization_Pct"], y=usage["Vendor"],
        orientation="h", marker_color=usage["color"],
        hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
    ))
    fig1.add_vline(x=70, line_dash="dot", line_color=COLOR_RED,
                   annotation_text="70% floor", annotation_font_size=10,
                   annotation_font_color=COLOR_RED)
    fig1.add_vline(x=85, line_dash="dot", line_color=COLOR_GREEN,
                   annotation_text="85% target", annotation_font_size=10,
                   annotation_font_color=COLOR_GREEN)
    fig1.update_layout(title_text="License Utilization by Vendor/Contract", height=H_MAIN)
    fig1.update_xaxes(range=[0, 110], ticksuffix="%")
    st.plotly_chart(style_fig(fig1), use_container_width=True)
    render_butterfly_rule_legend()

    n_low  = int((usage["Avg_Utilization_Pct"] < 70).sum())
    n_high = int((usage["Avg_Utilization_Pct"] > 90).sum())
    a1, a2 = st.columns(2, gap="small")
    a1.warning(f"🦋 **{n_low}** items below 70% — Low Utilization Rule active → optimization review task created")
    a2.info(   f"🦋 **{n_high}** items above 90% — High Utilization Rule active → capacity planning task created")

    # ── Pillar 2 ──
    st.divider()
    section_header("Vendor Performance — Are we getting what we paid for?", "Pillar 2 · Performance")
    perf = subset.copy()
    if view_level == "Vendor":
        perf = (
            perf.groupby("Vendor", as_index=False)
                .agg(performance_score=("performance_score", "mean"),
                     uptime_pct=("uptime_pct", "mean"),
                     sla_breaches=("sla_breaches", "sum"))
                .sort_values("performance_score")
        )
        y_vals = perf["Vendor"]
    else:
        perf   = perf.sort_values("performance_score")
        y_vals = perf["Contract_ID"]
    perf["uptime_scaled"] = ((perf["uptime_pct"] - 95) / 5 * 100).clip(0, 100)

    fig2 = go.Figure()
    fig2.add_bar(y=y_vals, x=perf["performance_score"], orientation="h",
                 name="Performance Score", marker_color=COLOR_BLUE,
                 hovertemplate="%{y}: <b>%{x:.0f}</b><extra>Score</extra>")
    fig2.add_bar(y=y_vals, x=perf["uptime_scaled"], orientation="h",
                 name="Uptime (scaled)", marker_color=COLOR_GRAY,
                 hovertemplate="%{y}: <b>%{x:.0f}</b><extra>Uptime</extra>")
    fig2.add_vline(x=60, line_dash="dot", line_color=COLOR_RED,
                   annotation_text="60 threshold", annotation_font_size=10,
                   annotation_font_color=COLOR_RED)
    fig2.update_layout(title_text="Vendor Performance Scorecard", barmode="group", height=H_MAIN)
    st.plotly_chart(style_fig(fig2), use_container_width=True)

    n_poor = int((perf["performance_score"] < 60).sum())
    n_sla  = (int((perf["sla_breaches"] > 5).sum()) if "sla_breaches" in perf.columns
              else int((subset["sla_breaches"] > 5).sum()))
    b1, b2 = st.columns(2, gap="small")
    b1.warning(f"🦋 **{n_poor}** items with score <60 — Negotiation Leverage Rule active → discount/credit demand flagged")
    b2.warning(f"🦋 **{n_sla}** items with >5 SLA breaches — Escalation Rule active → vendor review meeting scheduled")

    # ── Recommendations ──
    st.divider()
    section_header("Renewal Recommendations — Combined Signal")
    rec = df.copy()
    rec["Renewal_Action"] = rec.apply(renewal_action, axis=1)
    cols     = ["Contract_ID", "Vendor", "License_Type", "Days_to_Renewal",
                "Avg_Utilization_Pct", "performance_score", "Budget_Status", "Renewal_Action"]
    rec_view = rec[cols].sort_values("Days_to_Renewal")
    st.dataframe(rec_view, use_container_width=True, height=340)
    st.download_button(
        "⬇  Download Renewal Recommendations",
        data=rec_view.to_csv(index=False).encode("utf-8"),
        file_name="renewal_recommendations.csv",
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════
# PAGE: BUDGET ANALYSIS
# ═══════════════════════════════════════════════════════════
def render_budget_dashboard(df: pd.DataFrame, view_level: str, max_items: int) -> None:
    page_title("💰", "Budget Analysis", "Expenditure tracking, forecast, and budget status")

    c1, c2, c3 = st.columns(3, gap="small")
    c1.metric("Total Budget",       f"${df['Total_Annual_Budget_USD'].sum():,.0f}")
    c2.metric("Total Actual Spend", f"${df['Total_Actual_Spend_USD'].sum():,.0f}")
    c3.metric("Exceeded Contracts", int((df["Budget_Status"] == "Exceeded").sum()))

    subset           = get_chart_subset(df, max_items)
    license_options  = sorted(subset["License_Type"].dropna().unique().tolist())
    selected_license = st.selectbox("License Type for Contract Drilldown",
                                    options=license_options, key="budget_license_drilldown")
    license_contracts = subset[subset["License_Type"] == selected_license].copy()

    st.divider()
    section_header("Budget vs Actual by License Type")
    left, right = st.columns(2, gap="medium")

    with left:
        spend = subset.groupby("License_Type", as_index=False)[
            ["Total_Annual_Budget_USD", "Total_Actual_Spend_USD"]
        ].sum()
        figL = go.Figure()
        figL.add_bar(x=spend["License_Type"], y=spend["Total_Annual_Budget_USD"],
                     name="Budget", marker_color=COLOR_GREEN,
                     hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra>Budget</extra>")
        figL.add_bar(x=spend["License_Type"], y=spend["Total_Actual_Spend_USD"],
                     name="Actual", marker_color=COLOR_RED,
                     hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra>Actual</extra>")
        figL.update_layout(title_text="Budget vs Actual (License Level)",
                           barmode="group", height=H_HALF, xaxis_tickangle=-35)
        figL.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_fig(figL), use_container_width=True)

    with right:
        cs = (license_contracts[["Contract_ID", "Total_Annual_Budget_USD", "Total_Actual_Spend_USD"]]
              .sort_values("Total_Actual_Spend_USD", ascending=False))
        figR = go.Figure()
        figR.add_bar(x=cs["Contract_ID"], y=cs["Total_Annual_Budget_USD"],
                     name="Budget", marker_color=COLOR_GREEN)
        figR.add_bar(x=cs["Contract_ID"], y=cs["Total_Actual_Spend_USD"],
                     name="Actual", marker_color=COLOR_RED)
        figR.update_layout(title_text=f"Contract Budget vs Actual ({selected_license})",
                           barmode="group", height=H_HALF, xaxis_tickangle=-35)
        figR.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_fig(figR), use_container_width=True)

    st.divider()
    section_header("Actual vs Forecast", "Next 4 Months")
    m_df          = df[df["License_Type"] == selected_license].copy()
    m_df["Month"] = m_df["End_Date"].dt.to_period("M").dt.to_timestamp()
    m_act         = (m_df.dropna(subset=["Month"])
                         .groupby("Month")["Total_Actual_Spend_USD"].sum()
                         .sort_index())
    if len(m_act) > 18:
        m_act = m_act.tail(18)
    fcast = forecast_next_4_months(m_act)

    figF = go.Figure()
    figF.add_trace(go.Scatter(x=m_act.index, y=m_act.values,
                              mode="lines+markers", name="Actual Spend",
                              line=dict(color=COLOR_BLUE, width=2.5), marker=dict(size=6)))
    figF.add_trace(go.Scatter(x=fcast.index, y=fcast.values,
                              mode="lines+markers", name="Forecast Spend",
                              line=dict(color=COLOR_AMBER, dash="dash", width=2),
                              marker=dict(size=6, symbol="diamond")))
    figF.update_layout(height=H_SMALL,
                       title_text=f"Historical + 4-Month Forecast ({selected_license})")
    figF.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(style_fig(figF), use_container_width=True)

    st.divider()
    section_header("Monthly Spend Forecast", "24 Months")
    selected_years = st.multiselect("Forecast Years", [2024, 2025], default=[2024, 2025],
                                    key="budget_years")
    months = pd.date_range("2024-01-01", periods=24, freq="MS")
    trends = []
    for _, row in subset.iterrows():
        base_m = row["Total_Actual_Spend_USD"] / 12
        for dt in months:
            if dt.year not in selected_years:
                continue
            trends.append({
                "Month": dt.strftime("%Y-%m"),
                "Group": row["Vendor"] if view_level == "Vendor" else row["Contract_ID"],
                "Spend": base_m * np.random.uniform(0.95, 1.10),
            })
    if not trends:
        st.info("No forecast data for selected years.")
        return
    tdf  = pd.DataFrame(trends).groupby(["Month", "Group"], as_index=False)["Spend"].sum()
    figT = go.Figure()
    for grp in tdf["Group"].unique()[: min(max_items, 12)]:
        gd = tdf[tdf["Group"] == grp]
        figT.add_trace(go.Scatter(x=gd["Month"], y=gd["Spend"], mode="lines", name=str(grp)))
    figT.update_layout(title_text="24-Month Spend Forecast by Vendor/Contract", height=H_SMALL)
    figT.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(style_fig(figT), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE: LICENSE ANALYSIS
# ═══════════════════════════════════════════════════════════
def render_pillar1_deep_dive_dashboard(df: pd.DataFrame, max_items: int) -> None:
    page_title("🧩", "License analysis", "License utilization deep-dive and true-up exposure")

    subset       = get_chart_subset(df, max_items)
    total_users  = subset["Total_Users"].sum()
    active_users = subset["Active_Users"].sum()
    avg_util     = subset["Avg_Utilization_Pct"].mean() if len(subset) else 0
    low_util     = int((subset["Avg_Utilization_Pct"] < 70).sum())
    high_util    = int((subset["Avg_Utilization_Pct"] > 90).sum())

    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("Total Licensed Users", f"{int(total_users):,}")
    c2.metric("Total Active Users",   f"{int(active_users):,}")
    c3.metric("Avg Utilization",      f"{avg_util:.1f}%")
    c4.metric("Low Util Contracts",   low_util)

    license_options  = sorted(subset["License_Type"].dropna().unique().tolist())
    selected_license = st.selectbox("License Type for Contract Drilldown",
                                    options=license_options, key="pillar1_license_drilldown")
    license_contracts = subset[subset["License_Type"] == selected_license].copy()

    st.divider()
    section_header("Utilization by License Type")
    left, right = st.columns(2, gap="medium")

    with left:
        ubl = (subset.groupby("License_Type", as_index=False)
                     .agg(Avg_Utilization_Pct=("Avg_Utilization_Pct", "mean"),
                          Active_Users=("Active_Users", "sum"),
                          Total_Users=("Total_Users", "sum"),
                          Total_True_Up_USD=("Total_True_Up_USD", "sum"))
                     .sort_values("Avg_Utilization_Pct"))
        ubl["color"] = np.where(
            ubl["Avg_Utilization_Pct"] < 70, COLOR_RED,
            np.where(ubl["Avg_Utilization_Pct"] <= 85, COLOR_AMBER, COLOR_GREEN),
        )
        figL = go.Figure(go.Bar(
            x=ubl["Avg_Utilization_Pct"], y=ubl["License_Type"],
            orientation="h", marker_color=ubl["color"],
            hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
        ))
        figL.add_vline(x=70, line_dash="dot", line_color=COLOR_RED)
        figL.add_vline(x=85, line_dash="dot", line_color=COLOR_GREEN)
        figL.update_layout(height=H_HALF, title_text="License-Type Utilization")
        figL.update_xaxes(range=[0, 110], ticksuffix="%")
        st.plotly_chart(style_fig(figL), use_container_width=True)
        render_butterfly_rule_legend()

    with right:
        cu = license_contracts.sort_values("Avg_Utilization_Pct")
        cc = np.where(
            cu["Avg_Utilization_Pct"] < 70, COLOR_RED,
            np.where(cu["Avg_Utilization_Pct"] <= 85, COLOR_AMBER, COLOR_GREEN),
        )
        figR = go.Figure(go.Bar(
            x=cu["Avg_Utilization_Pct"], y=cu["Contract_ID"],
            orientation="h", marker_color=cc,
            hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
        ))
        figR.add_vline(x=70, line_dash="dot", line_color=COLOR_RED)
        figR.add_vline(x=85, line_dash="dot", line_color=COLOR_GREEN)
        figR.update_layout(height=H_HALF, title_text=f"Contract Utilization ({selected_license})")
        figR.update_xaxes(range=[0, 110], ticksuffix="%")
        st.plotly_chart(style_fig(figR), use_container_width=True)

    st.divider()
    section_header("True-Up Exposure vs Utilization")
    exp = (license_contracts[["Contract_ID", "Avg_Utilization_Pct", "Total_True_Up_USD"]]
           .sort_values("Total_True_Up_USD", ascending=False)
           .head(max_items))
    figE = go.Figure()
    figE.add_bar(x=exp["Contract_ID"], y=exp["Total_True_Up_USD"], name="True-Up USD",
                 marker_color=np.where(exp["Total_True_Up_USD"] > 0, COLOR_RED, COLOR_GREEN),
                 hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra>True-Up</extra>")
    figE.add_trace(go.Scatter(
        x=exp["Contract_ID"], y=exp["Avg_Utilization_Pct"],
        name="Utilization %", mode="lines+markers", yaxis="y2",
        line=dict(color=COLOR_BLUE, width=2), marker=dict(size=6),
        hovertemplate="%{x}: <b>%{y:.1f}%</b><extra>Utilization</extra>",
    ))
    figE.update_layout(
        height=H_SMALL, title_text=f"True-Up and Utilization ({selected_license})",
        yaxis =dict(title="True-Up USD", tickprefix="$", tickformat=",.0f"),
        yaxis2=dict(title="Utilization %", overlaying="y", side="right",
                    range=[0, 110], ticksuffix="%"),
        xaxis_tickangle=-35,
    )
    st.plotly_chart(style_fig(figE), use_container_width=True)

    e1, e2 = st.columns(2, gap="small")
    e1.warning(f"🦋 **{low_util}** contracts below 70% — Low Utilization Rule active → optimization review task created")
    e2.info(   f"🦋 **{high_util}** contracts above 90% — High Utilization Rule active → capacity planning task created")


# ═══════════════════════════════════════════════════════════
# PAGE: VENDOR PERFORMANCE
# ═══════════════════════════════════════════════════════════
def render_vendor_performance_dashboard(df: pd.DataFrame, max_items: int) -> None:
    page_title("📈", "Vendor Performance", "Reliability scores, SLA compliance, and breach drill-down")

    license_options = sorted(df["License_Type"].dropna().unique().tolist())
    if not license_options:
        st.info("No license data available.")
        return

    selected_license = st.selectbox("Select License Type to Audit", license_options,
                                    key="perf_license_drilldown")
    license_df = df[df["License_Type"] == selected_license].copy()
    subset     = get_chart_subset(license_df, max_items)

    c1, c2, c3 = st.columns(3, gap="small")
    c1.metric("Contracts",             len(license_df))
    c2.metric("Total SLA Breaches",    int(license_df["sla_breaches"].sum()))
    c3.metric("Avg Performance Score", f"{license_df['performance_score'].mean():.1f}")

    st.divider()
    section_header("Performance Overview")
    left, right = st.columns(2, gap="medium")

    with left:
        pbl = (df.groupby("License_Type", as_index=False)
                 .agg(performance_score=("performance_score", "mean"),
                      sla_breaches=("sla_breaches", "sum"))
                 .sort_values("performance_score"))
        figL = go.Figure(go.Bar(
            x=pbl["License_Type"], y=pbl["performance_score"],
            marker_color=np.where(pbl["performance_score"] < 60, COLOR_RED, COLOR_BLUE),
            hovertemplate="%{x}: <b>%{y:.0f}</b><extra></extra>",
        ))
        figL.add_hline(y=60, line_dash="dot", line_color=COLOR_RED,
                       annotation_text="60 threshold", annotation_font_size=10)
        figL.update_layout(title_text="Performance Score by License Type",
                           height=H_HALF, xaxis_tickangle=-35)
        st.plotly_chart(style_fig(figL), use_container_width=True)

    with right:
        ps   = subset.sort_values("performance_score")
        figR = go.Figure()
        figR.add_bar(x=ps["Contract_ID"], y=ps["sla_breaches"],
                     name="SLA Breaches", marker_color=COLOR_RED,
                     hovertemplate="%{x}: <b>%{y}</b> breaches<extra></extra>")
        figR.add_bar(x=ps["Contract_ID"], y=ps["performance_score"],
                     name="Performance Score", marker_color=COLOR_BLUE,
                     hovertemplate="%{x}: <b>%{y:.0f}</b> score<extra></extra>")
        figR.update_layout(title_text=f"SLA Breach + Performance ({selected_license})",
                           barmode="group", height=H_HALF, xaxis_tickangle=-35)
        st.plotly_chart(style_fig(figR), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def main() -> None:
    inject_global_style()
    base             = load_base_data()
    perf_df, hist_df = generate_sample_data(base)
    master_df        = (base
                        .merge(perf_df, on="Contract_ID", how="left")
                        .merge(hist_df, on="Contract_ID", how="left"))

    collapsed = st.session_state.get("v5_nav_collapsed", False)
    # gap="small" (~0.5 rem) prevents the gap eating into the narrow nav column.
    # Collapsed: icon-only strip (~55px); Expanded: ~18% of page width.
    nav_ratio            = [0.55, 5.45] if collapsed else [1.10, 4.90]
    nav_col, content_col = st.columns(nav_ratio, gap="small")

    with nav_col:
        filtered_df, page, view_level, max_items = build_left_panel(master_df)

    if filtered_df.empty:
        with content_col:
            st.info("No contracts match the selected filters.")
        return

    with content_col:
        # st.markdown (not st.caption) — st.caption ignores unsafe_allow_html
        st.markdown(
            f"<div class='view-caption'>{view_level} view &nbsp;·&nbsp; "
            f"charts limited to {max_items} items</div>",
            unsafe_allow_html=True,
        )
        if   page == "📋 Actions Dashboard":
            render_actions_dashboard(filtered_df, view_level, max_items)
        elif page == "🧩 License analysis":
            render_pillar1_deep_dive_dashboard(filtered_df, max_items)
        elif page == "💰 Budget Analysis":
            render_budget_dashboard(filtered_df, view_level, max_items)
        elif page == "📈 Vendor Performance":
            render_vendor_performance_dashboard(filtered_df, max_items)


if __name__ == "__main__":
    main()