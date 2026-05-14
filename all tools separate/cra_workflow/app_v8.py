import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATA_DIR = os.getenv("DATA_DIR", "data")

from appp import (
    COLOR_AMBER,
    COLOR_BLUE,
    COLOR_GRAY,
    COLOR_GREEN,
    COLOR_RED,
    H_HALF,
    H_MAIN,
    H_SMALL,
    generate_sample_data,
    forecast_next_4_months,
    get_chart_subset,
    inject_global_style,
    load_base_data,
    page_title,
    render_budget_dashboard,
    render_butterfly_rule_legend,
    render_pillar1_deep_dive_dashboard,
    renewal_action,
    section_header,
    style_fig,
)
def compact_license_selector(options: list[str], key: str, label: str = "License Type") -> str:
    left_spacer, right_picker = st.columns([4.2, 1.2], gap="small")
    with right_picker:
        return st.selectbox(label, options=options, key=key)


def render_budget_dashboard(kpi_df: pd.DataFrame, chart_df: pd.DataFrame, view_level: str, max_items: int) -> None:
    page_title("💰", "Budget Analysis", "Expenditure tracking, forecast, and budget status")

    c1, c2, c3 = st.columns(3, gap="small")
    c1.metric("Total Budget", f"${kpi_df['Total_Annual_Budget_USD'].sum():,.0f}")
    c2.metric("Total Actual Spend", f"${kpi_df['Total_Actual_Spend_USD'].sum():,.0f}")
    c3.metric("Exceeded Contracts", int((kpi_df["Budget_Status"] == "Exceeded").sum()))

    subset = get_chart_subset(chart_df, max_items)
    license_options = sorted(subset["License_Type"].dropna().unique().tolist())
    selected_license = compact_license_selector(
        license_options,
        key="budget_license_drilldown",
        label="License Type for Contract Drilldown",
    )
    license_contracts = subset[subset["License_Type"] == selected_license].copy()

    st.divider()
    section_header("Budget compared with actual spend by license type")
    left, right = st.columns(2, gap="medium")

    with left:
        spend = subset.groupby("License_Type", as_index=False)[
            ["Total_Annual_Budget_USD", "Total_Actual_Spend_USD"]
        ].sum()
        figL = go.Figure()
        figL.add_bar(
            x=spend["License_Type"],
            y=spend["Total_Annual_Budget_USD"],
            name="Budget",
            marker_color=COLOR_GREEN,
            hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra>Budget</extra>",
        )
        figL.add_bar(
            x=spend["License_Type"],
            y=spend["Total_Actual_Spend_USD"],
            name="Actual",
            marker_color=COLOR_RED,
            hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra>Actual</extra>",
        )
        figL.update_layout(title_text="Budget compared with actual spend at license level", barmode="group", height=H_HALF, xaxis_tickangle=-35)
        figL.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_fig(figL), use_container_width=True)

    with right:
        cs = license_contracts[["Contract_ID", "Total_Annual_Budget_USD", "Total_Actual_Spend_USD"]].sort_values(
            "Total_Actual_Spend_USD", ascending=False
        )
        figR = go.Figure()
        figR.add_bar(x=cs["Contract_ID"], y=cs["Total_Annual_Budget_USD"], name="Budget", marker_color=COLOR_GREEN)
        figR.add_bar(x=cs["Contract_ID"], y=cs["Total_Actual_Spend_USD"], name="Actual", marker_color=COLOR_RED)
        figR.update_layout(title_text=f"Contract budget compared with actual spend ({selected_license})", barmode="group", height=H_HALF, xaxis_tickangle=-35)
        figR.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_fig(figR), use_container_width=True)

    st.divider()
    section_header("Actual spend compared with forecast", "Next 4 Months")
    m_df = chart_df[chart_df["License_Type"] == selected_license].copy()
    m_df["Month"] = m_df["End_Date"].dt.to_period("M").dt.to_timestamp()
    m_act = m_df.dropna(subset=["Month"]).groupby("Month")["Total_Actual_Spend_USD"].sum().sort_index()
    if len(m_act) > 18:
        m_act = m_act.tail(18)
    fcast = forecast_next_4_months(m_act)

    figF = go.Figure()
    figF.add_trace(
        go.Scatter(
            x=m_act.index,
            y=m_act.values,
            mode="lines+markers",
            name="Actual Spend",
            line=dict(color=COLOR_BLUE, width=2.5),
            marker=dict(size=6),
        )
    )
    figF.add_trace(
        go.Scatter(
            x=fcast.index,
            y=fcast.values,
            mode="lines+markers",
            name="Forecast Spend",
            line=dict(color=COLOR_AMBER, dash="dash", width=2),
            marker=dict(size=6, symbol="diamond"),
        )
    )
    figF.update_layout(height=H_SMALL, title_text=f"Historical and 4-month forecast ({selected_license})")
    figF.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(style_fig(figF), use_container_width=True)


