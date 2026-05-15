"""Streamlit UI — Vendor Onboarding Command Centre.

Flow mirrors the LangGraph pipeline:
  [Input] → Discovery → Qualification HITL → Risk Audit → Contract HITL → Decision Report
"""
import streamlit as st
import requests, time
from datetime import datetime

API = "http://localhost:8090"

st.set_page_config(page_title="Vendor Onboarding", page_icon="🏢", layout="wide")

st.markdown("""
<style>
  .stApp{background:#0a0a0f;color:#c9d1d9}
  section[data-testid="stSidebar"]{background:#0d1117;border-right:1px solid #21262d}
  h1,h2,h3{color:#58a6ff!important}
  .stMetric label{color:#8b949e!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.1em}

  /* Stage cards */
  .card{border-radius:12px;padding:20px;margin:10px 0;border:1px solid #21262d}
  .card-discovery   {background:#0d1a2d;border-left:4px solid #58a6ff}
  .card-qual        {background:#1a1400;border-left:4px solid #f0b429}
  .card-risk        {background:#0d1f17;border-left:4px solid #238636}
  .card-contract    {background:#1a1400;border-left:4px solid #f0b429}
  .card-decision    {border-left:4px solid #58a6ff}
  .card-go          {background:#0d1f17;border-left:4px solid #3fb950}
  .card-conditional {background:#1f1900;border-left:4px solid #f0b429}
  .card-nogo        {background:#1f0d0d;border-left:4px solid #da3633}

  /* Status badges */
  .badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:11px;font-weight:700;margin:2px}
  .badge-done   {background:#1a4429;color:#3fb950}
  .badge-wait   {background:#2d2000;color:#f0b429}
  .badge-pend   {background:#161b22;color:#8b949e}
  .badge-fail   {background:#3d1a1a;color:#f85149}
  .badge-go     {background:#1a4429;color:#3fb950;font-size:16px;padding:6px 20px}
  .badge-cond   {background:#2d2000;color:#f0b429;font-size:16px;padding:6px 20px}
  .badge-nogo   {background:#3d1a1a;color:#f85149;font-size:16px;padding:6px 20px}

  /* Pipeline connector dots */
  .dot-done{color:#3fb950;font-size:20px}
  .dot-active{color:#58a6ff;font-size:20px}
  .dot-pend{color:#30363d;font-size:20px}

  .stTextInput input,.stTextArea textarea{background:#161b22!important;color:#c9d1d9!important;border-color:#30363d!important}
  .stSelectbox div[data-baseweb]{background:#161b22!important}
  hr{border-color:#21262d!important}
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────

def api(method: str, path: str, **kwargs):
    try:
        r = getattr(requests, method)(f"{API}{path}", timeout=120, **kwargs)
        if r.ok:
            return r.json()
        st.error(f"API {r.status_code}: {r.text[:200]}")
    except Exception as e:
        st.error(f"Cannot reach backend: {e}")
    return None


def alive() -> bool:
    try:
        return requests.get(f"{API}/health", timeout=3).ok
    except Exception:
        return False


def fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y  %H:%M")
    except Exception:
        return iso


# ── Stage renderers ───────────────────────────────────────────────────────────

def render_discovery(d: dict):
    st.markdown('<div class="card card-discovery">', unsafe_allow_html=True)
    st.markdown("#### 🔍 Supplier Discovery")
    st.markdown(f'<span class="badge badge-done">✓ Complete</span>', unsafe_allow_html=True)
    st.markdown(f"**{d.get('company_summary','—')}**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Founded",      d.get("founded", "—"))
    c2.metric("HQ",           d.get("headquarters", "—"))
    c3.metric("Employees",    d.get("employees", "—"))
    c4.metric("Segment",      d.get("market_segment", "—"))
    st.markdown(f"**Products:** {', '.join(d.get('products', []))}")
    st.markdown(f"**Market Position:** {d.get('market_position', '—')}")
    st.markdown(f"**Recent Funding:** {d.get('recent_funding', '—')}")
    if d.get("sources"):
        with st.expander("Sources"):
            for s in d["sources"]:
                st.markdown(f"- {s}")
    st.markdown('</div>', unsafe_allow_html=True)


def render_qualification(q: dict, session_id: str, status: str):
    is_hitl = status == "qualification_hitl"
    cls     = "card-qual" if is_hitl else "card-discovery"
    st.markdown(f'<div class="card {cls}">', unsafe_allow_html=True)
    st.markdown("#### ✅ Qualification Review")
    if is_hitl:
        st.markdown('<span class="badge badge-wait">👤 Awaiting Your Review</span>', unsafe_allow_html=True)
    else:
        approved = q.get("hitl_approved")
        label = "✓ Approved" if approved else ("✗ Rejected" if approved is False else "✓ Complete")
        st.markdown(f'<span class="badge badge-done">{label}</span>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SOC2",        q.get("soc2_status", "—"))
    c2.metric("ISO 27001",   q.get("iso27001", "—"))
    c3.metric("GDPR",        "✓ Yes" if q.get("gdpr_compliant") else "✗ No")
    c4.metric("ESG Grade",   q.get("esg_grade", "—"))
    st.markdown(f"**Certifications:** {', '.join(q.get('certifications', []))}")
    st.markdown(f"**Notes:** {q.get('compliance_notes', '—')}")

    if is_hitl:
        st.markdown("---")
        st.markdown("##### 👤 Your Decision")
        with st.form("qual_form"):
            notes = st.text_area("Review notes", placeholder="Add comments or flag concerns…", height=60)
            st.markdown("**Override fields (optional):**")
            ov_soc2 = st.text_input("SOC2 Status override",  value=q.get("soc2_status", ""))
            ov_esg  = st.text_input("ESG Grade override",    value=q.get("esg_grade", ""))
            ov_notes= st.text_input("Compliance notes override", value=q.get("compliance_notes", ""))
            c1, c2 = st.columns(2)
            approved_btn = c1.form_submit_button("✅ Approve & Proceed", type="primary", use_container_width=True)
            modify_btn   = c2.form_submit_button("✏️ Apply Modifications", use_container_width=True)

        if approved_btn:
            overrides = {}
            if ov_soc2  != q.get("soc2_status",""):  overrides["soc2_status"]      = ov_soc2
            if ov_esg   != q.get("esg_grade",""):     overrides["esg_grade"]        = ov_esg
            if ov_notes != q.get("compliance_notes",""):overrides["compliance_notes"]= ov_notes
            result = api("post", f"/sessions/{session_id}/approve/qualification",
                         json={"decision": "approve", "notes": notes, "overrides": overrides})
            if result:
                st.success("Qualification approved — running Risk Audit…")
                st.session_state.session = result
                st.rerun()

        if modify_btn:
            overrides = {
                "soc2_status":      ov_soc2,
                "esg_grade":        ov_esg,
                "compliance_notes": ov_notes,
            }
            result = api("post", f"/sessions/{session_id}/modify/qualification",
                         json={"decision": "modify", "notes": notes, "overrides": overrides})
            if result:
                st.info("Modifications saved. Review again then approve.")
                st.session_state.session = result
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_risk(r: dict):
    score = r.get("score", 0)
    level = r.get("level", "—")
    colour = "🟢" if score <= 3.5 else "🟡" if score <= 6.5 else "🔴"
    st.markdown('<div class="card card-risk">', unsafe_allow_html=True)
    st.markdown("#### 🛡️ Risk Audit")
    st.markdown('<span class="badge badge-done">✓ Complete — 24/7 Monitoring Active</span>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk Score",   f"{colour} {score}/10")
    c2.metric("Level",        level)
    c3.metric("Security",     r.get("security_rating", "—"))
    c4.metric("Fin. Stability", r.get("financial_stability", "—"))
    st.markdown(f"**Risk Factors:** {' · '.join(r.get('risk_factors', []))}")
    st.markdown(f"**Recommendation:** {r.get('recommendation', '—')}")
    with st.expander("Monitoring Hooks"):
        cy = r.get("cyber_monitoring", {})
        fi = r.get("financial_monitoring", {})
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Cyber Monitoring**")
            st.markdown(f"Status: `{cy.get('status','—')}` · Provider: {cy.get('provider','—')}")
            st.markdown(f"Cadence: {cy.get('cadence','—')}")
        with c2:
            st.markdown("**Financial Monitoring**")
            st.markdown(f"Status: `{fi.get('status','—')}` · Provider: {fi.get('provider','—')}")
            st.markdown(f"Cadence: {fi.get('cadence','—')}")
    st.markdown('</div>', unsafe_allow_html=True)


def render_contract(c: dict, session_id: str, status: str):
    is_hitl = status == "contract_hitl"
    cls     = "card-contract" if is_hitl else "card-discovery"
    st.markdown(f'<div class="card {cls}">', unsafe_allow_html=True)
    st.markdown("#### 📄 Contract Review")
    if is_hitl:
        st.markdown('<span class="badge badge-wait">👤 Awaiting Your Review</span>', unsafe_allow_html=True)
    else:
        approved = c.get("hitl_approved")
        label = "✓ Approved" if approved else ("✗ Rejected" if approved is False else "✓ Complete")
        st.markdown(f'<span class="badge badge-done">{label}</span>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Term",          c.get("suggested_term", "—"))
    c2.metric("Payment",       c.get("payment_terms", "—"))
    c3.metric("SLA Uptime",    c.get("sla_uptime", "—"))
    c4.metric("Termination",   c.get("termination_notice", "—"))
    st.markdown(f"**MSA Status:** {c.get('msa_status','—')}")
    st.markdown(f"**Price Protection:** {c.get('price_protection','—')}")
    st.markdown(f"**Savings Opportunity:** `{c.get('savings_opportunity','—')}`")

    with st.expander("Key Clauses"):
        for clause in c.get("key_clauses", []):
            st.markdown(f"- {clause}")

    with st.expander("Negotiation Blueprint"):
        for bp in c.get("negotiation_blueprint", []):
            if isinstance(bp, dict):
                st.markdown(f"**{bp.get('clause','—')}**")
                cc1, cc2 = st.columns(2)
                cc1.markdown(f"Current: `{bp.get('current','—')}`")
                cc2.markdown(f"Target: `{bp.get('target','—')}`")
                st.caption(f"Rationale: {bp.get('rationale','')}")
                st.markdown("---")

    if is_hitl:
        st.markdown("---")
        st.markdown("##### 👤 Your Decision")
        with st.form("contract_form"):
            notes    = st.text_area("Review notes", placeholder="Add negotiation comments…", height=60)
            ov_term  = st.text_input("Override term",           value=c.get("suggested_term",""))
            ov_pay   = st.text_input("Override payment terms",  value=c.get("payment_terms",""))
            ov_sav   = st.text_input("Override savings figure", value=c.get("savings_opportunity",""))
            cc1, cc2 = st.columns(2)
            approve_btn = cc1.form_submit_button("✅ Approve & Proceed to Decision", type="primary", use_container_width=True)
            modify_btn  = cc2.form_submit_button("✏️ Apply Modifications", use_container_width=True)

        if approve_btn:
            overrides = {}
            if ov_term != c.get("suggested_term",""):  overrides["suggested_term"]      = ov_term
            if ov_pay  != c.get("payment_terms",""):   overrides["payment_terms"]       = ov_pay
            if ov_sav  != c.get("savings_opportunity",""):overrides["savings_opportunity"]= ov_sav
            result = api("post", f"/sessions/{session_id}/approve/contract",
                         json={"decision": "approve", "notes": notes, "overrides": overrides})
            if result:
                st.success("Contract approved — computing final verdict…")
                st.session_state.session = result
                st.rerun()

        if modify_btn:
            overrides = {"suggested_term": ov_term, "payment_terms": ov_pay, "savings_opportunity": ov_sav}
            result = api("post", f"/sessions/{session_id}/modify/contract",
                         json={"decision": "modify", "notes": notes, "overrides": overrides})
            if result:
                st.info("Modifications saved. Review again then approve.")
                st.session_state.session = result
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_verdict(v: dict, vendor_name: str):
    verdict = v.get("verdict", "")
    colour_map = {"GO": "go", "CONDITIONAL_GO": "cond", "NO_GO": "nogo"}
    badge_map  = {"GO": "🟢 GO TO ONBOARD", "CONDITIONAL_GO": "🟡 CONDITIONAL GO", "NO_GO": "🔴 NO-GO"}
    cls   = colour_map.get(verdict, "go")
    label = badge_map.get(verdict, verdict)

    st.markdown(f'<div class="card card-{cls}">', unsafe_allow_html=True)
    st.markdown("#### 🎯 Decision Terminal — System Verdict")
    st.markdown(f'<span class="badge badge-{cls}">{label}</span>', unsafe_allow_html=True)
    st.markdown("")
    st.markdown(f"**{v.get('summary', '')}**")
    st.markdown("---")
    st.markdown(f"**Aggregated Logic:** {v.get('aggregated_logic', '—')}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Savings",  v.get("total_savings", "—"))
    c2.metric("Risk Summary",   v.get("risk_summary", "—")[:40])
    c3.metric("Compliance",     v.get("compliance_summary", "—")[:40])

    if verdict == "GO":
        st.success(f"✅ {vendor_name} has been promoted to the Production Vendor registry.")
    elif verdict == "CONDITIONAL_GO":
        st.warning("⚠️ Proceed with enhanced monitoring. Schedule 6-month compliance review.")
    else:
        st.error("❌ Onboarding rejected. Vendor must remediate gaps before re-evaluation.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🏢 Vendor Onboarding")

    if not alive():
        st.error("⚠️ Backend offline\n\n`python -m backend.main`")
        st.stop()
    st.success("● Backend connected")

    st.markdown("---")
    st.markdown("#### ➕ New Onboarding")
    with st.form("new_vendor"):
        vendor_name = st.text_input("Vendor Name *", placeholder="e.g. Salesforce")
        submit      = st.form_submit_button("🚀 Start Pipeline", use_container_width=True, type="primary")
        if submit and vendor_name.strip():
            with st.spinner(f"Launching pipeline for {vendor_name}…"):
                result = api("post", "/sessions", json={"vendor_name": vendor_name.strip()})
            if result:
                st.session_state.session = result
                st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Sessions")
    sessions = api("get", "/sessions") or []
    for s in sessions:
        emoji   = "🟢" if s["status"] == "approved" else "🔴" if s["status"] == "rejected" else "🟡"
        label   = f"{emoji} {s['vendor_name']}"
        is_sel  = st.session_state.get("session", {}).get("id") == s["id"]
        if st.button(label, key=f"sel_{s['id']}", use_container_width=True,
                     type="primary" if is_sel else "secondary"):
            full = api("get", f"/sessions/{s['id']}")
            if full:
                st.session_state.session = full
                st.rerun()

    st.markdown("---")
    total = len(sessions)
    done  = sum(1 for s in sessions if s["status"] == "approved")
    st.metric("Total", total)
    st.metric("Approved", done)


# ── Main workspace ────────────────────────────────────────────────────────────

st.markdown("# 🏢 VENDOR ONBOARDING COMMAND CENTRE")
st.markdown("*Agentic pipeline · LangGraph state machine · HITL gates · GenAI agents*")
st.markdown("---")

sess = st.session_state.get("session")

if not sess:
    # Production vendors table
    prod = api("get", "/production") or []
    if prod:
        st.markdown("### ✅ Production Vendor Registry")
        for v in prod:
            st.markdown(
                f'<div class="card card-go"><b>{v["vendor_name"]}</b> &nbsp; '
                f'<span class="badge badge-done">Onboarded {fmt_date(v["onboarded_at"])}</span>'
                f'<br>Risk: {v["risk_level"]} · ESG: {v["esg_grade"]} · '
                f'Term: {v["contract_term"]} · Savings: {v["total_savings"]}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("👈  Enter a vendor name in the sidebar to launch the onboarding pipeline.")
else:
    vendor_name = sess.get("vendor_name", "—")
    status      = sess.get("status", "discovery")
    session_id  = sess.get("id")

    # Refresh button
    col_h, col_r = st.columns([5, 1])
    col_h.markdown(f"## {vendor_name}")
    if col_r.button("🔄 Refresh"):
        fresh = api("get", f"/sessions/{session_id}")
        if fresh:
            st.session_state.session = fresh
        st.rerun()

    # Pipeline progress bar
    STAGES   = ["discovery", "qualification_hitl", "risk_audit", "contract_hitl", "decision", "approved"]
    cur_idx  = STAGES.index(status) if status in STAGES else 0
    progress = (cur_idx) / (len(STAGES) - 1)
    st.progress(progress)
    st.caption(f"Stage: **{status.replace('_', ' ').upper()}**")
    st.markdown("---")

    # Render completed / active stages
    if sess.get("discovery"):
        render_discovery(sess["discovery"])

    if sess.get("qualification"):
        render_qualification(sess["qualification"], session_id, status)
    elif status == "qualification_hitl":
        st.info("⚙️ Qualification agent running… please wait.")

    if sess.get("risk"):
        render_risk(sess["risk"])
    elif status == "risk_audit":
        st.info("⚙️ Risk audit agent running… please wait.")

    if sess.get("contract"):
        render_contract(sess["contract"], session_id, status)
    elif status == "contract_hitl":
        st.info("⚙️ Contract review agent running… please wait.")

    if sess.get("verdict"):
        render_verdict(sess["verdict"], vendor_name)

    # Auto-refresh while pipeline is actively running (non-HITL stages)
    auto_refresh_stages = {"discovery", "risk_audit", "decision"}
    if status in auto_refresh_stages:
        time.sleep(3)
        fresh = api("get", f"/sessions/{session_id}")
        if fresh:
            st.session_state.session = fresh
        st.rerun()
