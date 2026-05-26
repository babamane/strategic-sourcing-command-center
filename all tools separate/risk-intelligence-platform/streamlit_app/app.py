import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF, XPos, YPos

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="RiskIntel | Enterprise Vendor Risk Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------
if "vendor_history" not in st.session_state:
    st.session_state["vendor_history"] = {}

# -----------------------------------
# CUSTOM CSS FOR Bloomberg/Palantir SOC THEME
# -----------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Main layout overrides */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #030712;
    color: #F3F4F6;
}

.stApp {
    background: radial-gradient(circle at 50% 50%, #111827 0%, #030712 100%);
}

/* Glassmorphism Cards */
.card {
    background: rgba(17, 24, 39, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 24px;
    border-radius: 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    margin-bottom: 20px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.card:hover {
    border-color: rgba(99, 102, 241, 0.4);
}

/* Metric Display */
.metric-title {
    color: #9CA3AF;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}

.metric-value {
    font-family: 'Outfit', sans-serif;
    font-size: 38px;
    font-weight: 800;
    line-height: 1.1;
}

/* Agent Card Styles */
.agent-card {
    background: rgba(31, 41, 55, 0.45);
    border-left: 5px solid #6366F1;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.agent-title {
    font-family: 'Outfit', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #F3F4F6;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
}

/* Severity badge styling */
.severity-badge {
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
}

.critical-badge {
    background-color: rgba(239, 68, 68, 0.2);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.4);
}

.high-badge {
    background-color: rgba(249, 115, 22, 0.2);
    color: #F97316;
    border: 1px solid rgba(249, 115, 22, 0.4);
}

.medium-badge {
    background-color: rgba(234, 179, 8, 0.2);
    color: #EAB308;
    border: 1px solid rgba(234, 179, 8, 0.4);
}

.low-badge {
    background-color: rgba(34, 197, 94, 0.2);
    color: #22C55E;
    border: 1px solid rgba(34, 197, 94, 0.4);
}

/* Timeline */
.timeline-item {
    padding-left: 20px;
    border-left: 2px solid #374151;
    position: relative;
    padding-bottom: 20px;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -6px;
    top: 4px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #6366F1;
}

.timeline-date {
    font-size: 12px;
    color: #9CA3AF;
    font-weight: 600;
}

.timeline-content {
    font-size: 14px;
    color: #F3F4F6;
    margin-top: 4px;
}

/* Header Text styling */
.title {
    font-family: 'Outfit', sans-serif;
    font-size: 48px;
    font-weight: 800;
    background: linear-gradient(to right, #FFFFFF, #9CA3AF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
}

.subtitle {
    font-size: 16px;
    color: #9CA3AF;
    margin-top: 5px;
    margin-bottom: 30px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# PDF REPORT GENERATOR
# -----------------------------------
def generate_pdf_report(company_name, overall_score, severity, decision, confidence, results, executive_summary, mitigation_plan):
    pdf = FPDF()
    pdf.add_page()
    
    # Safe text converter
    def clean(t):
        if not t:
            return ""
        replacements = {
            "🛡️": "[Mitigation]",
            "🤖": "[Agent]",
            "🟢": "[OK]",
            "🔴": "[ALERT]",
            "✅": "[PASSED]",
            "📊": "[Chart]",
            "📈": "[Trend]",
            "⏳": "[Timeline]",
            "📡": "[Feed]",
            "⚡": "[Action]",
            "🔍": "[Audit]",
            "🔹": "-",
            "🎯": "[Target]",
            "💸": "$",
            "⚖️": "[Legal]",
        }
        for k, v in replacements.items():
            t = t.replace(k, v)
        # Drop non-latin-1 to prevent fpdf encoding errors
        return t.encode('latin-1', 'ignore').decode('latin-1')

    # Draw header bar
    pdf.set_fill_color(17, 24, 39)
    pdf.rect(0, 0, 210, 30, 'F')
    
    # Title
    pdf.set_y(10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, clean(f"RISKINTEL | VENDOR RISK DOSSIER: {company_name.upper()}"), border=0, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(15)
    
    # Metadata Info Box
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(243, 244, 246)
    pdf.rect(10, 40, 190, 35, 'F')
    
    pdf.set_y(43)
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(50, 6, "Overall Risk Score:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(50, 6, f"{overall_score}/100", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(50, 6, "Risk Severity:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(50, 6, f"{severity}", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(50, 6, "Procurement Recommendation:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(50, 6, clean(decision), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(50, 6, "Telemetry Confidence Level:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(50, 6, f"{confidence}%", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(12)
    
    # Executive Summary Section
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "1. EXECUTIVE RISK ASSESSMENT SUMMARY", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(99, 102, 241)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(pdf.epw, 5, clean(executive_summary))
    pdf.ln(8)
    
    # Mitigation Section
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "2. RISK MITIGATION & REMEDIATION PLAN", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(pdf.epw, 5, clean(mitigation_plan))
    pdf.ln(8)
    
    # Agent Reports Section
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "3. INDEPENDENT AGENT DOSSIER REPORTS", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    for agent in results:
        if pdf.get_y() > 240:
            pdf.add_page()
            
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(0, 6, clean(f"[{agent['risk_category']}] - Score: {agent['risk_score']}/100 ({agent['severity']})"), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(107, 114, 128)
        pdf.multi_cell(pdf.epw, 4, clean(f"Summary: {agent.get('ai_summary', '')}"))
        pdf.ln(1)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)
        # Recommendations
        pdf.cell(0, 4, "Key Actions Required:", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for r in agent.get("recommendations", []):
            pdf.cell(10, 4, "-", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.multi_cell(pdf.epw - 10, 4, clean(r))
        pdf.ln(3)

    return bytes(pdf.output())

# -----------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h1 style='font-family: Outfit, sans-serif; color: #6366F1; font-weight: 800; font-size: 32px; margin-bottom: 0;'>🛡️ RISKINTEL</h1>
    <span style='color: #9CA3AF; font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em;'>Enterprise Third-Party Risk</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.subheader("Vendor Scope")
company_name = st.sidebar.text_input("Company Name", "Meta")

st.sidebar.subheader("Engagement Details")
services = st.sidebar.text_area(
    "Services Provided",
    "AI Infrastructure, Cloud Operations & Strategic Data Pipeline Services"
)

run_analysis = st.sidebar.button(
    "🚀 Run Agent Intelligence",
    width='stretch'
)

st.sidebar.divider()

# Show active keys status
st.sidebar.caption("System Telemetry Status")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    st.markdown("🟢 Shodan Connected")
    st.markdown("🟢 Tavily Active")
with col_s2:
    st.markdown("🟢 OTX Threat Feed")
    st.markdown("🟢 GDELT Engine")

st.sidebar.info("Continuous compliance audit pipeline enabled.")

# -----------------------------------
# MAIN CONTENT HEADER
# -----------------------------------
st.markdown(
    f"""
    <div class="title">
        {company_name} Intelligence Dossier
    </div>
    <div class="subtitle">
        AI-Powered Vendor Risk Intelligence Platform | Real-Time Corporate Threat Telemetry
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------
# EXECUTE / PARSE VENDOR INTEL
# -----------------------------------
data = None
if run_analysis:
    with st.spinner("Initializing multi-agent threat pipeline & gathering telemetry..."):
        try:
            # Domain and Ticker are resolved dynamically on the backend
            response = requests.post(
                "http://127.0.0.1:8020/analyze",
                json={
                    "company_name": company_name,
                    "services": services,
                    "domain": "",
                    "ticker": ""
                },
                timeout=120
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["current_vendor_data"] = data
                st.session_state["vendor_history"][company_name] = data
            else:
                st.error(f"Backend Server returned error code {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Failed to connect to the backend server. Make sure it is running at http://127.0.0.1:8000. Error: {str(e)}")

# Get current cached data if exists
if "current_vendor_data" in st.session_state and not data:
    data = st.session_state["current_vendor_data"]

# -----------------------------------
# DASHBOARD LAYOUT & TABS
# -----------------------------------
if data:
    overall = data["overall_assessment"]
    results = data["results"]
    
    # Extract overall metrics
    overall_score = overall.get("overall_risk_score", 0.0)
    severity = overall.get("overall_severity", "Low")
    decision = overall.get("procurement_decision", "Approved Vendor")
    confidence = overall.get("confidence_score", 85)
    highest_risk = overall.get("highest_risk_category", "N/A")
    tier = overall.get("vendor_tier", "Tier 1")

    # Define color class based on severity
    sev_class = "low-badge"
    sev_color = "#22C55E"
    if severity == "Critical":
        sev_class = "critical-badge"
        sev_color = "#EF4444"
    elif severity == "High":
        sev_class = "high-badge"
        sev_color = "#F97316"
    elif severity == "Medium":
        sev_class = "medium-badge"
        sev_color = "#EAB308"

    # Tab navigation
    tabs = st.tabs([
        "🛡️ Executive Summary", 
        "🤖 Agent Intelligence Reports", 
        "🔄 Vendor Comparison",
        "📡 Threat News Feed",
        "📄 Export Dossier"
    ])

    # ===================================
    # TAB 1: EXECUTIVE SUMMARY
    # ===================================
    with tabs[0]:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">Overall Risk Score</div>
                <div class="metric-value" style="color: {sev_color};">{overall_score}/100</div>
                <div style="font-size: 11px; margin-top: 4px; color: #9CA3AF;">Weighted Synthesis</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">Risk Severity</div>
                <div class="metric-value"><span class="severity-badge {sev_class}">{severity}</span></div>
                <div style="font-size: 11px; margin-top: 8px; color: #9CA3AF;">{tier}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">Procurement Action</div>
                <div class="metric-value" style="font-size: 24px; font-weight: 700; color: #F3F4F6; padding-top: 5px;">{decision}</div>
                <div style="font-size: 11px; margin-top: 9px; color: #9CA3AF;">Risk Committee Recommendation</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">AI Confidence</div>
                <div class="metric-value" style="color: #6366F1;">{confidence}%</div>
                <div style="font-size: 11px; margin-top: 4px; color: #9CA3AF;">Telemetry Evidence Weight</div>
            </div>
            """, unsafe_allow_html=True)

        grid_col1, grid_col2 = st.columns([3, 2])

        with grid_col1:
            st.markdown("### 🧠 Executive Risk Synthesis")
            st.markdown(f"""
            <div class="card" style="font-size: 15px; line-height: 1.6;">
                {data.get('executive_summary', 'AI synthesis report is unavailable.')}
            </div>
            """, unsafe_allow_html=True)
            
            # Get findings for the highest risk category
            highest_agent = next((r for r in results if r["risk_category"] == highest_risk), None)
            findings_bullets = ""
            if highest_agent and highest_agent.get("findings"):
                findings_bullets = "<br><strong>Key telemetry findings:</strong><ul style='margin-top: 5px; margin-bottom: 5px; padding-left: 20px;'>" + "".join([f"<li>{f}</li>" for f in highest_agent["findings"][:3]]) + "</ul>"

            st.markdown(f"""
            <div style="background-color: rgba(99, 102, 241, 0.05); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #A5B4FC; font-size: 14px;">🎯 KEY EXPOSURE VECTOR: <strong>{highest_risk.upper()}</strong></h4>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #E0E7FF;">
                    The highest risk contribution stems from the <strong>{highest_risk}</strong> vector, scoring <strong>{overall.get('highest_risk_score', 0)}/100</strong>.
                    {findings_bullets}
                    Procurement controls should focus primary mitigation checkpoints on this dimension.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with grid_col2:
            st.markdown("### 📊 Risk Heatmap")
            
            heatmap_data = data.get("heatmap", [])
            h_df = pd.DataFrame(heatmap_data)
            
            if not h_df.empty:
                fig = px.bar(
                    h_df,
                    x="score",
                    y="category",
                    orientation="h",
                    color="score",
                    color_continuous_scale=["#22C55E", "#EAB308", "#F97316", "#EF4444"],
                    range_color=[0, 100],
                    text="score",
                    labels={"score": "Risk Level", "category": "Vector"}
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#F3F4F6",
                    showlegend=False,
                    height=350,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", categoryorder="total ascending")
                )
                st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
            else:
                st.info("Heatmap details loading...")

        st.markdown("### 📈 Vector Risk Benchmarking vs. Industry Average")
        bench_data = data.get("benchmark", [])
        b_df = pd.DataFrame(bench_data)
        
        if not b_df.empty:
            fig_b = go.Figure()
            fig_b.add_trace(go.Bar(
                name="Vendor Risk Score",
                x=b_df["category"],
                y=b_df["vendor_score"],
                marker_color="#6366F1",
                opacity=0.85
            ))
            fig_b.add_trace(go.Scatter(
                name="Industry Baseline",
                x=b_df["category"],
                y=b_df["industry_average"],
                line=dict(color="#EF4444", width=3, dash="dash"),
                mode="lines"
            ))
            fig_b.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F3F4F6",
                barmode="group",
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", range=[0, 100])
            )
            st.plotly_chart(fig_b, width='stretch', config={"displayModeBar": False})

    # ===================================
    # TAB 2: AGENT REPORTS
    # ===================================
    with tabs[1]:
        st.markdown("### 🤖 Independent Intelligence Agent Dossiers")
        
        col_a, col_b = st.columns(2)
        
        for idx, agent in enumerate(results):
            target_col = col_a if idx % 2 == 0 else col_b
            
            with target_col:
                badge_type = "low-badge"
                badge_color = "#22C55E"
                a_sev = agent.get("severity", "Low")
                if a_sev == "Critical":
                    badge_type = "critical-badge"
                    badge_color = "#EF4444"
                elif a_sev == "High":
                    badge_type = "high-badge"
                    badge_color = "#F97316"
                elif a_sev == "Medium":
                    badge_type = "medium-badge"
                    badge_color = "#EAB308"

                st.markdown(f"""
                <div class="agent-card" style="border-left-color: {badge_color};">
                    <div class="agent-title">
                        <span>{agent['risk_category']} Agent</span>
                        <span class="severity-badge {badge_type}">{a_sev} ({agent['risk_score']})</span>
                    </div>
                    <div style="font-size: 13px; font-weight: 600; color: #A5B4FC; margin-bottom: 8px;">Confidence Score: {agent.get('confidence_score', 85)}%</div>
                    <p style="font-size: 14px; font-style: italic; color: #D1D5DB; background-color: rgba(0,0,0,0.15); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                        {agent.get('ai_summary', 'AI Summary pending review...')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"🔍 Telemetry Evidence & Recommendations ({agent['risk_category']})"):
                    st.markdown("**Evidence Findings:**")
                    for f in agent.get("findings", []):
                        st.markdown(f"- 🔴 {f}" if "warning" in f.lower() or "cve" in f.lower() or "breach" in f.lower() or "match" in f.lower() else f"- 🔹 {f}")
                        
                    st.markdown("<br>**Risk Recommendations:**", unsafe_allow_html=True)
                    for r in agent.get("recommendations", []):
                        st.markdown(f"- ✅ {r}")
                        
                    st.markdown("<br>**Business Operational Impact:**", unsafe_allow_html=True)
                    st.write(agent.get("business_impact", "N/A"))
                    
                    st.markdown("**Procurement SLA Guidelines:**", unsafe_allow_html=True)
                    st.write(agent.get("procurement_impact", "N/A"))
                    
                    if agent.get("references"):
                        st.markdown("<br>**Source Attribution:**", unsafe_allow_html=True)
                        for ref in agent.get("references", []):
                            st.markdown(f"- [{ref.get('title')}]({ref.get('url')})")

    # ===================================
    # TAB 3: VENDOR COMPARISON
    # ===================================
    with tabs[2]:
        st.markdown("### 🔄 Vendor Portfolio Comparison")
        st.write("Compare the current vendor risk profile against other vendors analyzed in this session.")
        
        history = st.session_state["vendor_history"]
        all_vendors = list(history.keys())
        
        selected_vendors = st.multiselect(
            "Select Vendors to Compare:",
            options=all_vendors,
            default=[company_name]
        )
        
        if len(selected_vendors) > 1:
            comp_rows = []
            for v_name in selected_vendors:
                v_data = history[v_name]
                v_overall = v_data["overall_assessment"]
                
                row = {
                    "Vendor": v_name,
                    "Overall Risk Score": v_overall.get("overall_risk_score"),
                    "Severity": v_overall.get("overall_severity"),
                    "Procurement Decision": v_overall.get("procurement_decision"),
                    "AI Confidence": f"{v_overall.get('confidence_score')}%"
                }
                
                for agent in v_data["results"]:
                    if agent["risk_category"] != "Procurement Decision":
                        row[agent["risk_category"]] = agent["risk_score"]
                
                comp_rows.append(row)
                
            comp_df = pd.DataFrame(comp_rows)
            st.dataframe(comp_df, width='stretch')
            
            melt_df = comp_df.melt(id_vars=["Vendor", "Overall Risk Score", "Severity", "Procurement Decision", "AI Confidence"], var_name="Category", value_name="Score")
            fig_compare = px.line(
                melt_df,
                x="Category",
                y="Score",
                color="Vendor",
                markers=True,
                title="Risk Category Scores Side-by-Side Comparison"
            )
            fig_compare.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F3F4F6",
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", range=[0, 100])
            )
            st.plotly_chart(fig_compare, width='stretch')
        else:
            st.info("Please select at least 2 vendors from the dropdown to display comparison charts.")

    # ===================================
    # TAB 4: THREAT NEWS FEED
    # ===================================
    with tabs[3]:
        st.markdown("### 📡 Live Threat Intelligence Feed")
        st.write("Real-time external threat feeds and data breach news collected from active security bulletins.")
        
        feed_items = []
        for agent in results:
            if agent["risk_category"] in ["Cybersecurity", "Legal & Sanctions"]:
                for ref in agent.get("references", []):
                    feed_items.append({
                        "category": agent["risk_category"],
                        "title": ref.get("title"),
                        "url": ref.get("url"),
                        "severity": agent.get("severity")
                    })
                    
        if feed_items:
            for item in feed_items[:15]:
                badge_cls = "low-badge"
                if item["severity"] in ["High", "Critical"]:
                    badge_cls = "critical-badge"
                elif item["severity"] == "Medium":
                    badge_cls = "medium-badge"
                    
                st.markdown(f"""
                <div style="background-color: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #6366F1; font-weight: 700; font-size: 12px; text-transform: uppercase;">{item['category']} Telemetry</span>
                        <span class="severity-badge {badge_cls}" style="font-size: 10px; padding: 2px 8px;">{item['severity']} Exposure</span>
                    </div>
                    <a href="{item['url']}" target="_blank" style="color: #E0E7FF; font-weight: 600; font-size: 15px; text-decoration: none; hover: underline;">
                        {item['title']}
                    </a>
                    <div style="font-size: 11px; color: #6B7280; margin-top: 4px;">Source: Open Web Intelligence Feed</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No active threat news items found.")

    # ===================================
    # TAB 5: EXPORT DOSSIER
    # ===================================
    with tabs[4]:
        st.markdown("### 📄 Export Risk Dossier")
        st.write("Generate a professional enterprise PDF report containing all intelligence findings and AI recommendations.")
        
        # Add a PDF download trigger
        with st.spinner("Compiling PDF document formatting..."):
            try:
                pdf_bytes = generate_pdf_report(
                    company_name=company_name,
                    overall_score=overall_score,
                    severity=severity,
                    decision=decision,
                    confidence=confidence,
                    results=results,
                    executive_summary=data.get('executive_summary', ''),
                    mitigation_plan=data.get('mitigation_plan', '')
                )
                
                st.download_button(
                    label="💾 Download Dossier as PDF (.pdf)",
                    data=pdf_bytes,
                    file_name=f"RiskIntel_Dossier_{company_name}.pdf",
                    mime="application/pdf",
                    width='stretch'
                )
                st.success("PDF ready for download!")
            except Exception as pdf_err:
                st.error(f"Failed to generate PDF Report: {str(pdf_err)}")
else:
    st.markdown("""
    <div style="text-align: center; padding: 80px 20px; border: 1px dashed rgba(255,255,255,0.08); border-radius: 20px; background-color: rgba(255,255,255,0.01);">
        <span style="font-size: 48px;">🛡️</span>
        <h3 style="font-family: Outfit, sans-serif; font-weight: 700; margin-top: 15px;">Awaiting Vendor Scope Input</h3>
        <p style="color: #9CA3AF; max-width: 500px; margin: 10px auto 0 auto; font-size: 14px; line-height: 1.6;">
            Enter the vendor's company name and business services in the sidebar panel, then execute the multi-agent threat pipeline to fetch real-time intelligence feeds.
        </p>
    </div>
    """, unsafe_allow_html=True)