def render_pillar1_deep_dive_dashboard(kpi_df: pd.DataFrame, chart_df: pd.DataFrame, max_items: int) -> None:
    page_title("🧩", "License analysis", "License utilization deep-dive and true-up exposure")
    subset = get_chart_subset(chart_df, max_items)
    total_users = kpi_df["Total_Users"].sum()
    active_users = kpi_df["Active_Users"].sum()
    avg_util = kpi_df["Avg_Utilization_Pct"].mean() if len(kpi_df) else 0
    low_util = int((kpi_df["Avg_Utilization_Pct"] < 30).sum())
    high_util = int((kpi_df["Avg_Utilization_Pct"] > 90).sum())

    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("Total Licensed Users", f"{int(total_users):,}")
    c2.metric("Total Active Users", f"{int(active_users):,}")
    c3.metric("Average Utilization", f"{avg_util:.1f}%")
    c4.metric("Low Utilization Contracts", low_util)

    license_options = sorted(subset["License_Type"].dropna().unique().tolist())
    selected_license = compact_license_selector(
        license_options,
        key="pillar1_license_drilldown",
        label="License Type for Contract Drilldown",
    )
    license_contracts = subset[subset["License_Type"] == selected_license].copy()

    st.divider()
    section_header("Utilization by license type")
    left, right = st.columns(2, gap="medium")
    with left:
        ubl = (
            subset.groupby("License_Type", as_index=False)
            .agg(
                Avg_Utilization_Pct=("Avg_Utilization_Pct", "mean"),
                Active_Users=("Active_Users", "sum"),
                Total_Users=("Total_Users", "sum"),
                Total_True_Up_USD=("Total_True_Up_USD", "sum"),
            )
            .sort_values("Avg_Utilization_Pct")
        )
        ubl["color"] = np.where((ubl["Avg_Utilization_Pct"] < 70) | (ubl["Avg_Utilization_Pct"] > 90), COLOR_RED, COLOR_GREEN)
        figL = go.Figure(
            go.Bar(
                x=ubl["Avg_Utilization_Pct"],
                y=ubl["License_Type"],
                orientation="h",
                marker_color=ubl["color"],
                hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
            )
        )
        figL.add_vline(x=70, line_dash="dot", line_color=COLOR_RED)
        figL.add_vline(x=90, line_dash="dot", line_color=COLOR_RED)
        figL.update_layout(height=H_HALF, title_text="License-type utilization")
        figL.update_xaxes(range=[0, 110], ticksuffix="%")
        st.plotly_chart(style_fig(figL), use_container_width=True)

    with right:
        cu = license_contracts.sort_values("Avg_Utilization_Pct")
        cc = np.where((cu["Avg_Utilization_Pct"] < 70) | (cu["Avg_Utilization_Pct"] > 90), COLOR_RED, COLOR_GREEN)
        figR = go.Figure(
            go.Bar(
                x=cu["Avg_Utilization_Pct"],
                y=cu["Contract_ID"],
                orientation="h",
                marker_color=cc,
                hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
            )
        )
        figR.add_vline(x=70, line_dash="dot", line_color=COLOR_RED)
        figR.add_vline(x=90, line_dash="dot", line_color=COLOR_RED)
        figR.update_layout(height=H_HALF, title_text=f"Contract utilization ({selected_license})")
        figR.update_xaxes(range=[0, 110], ticksuffix="%")
        st.plotly_chart(style_fig(figR), use_container_width=True)

    st.divider()
    section_header("True-up exposure compared with utilization")
    exp = license_contracts[["Contract_ID", "Avg_Utilization_Pct", "Total_True_Up_USD"]].sort_values("Total_True_Up_USD", ascending=False).head(max_items)
    figE = go.Figure()
    figE.add_bar(
        x=exp["Contract_ID"],
        y=exp["Total_True_Up_USD"],
        name="True-Up USD",
        marker_color=np.where(exp["Total_True_Up_USD"] > 0, COLOR_RED, COLOR_GREEN),
        hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra>True-Up</extra>",
    )
    figE.add_trace(
        go.Scatter(
            x=exp["Contract_ID"],
            y=exp["Avg_Utilization_Pct"],
            name="Utilization Percentage",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=COLOR_BLUE, width=2),
            marker=dict(size=6),
            hovertemplate="%{x}: <b>%{y:.1f}%</b><extra>Utilization</extra>",
        )
    )
    figE.update_layout(
        height=H_SMALL,
        title_text=f"True-up and utilization ({selected_license})",
        yaxis=dict(title="True-Up USD", tickprefix="$", tickformat=",.0f"),
        yaxis2=dict(title="Utilization Percentage", overlaying="y", side="right", range=[0, 110], ticksuffix="%"),
        xaxis_tickangle=-35,
    )
    st.plotly_chart(style_fig(figE), use_container_width=True)
    e1, e2 = st.columns(2, gap="small")
    e1.warning(f"🦋 **{low_util}** contracts below 30% utilization — optimization review task created")
    e2.error(f"🦋 **{high_util}** contracts above 90% utilization — capacity planning task created")


def initialize_default_filters(master_df: pd.DataFrame) -> None:
    owner_opts = sorted(master_df["Owner"].dropna().unique().tolist())
    vendor_opts = sorted(master_df["Vendor"].dropna().unique().tolist())
    crit_opts = sorted(master_df["Criticality"].dropna().unique().tolist())
    lic_opts = sorted(master_df["License_Type"].dropna().unique().tolist())
    con_opts = sorted(master_df["Contract_ID"].dropna().unique().tolist())

    requested_defaults = {
        "v5_owner_sel": ["Finance", "IT", "Procurement"],
        "v5_vendor_sel": ["Vendor 1", "Vendor 2"],
        "v5_crit_sel": ["Critical", "High", "Low", "Medium"],
        "v5_lic_sel": ["License 1", "License 2", "License 3", "License 4", "License 5", "License 6"],
        "v5_con_sel": ["C-1001", "C-1002", "C-1003", "C-1005", "C-1006", "C-1064"],
    }
    available_options = {
        "v5_owner_sel": owner_opts,
        "v5_vendor_sel": vendor_opts,
        "v5_crit_sel": crit_opts,
        "v5_lic_sel": lic_opts,
        "v5_con_sel": con_opts,
    }

    for key, values in requested_defaults.items():
        if key not in st.session_state:
            allowed = [v for v in values if v in available_options[key]]
            st.session_state[key] = allowed if allowed else available_options[key]

    if "v5_view_level" not in st.session_state:
        st.session_state["v5_view_level"] = "Contract"


def build_left_panel(master_df: pd.DataFrame) -> tuple[pd.DataFrame, str, str, int]:
    collapsed = st.session_state.get("v5_nav_collapsed", False)

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

    if collapsed:
        if st.button("▶", key="v5_nav_toggle_open", use_container_width=True):
            st.session_state["v5_nav_collapsed"] = False
            st.rerun()
    else:
        if st.button("◀  Dashboard", key="v5_nav_toggle_close", use_container_width=True):
            st.session_state["v5_nav_collapsed"] = True
            st.rerun()

    if not collapsed:
        st.markdown("<div class='nav-label'>Navigation</div>", unsafe_allow_html=True)

    page_options = [
        ("📋 Actions Dashboard", "📋"),
        ("🧩 License analysis", "🧩"),
        ("💰 Budget Analysis", "💰"),
    ]
    if "v5_page" not in st.session_state:
        st.session_state["v5_page"] = page_options[0][0]
    for page_name, short_name in page_options:
        label = short_name if collapsed else page_name
        if st.button(label, use_container_width=True, key=f"v5_nav_{page_name}"):
            st.session_state["v5_page"] = page_name
            st.rerun()
    page = st.session_state["v5_page"]

    owner_opts = sorted(master_df["Owner"].dropna().unique().tolist())
    vendor_opts = sorted(master_df["Vendor"].dropna().unique().tolist())
    crit_opts = sorted(master_df["Criticality"].dropna().unique().tolist())
    lic_opts = sorted(master_df["License_Type"].dropna().unique().tolist())

    owner_key = "v5_owner_sel"
    vendor_key = "v5_vendor_sel"
    crit_key = "v5_crit_sel"
    lic_key = "v5_lic_sel"
    con_key = "v5_con_sel"
    view_key = "v5_view_level"
    max_key = "v5_max_items"
    lic_radio_key = "v8_license_radio"

    if owner_key not in st.session_state:
        st.session_state[owner_key] = owner_opts
    if vendor_key not in st.session_state:
        st.session_state[vendor_key] = vendor_opts
    if crit_key not in st.session_state:
        st.session_state[crit_key] = crit_opts
    if lic_key not in st.session_state:
        st.session_state[lic_key] = lic_opts
    if view_key not in st.session_state:
        st.session_state[view_key] = "Contract"
    if max_key not in st.session_state:
        st.session_state[max_key] = 20

    if not collapsed:
        st.markdown("<div class='nav-label nav-label-border'>Filters</div>", unsafe_allow_html=True)
        owner_sel = st.multiselect("Owner", owner_opts, key=owner_key)
        vendor_sel = st.multiselect("Vendor", vendor_opts, key=vendor_key)
        crit_sel = st.multiselect("Criticality", crit_opts, key=crit_key)

        available_licenses = sorted(
            master_df[
                master_df["Owner"].isin(owner_sel)
                & master_df["Vendor"].isin(vendor_sel)
                & master_df["Criticality"].isin(crit_sel)
            ]["License_Type"]
            .dropna()
            .unique()
            .tolist()
        )
        license_radio_options = ["All License Types"] + available_licenses
        
        if st.session_state.get(lic_radio_key, "All License Types") not in license_radio_options:
            st.session_state[lic_radio_key] = "All License Types"
            
        selected_license = st.radio(
            "License Type",
            options=license_radio_options,
            key=lic_radio_key,
        )
        lic_sel = available_licenses if selected_license == "All License Types" else [selected_license]
        st.session_state[lic_key] = lic_sel

        cf = master_df[
            master_df["Owner"].isin(owner_sel)
            & master_df["Vendor"].isin(vendor_sel)
            & master_df["Criticality"].isin(crit_sel)
            & (master_df["License_Type"].isin(lic_sel) if lic_sel else True)
        ]
        con_opts = sorted(cf["Contract_ID"].dropna().unique().tolist())
        
        if con_key in st.session_state:
            st.session_state[con_key] = [v for v in st.session_state[con_key] if v in con_opts]
            
        con_sel = st.multiselect(
            "Contract Identifier",
            con_opts,
            key=con_key,
        )
        view_level = st.radio("View Level", ["Contract", "Vendor"], horizontal=True, key=view_key)
        
        if max_key not in st.session_state:
            st.session_state[max_key] = 20
        max_chart_items = int(st.slider("Chart items", 5, 50, step=5, key=max_key))
    else:
        owner_sel = st.session_state.get(owner_key, owner_opts)
        vendor_sel = st.session_state.get(vendor_key, vendor_opts)
        crit_sel = st.session_state.get(crit_key, crit_opts)
        lic_sel = st.session_state.get(lic_key, lic_opts)
        con_sel = st.session_state.get(con_key, [])
        view_level = st.session_state.get(view_key, "Contract")
        max_chart_items = int(st.session_state.get(max_key, 20))

    kpi_filtered = master_df[
        master_df["Owner"].isin(owner_sel)
        & master_df["Vendor"].isin(vendor_sel)
        & master_df["Criticality"].isin(crit_sel)
        & (master_df["License_Type"].isin(lic_sel) if lic_sel else True)
    ].copy()

    chart_filtered = kpi_filtered[
        (kpi_filtered["Contract_ID"].isin(con_sel) if con_sel else True)
    ].copy()

    return kpi_filtered, chart_filtered, page, view_level, max_chart_items


def render_actions_dashboard(kpi_df: pd.DataFrame, chart_df: pd.DataFrame, view_level: str, max_items: int) -> None:
    page_title("📋", "Actions Dashboard", "Unified contract risk signals and renewal recommendations")

    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("Total Contracts", len(kpi_df))
    c2.metric("Contracts at Risk", int(kpi_df["Renewal_Flag"].isin(["Warning", "Critical"]).sum()))
    c3.metric("Cap-Exceeded", int((kpi_df["Budget_Status"] == "Exceeded").sum()))
    c4.metric("Average Portfolio Utilization", f"{kpi_df['Avg_Utilization_Pct'].mean():.1f}%")

    subset = get_chart_subset(chart_df, max_items)

    # ── Pillar 1 ──
    st.divider()
    section_header("License Utilization ")
    usage = (
        subset.groupby("Vendor", as_index=False)["Avg_Utilization_Pct"].mean().sort_values("Avg_Utilization_Pct")
        if view_level == "Vendor"
        else subset.sort_values("Avg_Utilization_Pct")[["Contract_ID", "Avg_Utilization_Pct"]].rename(
            columns={"Contract_ID": "Vendor"}
        )
    )
    usage["color"] = np.where(
        usage["Avg_Utilization_Pct"] < 35,
        COLOR_AMBER,
        np.where(usage["Avg_Utilization_Pct"] > 90, COLOR_RED, COLOR_GREEN)
    )
    fig1 = go.Figure(
        go.Bar(
            x=usage["Avg_Utilization_Pct"],
            y=usage["Vendor"],
            orientation="h",
            marker_color=usage["color"],
            hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
        )
    )
    fig1.add_vline(
        x=70,
        line_dash="dot",
        line_color=COLOR_RED,
        annotation_text="70% floor",
        annotation_font_size=10,
        annotation_font_color=COLOR_RED,
    )
    fig1.add_vline(
        x=85,
        line_dash="dot",
        line_color=COLOR_GREEN,
        annotation_text="85% target",
        annotation_font_size=10,
        annotation_font_color=COLOR_GREEN,
    )
    fig1.update_layout(title_text="License Utilization by Vendor or Contract", height=H_MAIN)
    fig1.update_xaxes(range=[0, 110], ticksuffix="%")
    st.plotly_chart(style_fig(fig1), use_container_width=True)
    st.markdown(
        "<div class='legend-row'>"
        f"<span><span class='legend-dot' style='background:{COLOR_AMBER}'></span>Under-utilized (&lt;35%)</span>"
        f"<span><span class='legend-dot' style='background:{COLOR_RED}'></span>Over-utilized (&gt;90%)</span>"
        f"<span><span class='legend-dot' style='background:{COLOR_GREEN}'></span>Balanced (35%-90%)</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    n_low = int((usage["Avg_Utilization_Pct"] < 70).sum())
    n_high = int((usage["Avg_Utilization_Pct"] > 90).sum())
    a1, a2 = st.columns(2, gap="small")
    a1.warning(f"🦋 **{n_low}** items below 30% utilization — optimization review task created")
    a2.error(f"🦋 **{n_high}** items above 90% utilization — capacity risk task created")

    st.divider()
    left_chart, right_chart = st.columns(2, gap="medium")

    # ── Budget Monitoring (replacing Vendor Performance on first page) ──
    with left_chart:
        section_header("Budget compared with actual spend")
        budget = subset.copy()
        if view_level == "Vendor":
            budget = (
                budget.groupby("Vendor", as_index=False)
                .agg(
                    total_budget=("Total_Annual_Budget_USD", "sum"),
                    total_actual_spend=("Total_Actual_Spend_USD", "sum"),
                )
                .sort_values("total_budget", ascending=False)
            )
            budget_x = budget["Vendor"]
        else:
            budget = budget.sort_values("Total_Annual_Budget_USD", ascending=False)
            budget_x = budget["Contract_ID"]
        fig2 = go.Figure()
        fig2.add_bar(
            x=budget_x,
            y=budget["total_budget"] if view_level == "Vendor" else budget["Total_Annual_Budget_USD"],
            name="Total Annual Budget",
            marker_color=COLOR_GREEN,
        )
        fig2.add_bar(
            x=budget_x,
            y=budget["total_actual_spend"] if view_level == "Vendor" else budget["Total_Actual_Spend_USD"],
            name="Total Actual Spend",
            marker_color=COLOR_RED,
        )
        fig2.update_layout(
            title_text="Budget and actual spend by selected view",
            barmode="group",
            height=H_MAIN,
            xaxis_tickangle=-35,
        )
        fig2.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_fig(fig2), use_container_width=True)

    # ── Renewal timeline monitor (new) ──
    with right_chart:
        section_header("License Renewal Timeline Monitoring", "Butterfly Triggers · 180/60")
        renewal_timeline = subset.copy()
        renewal_timeline["Renewal_Window"] = np.where(
            renewal_timeline["Days_to_Renewal"] <= 60,
            "0-60 Days (Escalate)",
            np.where(
                renewal_timeline["Days_to_Renewal"] <= 180,
                "61-180 Days (Alert)",
                ">180 Days (Watch)",
            ),
        )
        timeline_counts = (
            renewal_timeline.groupby("Renewal_Window", as_index=False)
            .size()
            .rename(columns={"size": "Contracts"})
        )
        order = ["0-60 Days (Escalate)", "61-180 Days (Alert)", ">180 Days (Watch)"]
        timeline_counts["Renewal_Window"] = pd.Categorical(
            timeline_counts["Renewal_Window"], categories=order, ordered=True
        )
        timeline_counts = timeline_counts.sort_values("Renewal_Window")

        timeline_colors = {
            "0-60 Days (Escalate)": COLOR_RED,
            "61-180 Days (Alert)": COLOR_AMBER,
            ">180 Days (Watch)": COLOR_GREEN,
        }
        fig4 = go.Figure(
            go.Bar(
                x=timeline_counts["Renewal_Window"],
                y=timeline_counts["Contracts"],
                marker_color=[timeline_colors[w] for w in timeline_counts["Renewal_Window"]],
                text=timeline_counts["Contracts"],
                textposition="outside",
                hovertemplate="%{x}: <b>%{y}</b> contracts<extra></extra>",
            )
        )
        fig4.update_layout(title_text="License Renewal Timeline by Butterfly Trigger Window", height=H_MAIN)
        fig4.update_yaxes(title="Contracts")
        st.plotly_chart(style_fig(fig4), use_container_width=True)

    n_60 = int((subset["Days_to_Renewal"] <= 60).sum())
    n_180 = int(((subset["Days_to_Renewal"] > 60) & (subset["Days_to_Renewal"] <= 180)).sum())
    t1, t2 = st.columns(2, gap="small")
    t1.error(f"🦋 **{n_60}** contracts at <=60 days — Renewal Escalation Trigger active")
    t2.warning(f"🦋 **{n_180}** contracts in 61-180 days — Early Alert Trigger active")

    # ── Recommendations ──
    st.divider()
    section_header("Renewal Stages")
    rec = chart_df.copy()
    rec["Renewal_Action"] = rec.apply(renewal_action, axis=1)

    import json
    import os
    override_file = os.path.join(DATA_DIR, "agent_state.json")
    if os.path.exists(override_file):
        try:
            with open(override_file, "r") as f:
                state_overrides = json.load(f)
            
            def get_stage(cid, original):
                return state_overrides.get(cid, {}).get("Stage", original)
            def get_pending(cid, original_stage):
                override = state_overrides.get(cid, {}).get("Pending_With")
                if override:
                    return override
                # Default mapping if no override found
                default_map = {
                    "Planning": "Procurement Team",
                    "Budgeting": "Procurement Team",
                    "Approval": "Executive Approver",
                    "Execution": "Procurement Team",
                    "Closed": "None"
                }
                return default_map.get(original_stage, "Unassigned")
            
            if "Stages" in rec.columns:
                rec["Current_Stage"] = rec.apply(lambda r: get_stage(r["Contract_ID"], r["Stages"]), axis=1)
                rec["Pending_With"] = rec.apply(lambda r: get_pending(r["Contract_ID"], r["Current_Stage"]), axis=1)
            else:
                rec["Current_Stage"] = rec["Contract_ID"].map(lambda x: state_overrides.get(x, {}).get("Stage", "Planning"))
                rec["Pending_With"] = rec["Contract_ID"].map(lambda x: state_overrides.get(x, {}).get("Pending_With", "Procurement Team"))
        except Exception:
            rec["Current_Stage"] = rec.get("Stages", "Planning")
            rec["Pending_With"] = "Procurement Team"
    else:
        rec["Current_Stage"] = rec.get("Stages", "Planning")
        rec["Pending_With"] = "Procurement Team"

    cols = [
        "Contract_ID",
        "Vendor",
        "License_Type",
        "Days_to_Renewal",
        "Avg_Utilization_Pct",
        "performance_score",
        "Budget_Status",
        "Renewal_Action",
        "Current_Stage",
        "Pending_With"
    ]
    rec_view = rec[cols].sort_values("Days_to_Renewal")
    st.dataframe(rec_view, use_container_width=True, height=340)
    st.download_button(
        "⬇  Download Renewal Recommendations",
        data=rec_view.to_csv(index=False).encode("utf-8"),
        file_name="renewal_recommendations.csv",
        mime="text/csv",
    )


def main() -> None:
    inject_global_style()
    base = load_base_data()
    perf_df, hist_df = generate_sample_data(base)
    master_df = base.merge(perf_df, on="Contract_ID", how="left").merge(hist_df, on="Contract_ID", how="left")
    initialize_default_filters(master_df)

    collapsed = st.session_state.get("v5_nav_collapsed", False)
    nav_ratio = [0.55, 5.45] if collapsed else [1.10, 4.90]
    nav_col, content_col = st.columns(nav_ratio, gap="small")

    with nav_col:
        kpi_df, chart_df, page, view_level, max_items = build_left_panel(master_df)

    if chart_df.empty:
        with content_col:
            st.info("No contracts match the selected filters.")
        return

    with content_col:
        st.markdown(
            f"<div class='view-caption'>{view_level} view &nbsp;·&nbsp; charts limited to {max_items} items</div>",
            unsafe_allow_html=True,
        )
        if page == "📋 Actions Dashboard":
            render_actions_dashboard(kpi_df, chart_df, view_level, max_items)
        elif page == "🧩 License analysis":
            render_pillar1_deep_dive_dashboard(kpi_df, chart_df, max_items)
        elif page == "💰 Budget Analysis":
            render_budget_dashboard(kpi_df, chart_df, view_level, max_items)


if __name__ == "__main__":
    main()
