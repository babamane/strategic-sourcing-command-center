"""
app_v9.py — VendorFlow AI · CRA Enterprise Dashboard
======================================================
Operational AI Workflow Monitor • Enterprise Trigger Center — Clean, interactive, end-to-end connected.

Pages:
  1. Operations Overview  — KPIs, live workflow state, activity feed
  2. Workflow Monitor     — Node-level stage visibility per contract
  3. Trigger Center       — All 6 trigger types with live execution state
  4. Alert Center         — Critical contracts, escalations, util alerts
  5. Execution Logs       — Full audit trail, email log, terminal

Run: streamlit run app_v9.py
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timezone
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Enforce Python 3.11 runtime for the dashboard
import sys
# Temporarily disabled for testing on Python 3.14
# if sys.version_info[:2] != (3, 11):
#     sys.stderr.write(f"ERROR: VendorFlow AI requires Python 3.11, found {sys.version}\n")
#     raise SystemExit(1)

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_DIR         = os.getenv("DATA_DIR", "data")
STATE_FILE       = os.path.join(DATA_DIR, "agent_state.json")
TRIGGER_LOG_FILE = os.path.join(DATA_DIR, "trigger_log.json")
EMAIL_STATE_FILE = os.path.join(DATA_DIR, "email_state.json")
_CSV_CANDIDATES  = [
    os.path.join(DATA_DIR, "renewal_drafts", "merged_dataset_FINAL_fabricated_1341_util_adjusted.csv"),
    os.path.join(DATA_DIR, "merged_dataset_FINAL_fabricated_1341_util_adjusted.csv"),
    os.path.join(DATA_DIR, "renewal_drafts", "merged_dataset_FINAL_fabricated_1341_util1_adjusted.csv"),
    os.path.join(DATA_DIR, "merged_dataset_FINAL_fabricated_1341_util1_adjusted.csv"),
]
CSV_FILE         = next((p for p in _CSV_CANDIDATES if os.path.exists(p)), _CSV_CANDIDATES[0])
BACKEND_URL      = os.getenv("BASE_URL", "http://localhost:8001")
FONT             = "'Inter','Segoe UI',system-ui,sans-serif"

VENDORS      = ["OpenAI","Atlassify","Cloudora","Nexaflow","Veloxa","Prismly","Databridge","Salesforce","Microsoft","AWS"]
STAGE_ORDER  = ["Planning","Budgeting","Approval","Execution","Closed"]

st.set_page_config(
    page_title="VendorFlow AI · CRA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# THEME
# ══════════════════════════════════════════════════════════════════════════════
DARK = {
    "bg":"#07090F","sidebar":"#0B0E17","card":"#0F1420","card2":"#131928",
    "border":"#1C2640","border2":"#243050","text":"#E2E8F0","muted":"#64748B",
    "accent":"#3B82F6","accent2":"#6366F1","green":"#10B981","amber":"#F59E0B",
    "red":"#EF4444","purple":"#8B5CF6","cyan":"#06B6D4","orange":"#F97316",
    "glow":"rgba(59,130,246,0.18)","glow_g":"rgba(16,185,129,0.15)",
    "glow_r":"rgba(239,68,68,0.18)","glow_a":"rgba(245,158,11,0.15)",
    "grad":"linear-gradient(135deg,#3B82F6,#6366F1)",
    "grad2":"linear-gradient(135deg,#10B981,#06B6D4)",
    "grad_r":"linear-gradient(135deg,#EF4444,#F97316)",
}
LIGHT = {
    "bg":"#F0F4FF","sidebar":"#0F172A","card":"#FFFFFF","card2":"#F8FAFF",
    "border":"#E2E8F0","border2":"#CBD5E1","text":"#0F172A","muted":"#64748B",
    "accent":"#2563EB","accent2":"#4F46E5","green":"#059669","amber":"#D97706",
    "red":"#DC2626","purple":"#7C3AED","cyan":"#0891B2","orange":"#EA580C",
    "glow":"rgba(37,99,235,0.10)","glow_g":"rgba(5,150,105,0.10)",
    "glow_r":"rgba(220,38,38,0.12)","glow_a":"rgba(217,119,6,0.10)",
    "grad":"linear-gradient(135deg,#2563EB,#4F46E5)",
    "grad2":"linear-gradient(135deg,#059669,#0891B2)",
    "grad_r":"linear-gradient(135deg,#DC2626,#EA580C)",
}

def T():
    return LIGHT

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _load_json(p):
    try:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _force_reload_states():
    """Force reload all JSON states from disk."""
    global _cached_agent_state, _cached_trigger_log, _cached_email_state
    _cached_agent_state = None
    _cached_trigger_log = None
    _cached_email_state = None

# Cached state variables
_cached_agent_state = None
_cached_trigger_log = None
_cached_email_state = None

def _ago(iso):
    try:
        d = datetime.fromisoformat(iso.replace("Z",""))
        s = (datetime.now() - d).total_seconds()
        if s < 60:   return "just now"
        if s < 3600: return f"{int(s//60)}m ago"
        return f"{int(s//3600)}h ago"
    except:
        return "—"

def _map_vendor(orig, cid):
    if isinstance(orig, str) and orig.lower().startswith("vendor"):
        digits = "".join(c for c in str(cid) if c.isdigit())
        try: idx = int(digits) if digits else 0
        except: idx = 0
        return VENDORS[idx % len(VENDORS)]
    return orig

def badge(lbl, col="blue"):
    return f"<span class='vf-badge vf-badge-{col}'>{lbl}</span>"

def dot(col="green"):
    return f"<span class='vf-dot vf-dot-{col}'></span>"

def bar(pct, color=None):
    t = T()
    c = color or t["accent"]
    return (f"<div class='vf-bar'>"
            f"<div class='vf-bar-fill' style='width:{min(float(pct),100):.1f}%;background:{c}'></div>"
            f"</div>")

def sec(label, pill=""):
    t = T()
    ph = f"<span class='vf-pill'>{pill}</span>" if pill else ""
    st.markdown(f"<div class='vf-sec'>{ph}<h3>{label}</h3></div>", unsafe_allow_html=True)

def _load_csv():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["Days_to_Renewal"] = pd.to_numeric(df["Days_to_Renewal"], errors="coerce").fillna(999)
        df["Avg_Utilization_Pct"] = pd.to_numeric(
            df["Avg_Utilization_Pct"].astype(str).str.replace("%",""), errors="coerce").fillna(0)
        df["Total_Annual_Budget_USD"] = pd.to_numeric(df["Total_Annual_Budget_USD"], errors="coerce").fillna(0)
        df["Vendor"] = df.apply(lambda r: _map_vendor(r["Vendor"], r["Contract_ID"]), axis=1)
        return df
    return pd.DataFrame()


def _load_agent_state():
    global _cached_agent_state
    if _cached_agent_state is None:
        _cached_agent_state = _load_json(STATE_FILE)
    return _cached_agent_state or {}


def _enrich_df_with_agent_state(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    agent_state = _load_agent_state()
    if not agent_state:
        return df

    state_rows = []
    for cid, info in agent_state.items():
        state_rows.append({
            "Contract_ID": cid,
            "Stage": info.get("Stage", "Planning"),
            "Pending_With": info.get("Pending_With", "Procurement Team"),
            "Email_Sent": info.get("Email_Sent", False),
            "Execution_Status": info.get("Execution_Status", "Running"),
            "Escalated": info.get("Escalated", False),
        })

    state_df = pd.DataFrame(state_rows)
    if state_df.empty:
        return df

    merged = df.merge(state_df, on="Contract_ID", how="left")
    return merged


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df
    if filtered.empty:
        return filtered

    if st.session_state.get("filter_vendor", "All") != "All":
        filtered = filtered[filtered["Vendor"] == st.session_state["filter_vendor"]]

    if st.session_state.get("filter_criticality", "All") != "All":
        crit = st.session_state["filter_criticality"]
        if crit == "Critical (≤7d)":
            filtered = filtered[filtered["Days_to_Renewal"] <= 7]
        elif crit == "Urgent (≤30d)":
            filtered = filtered[filtered["Days_to_Renewal"] <= 30]
        elif crit == "Normal (>30d)":
            filtered = filtered[filtered["Days_to_Renewal"] > 30]

    if st.session_state.get("filter_license", "All") != "All":
        filtered = filtered[filtered["License_Type"] == st.session_state["filter_license"]]

    if st.session_state.get("filter_owner", "All") != "All" and "Pending_With" in filtered.columns:
        filtered = filtered[filtered["Pending_With"] == st.session_state["filter_owner"]]

    return filtered


def _filters_active() -> bool:
    return any([
        st.session_state.get("filter_vendor", "All") != "All",
        st.session_state.get("filter_criticality", "All") != "All",
        st.session_state.get("filter_license", "All") != "All",
        st.session_state.get("filter_owner", "All") != "All",
    ])

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

def inject_css():
    t = T()
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*{{box-sizing:border-box;}}
html,body,.stApp{{font-family:{FONT};background:{t['bg']};color:{t['text']};margin:0;}}
.block-container{{padding:0!important;max-width:100%!important;}}
section[data-testid="stSidebar"],[data-testid="stHeader"],footer,#MainMenu{{display:none!important;}}
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:{t['border2']};border-radius:4px;}}

[data-testid="metric-container"]{{
  background:{t['card']}!important;border:1px solid {t['border']}!important;
  border-radius:14px!important;padding:1rem 1.2rem!important;
  box-shadow:0 2px 12px rgba(0,0,0,.08);transition:all .25s;position:relative;overflow:hidden;
}}
[data-testid="metric-container"]:hover{{border-color:{t['accent']}!important;box-shadow:0 0 24px {t['glow']}!important;transform:translateY(-2px);}}
[data-testid="metric-container"]::before{{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:{t['grad']};}}
[data-testid="metric-container"] label{{color:{t['muted']}!important;font-size:.63rem!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.09em;}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:{t['text']}!important;font-weight:800!important;font-size:1.7rem!important;}}
[data-testid="metric-container"] [data-testid="stMetricDelta"]{{font-size:.68rem!important;}}

[data-testid="stDataFrame"]{{border-radius:12px;overflow:hidden;border:1px solid {t['border']};}}
[data-testid="stDataFrame"] th{{background:{t['card2']}!important;color:{t['muted']}!important;font-size:.62rem!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.05em;}}

.stButton>button{{background:transparent!important;border:1px solid {t['border2']}!important;
  color:{t['text']}!important;border-radius:9px!important;font-size:.78rem!important;
  font-weight:500!important;padding:.35rem .9rem!important;transition:all .2s!important;}}
.stButton>button:hover{{background:{t['glow']}!important;border-color:{t['accent']}!important;color:{t['accent']}!important;}}
[data-testid="stDownloadButton"]>button{{background:{t['grad']}!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:700!important;}}

[data-baseweb="select"]>div,[data-baseweb="input"]>div{{background:{t['card']}!important;border-color:{t['border2']}!important;color:{t['text']}!important;border-radius:9px!important;}}
.stSelectbox label,.stMultiSelect label,.stSlider label,.stRadio label{{color:{t['muted']}!important;font-size:.63rem!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.06em;}}

/* ── LAYOUT ── */
.vf-shell{{display:flex;min-height:100vh;}}
.vf-sidebar{{width:220px;min-width:220px;background:{t['sidebar']};border-right:1px solid #1C2640;
  display:flex;flex-direction:column;position:fixed;top:0;left:0;height:100vh;z-index:999;overflow-y:auto;}}
.vf-content{{margin-left:220px;flex:1;min-height:100vh;background:{t['bg']};}}

/* ── TOPBAR ── */
.vf-topbar{{background:{t['card']}dd;border-bottom:1px solid {t['border']};
  backdrop-filter:blur(16px);padding:.7rem 1.6rem;
  display:flex;align-items:center;justify-content:space-between;
  position:relative;z-index:100;}}
.vf-topbar-title{{font-size:1rem;font-weight:700;color:{t['text']};margin:0;}}
.vf-topbar-sub{{font-size:.66rem;color:{t['muted']};margin:1px 0 0;}}

/* ── BRAND ── */
.vf-brand{{padding:1.1rem 1rem .9rem;border-bottom:1px solid #1C2640;}}
.vf-brand-name{{font-size:1rem;font-weight:800;background:{t['grad']};
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.vf-brand-sub{{font-size:.58rem;color:#475569;margin-top:2px;text-transform:uppercase;letter-spacing:.1em;}}

/* ── PULSE ── */
.vf-pulse{{width:7px;height:7px;border-radius:50%;background:{t['green']};
  display:inline-block;margin-right:5px;box-shadow:0 0 7px {t['green']};
  animation:vf-pulse 2s infinite;}}
@keyframes vf-pulse{{0%,100%{{opacity:1;transform:scale(1);}}50%{{opacity:.4;transform:scale(.8);}}}}

/* ── NAV ── */
.vf-nav-label{{font-size:.56rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.1em;color:#475569;padding:.8rem 1rem .2rem;}}
.vf-nav-btn{{display:flex;align-items:center;gap:9px;width:100%;padding:.55rem 1rem;
  font-size:.8rem;color:#94A3B8;cursor:pointer;border-left:2px solid transparent;
  transition:all .15s;border:none;background:transparent;text-align:left;}}
.vf-nav-btn:hover{{color:#E2E8F0;background:rgba(255,255,255,.04);}}
.vf-nav-btn.active{{color:#F8FAFC;background:rgba(59,130,246,.14);border-left:2px solid {t['accent']};}}

/* ── SIGNAL BADGES ── */
.vf-sig-row{{display:flex;justify-content:space-between;align-items:center;
  padding:.28rem 1rem;font-size:.68rem;color:#94A3B8;}}
.vf-sig-badge{{border-radius:999px;padding:1px 7px;font-size:.6rem;
  font-weight:700;color:#fff;min-width:22px;text-align:center;}}

/* ── MAIN ── */
.vf-main{{padding:1.2rem 1.6rem 2.5rem;}}

/* ── SECTION HEADER ── */
.vf-sec{{display:flex;align-items:center;gap:8px;margin:.9rem 0 .45rem;}}
.vf-sec h3{{margin:0;font-size:.95rem;font-weight:700;color:{t['text']};}}
.vf-pill{{background:{t['accent']}22;color:{t['accent']};font-size:.6rem;
  font-weight:700;padding:2px 8px;border-radius:999px;
  border:1px solid {t['accent']}44;text-transform:uppercase;letter-spacing:.04em;}}

/* ── CARD ── */
.vf-card{{background:{t['card']};border:1px solid {t['border']};
  border-radius:14px;padding:1.2rem 1.3rem;margin-bottom:.75rem;transition:border-color .2s;}}
.vf-card:hover{{border-color:{t['border2']};}}
.vf-card-title{{font-size:.78rem;font-weight:700;color:{t['text']};
  margin-bottom:.75rem;display:flex;align-items:center;justify-content:space-between;}}

/* ── BADGES ── */
.vf-badge{{display:inline-flex;align-items:center;gap:3px;
  padding:2px 9px;border-radius:999px;font-size:.65rem;font-weight:600;}}
.vf-badge-blue{{background:{t['accent']}20;color:{t['accent']};border:1px solid {t['accent']}44;}}
.vf-badge-green{{background:{t['green']}20;color:{t['green']};border:1px solid {t['green']}44;}}
.vf-badge-amber{{background:{t['amber']}20;color:{t['amber']};border:1px solid {t['amber']}44;}}
.vf-badge-red{{background:{t['red']}20;color:{t['red']};border:1px solid {t['red']}44;}}
.vf-badge-purple{{background:{t['purple']}20;color:{t['purple']};border:1px solid {t['purple']}44;}}
.vf-badge-cyan{{background:{t['cyan']}20;color:{t['cyan']};border:1px solid {t['cyan']}44;}}
.vf-badge-orange{{background:{t['orange']}20;color:{t['orange']};border:1px solid {t['orange']}44;}}
.vf-badge-gray{{background:{t['muted']}20;color:{t['muted']};border:1px solid {t['muted']}33;}}

/* ── GLOW DOTS ── */
.vf-dot{{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:4px;flex-shrink:0;}}
.vf-dot-green{{background:{t['green']};box-shadow:0 0 6px {t['green']};}}
.vf-dot-amber{{background:{t['amber']};box-shadow:0 0 6px {t['amber']};}}
.vf-dot-red{{background:{t['red']};box-shadow:0 0 6px {t['red']};animation:vf-pulse 1.5s infinite;}}
.vf-dot-blue{{background:{t['accent']};box-shadow:0 0 6px {t['accent']};}}
.vf-dot-purple{{background:{t['purple']};box-shadow:0 0 6px {t['purple']};}}
.vf-dot-gray{{background:{t['muted']};}}

/* ── PIPELINE NODES ── */
.vf-pipe{{display:flex;align-items:stretch;gap:0;margin:.8rem 0 1.2rem;}}
.vf-stage{{flex:1;text-align:center;padding:.7rem .4rem .5rem;
  border-top:3px solid {t['border2']};font-size:.65rem;color:{t['muted']};transition:all .2s;}}
.vf-stage.active{{color:{t['accent']};border-top-color:{t['accent']};
  background:{t['accent']}0A;border-radius:0 0 6px 6px;}}
.vf-stage.done{{color:{t['green']};border-top-color:{t['green']}55;}}
.vf-stage.failed{{color:{t['red']};border-top-color:{t['red']}55;}}
.vf-stage-num{{width:24px;height:24px;border-radius:50%;margin:.3rem auto .18rem;
  display:flex;align-items:center;justify-content:center;
  font-size:.65rem;font-weight:700;
  background:{t['border']};color:{t['muted']};border:1px solid {t['border2']};}}
.vf-stage.active .vf-stage-num{{background:{t['grad']};color:#fff;border:none;box-shadow:0 0 10px {t['accent']};}}
.vf-stage.done .vf-stage-num{{background:{t['green']}22;color:{t['green']};border-color:{t['green']}44;}}
.vf-stage.failed .vf-stage-num{{background:{t['red']}22;color:{t['red']};border-color:{t['red']}44;}}
.vf-arrow{{color:{t['muted']};font-size:.75rem;display:flex;align-items:center;
  padding:0 2px;margin-top:.5rem;}}

/* ── TRIGGER CARDS ── */
.vf-tc{{border-radius:12px;padding:1.1rem 1.2rem;border:1px solid;transition:transform .2s;cursor:default;}}
.vf-tc:hover{{transform:translateY(-2px);}}
.vf-tc-blue{{background:{t['accent']}0E;border-color:{t['accent']}33;}}
.vf-tc-amber{{background:{t['amber']}0E;border-color:{t['amber']}33;}}
.vf-tc-red{{background:{t['red']}0E;border-color:{t['red']}33;}}
.vf-tc-purple{{background:{t['purple']}0E;border-color:{t['purple']}33;}}
.vf-tc-orange{{background:{t['orange']}0E;border-color:{t['orange']}33;}}
.vf-tc-green{{background:{t['green']}0E;border-color:{t['green']}33;}}
.vf-tc-num{{font-size:2rem;font-weight:800;line-height:1;margin-bottom:2px;}}
.vf-tc-blue .vf-tc-num{{color:{t['accent']};}}
.vf-tc-amber .vf-tc-num{{color:{t['amber']};}}
.vf-tc-red .vf-tc-num{{color:{t['red']};}}
.vf-tc-purple .vf-tc-num{{color:{t['purple']};}}
.vf-tc-orange .vf-tc-num{{color:{t['orange']};}}
.vf-tc-green .vf-tc-num{{color:{t['green']};}}
.vf-tc-lbl{{font-size:.72rem;font-weight:600;margin-bottom:2px;}}
.vf-tc-blue .vf-tc-lbl{{color:{t['accent']};}}
.vf-tc-amber .vf-tc-lbl{{color:{t['amber']};}}
.vf-tc-red .vf-tc-lbl{{color:{t['red']};}}
.vf-tc-purple .vf-tc-lbl{{color:{t['purple']};}}
.vf-tc-orange .vf-tc-lbl{{color:{t['orange']};}}
.vf-tc-green .vf-tc-lbl{{color:{t['green']};}}
.vf-tc-sub{{font-size:.63rem;color:{t['muted']};}}

/* ── TABLE ── */
.vf-tbl{{width:100%;border-collapse:collapse;font-size:.72rem;}}
.vf-tbl th{{color:{t['muted']};font-size:.6rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;padding:.5rem .7rem;border-bottom:1px solid {t['border']};text-align:left;}}
.vf-tbl td{{padding:.55rem .7rem;border-bottom:1px solid {t['border']};color:{t['text']};vertical-align:middle;}}
.vf-tbl tr:last-child td{{border-bottom:none;}}
.vf-tbl tr:hover td{{background:{t['glow']};}}

/* ── PROGRESS BAR ── */
.vf-bar{{height:5px;border-radius:3px;background:{t['border']};overflow:hidden;margin-top:3px;}}
.vf-bar-fill{{height:100%;border-radius:3px;transition:width .6s;}}

/* ── HERO ── */
.vf-hero{{background:{t['card']};border:1px solid {t['border']};border-radius:16px;
  padding:1.6rem 1.8rem;margin-bottom:1rem;
  background-image:radial-gradient(ellipse at top right,{t['accent']}0A,transparent 60%),
                   radial-gradient(ellipse at bottom left,{t['accent2']}08,transparent 60%);}}
.vf-hero-title{{font-size:1.35rem;font-weight:800;color:{t['text']};margin:0 0 4px;}}
.vf-hero-sub{{font-size:.78rem;color:{t['muted']};margin:0;}}

/* ── ALERT CARDS ── */
.vf-alert-card{{border-radius:12px;padding:1rem 1.1rem;border:1px solid;margin-bottom:.6rem;}}
.vf-alert-crit{{background:{t['red']}0D;border-color:{t['red']}44;}}
.vf-alert-warn{{background:{t['amber']}0D;border-color:{t['amber']}44;}}
.vf-alert-info{{background:{t['accent']}0D;border-color:{t['accent']}44;}}
.vf-alert-purple{{background:{t['purple']}0D;border-color:{t['purple']}44;}}
.vf-alert-title{{font-size:.78rem;font-weight:700;margin-bottom:3px;}}
.vf-alert-crit .vf-alert-title{{color:{t['red']};}}
.vf-alert-warn .vf-alert-title{{color:{t['amber']};}}
.vf-alert-info .vf-alert-title{{color:{t['accent']};}}
.vf-alert-purple .vf-alert-title{{color:{t['purple']};}}
.vf-alert-body{{font-size:.7rem;color:{t['muted']};}}

/* ── TERMINAL ── */
.vf-terminal{{background:#050810;border:1px solid #1C2640;border-radius:12px;
  padding:1rem 1.2rem;font-family:'Courier New',monospace;font-size:.72rem;
  color:#94A3B8;max-height:380px;overflow-y:auto;}}
.vf-terminal .ts{{color:#334155;margin-right:8px;}}
.vf-terminal .ok{{color:#10B981;}}
.vf-terminal .warn{{color:#F59E0B;}}
.vf-terminal .err{{color:#EF4444;}}
.vf-terminal .info{{color:#3B82F6;}}
.vf-terminal .purple{{color:#8B5CF6;}}

/* ── FEED ── */
.vf-feed-item{{display:flex;gap:.7rem;padding:.45rem 0;border-bottom:1px solid {t['border']};
  font-size:.72rem;align-items:flex-start;}}
.vf-feed-item:last-child{{border-bottom:none;}}
.vf-feed-ts{{color:{t['muted']};font-size:.62rem;white-space:nowrap;margin-top:1px;}}

/* ── WORKFLOW NODE CARD ── */
.vf-wf-card{{background:{t['card']};border:1px solid {t['border']};border-radius:14px;
  padding:1rem 1.1rem;margin-bottom:.6rem;transition:all .2s;cursor:pointer;}}
.vf-wf-card:hover{{border-color:{t['accent']};box-shadow:0 0 16px {t['glow']};}}
.vf-wf-card.critical{{border-color:{t['red']}44;background:{t['red']}05;}}
.vf-wf-card.high{{border-color:{t['amber']}44;background:{t['amber']}05;}}
.vf-wf-row{{display:flex;justify-content:space-between;align-items:center;
  font-size:.72rem;margin-bottom:.3rem;}}

/* ── REFRESH BTN SPECIAL ── */
.vf-refresh-btn{{background:{t['grad']}!important;color:#fff!important;
  border:none!important;border-radius:10px!important;font-weight:700!important;
  padding:.5rem 1.2rem!important;font-size:.78rem!important;cursor:pointer;}}

/* ── STATUS ROW ── */
.vf-status-row{{display:flex;align-items:center;gap:.5rem;
  padding:.4rem .8rem;border-radius:8px;margin-bottom:.35rem;
  border:1px solid {t['border']};background:{t['card']};font-size:.72rem;}}

hr{{border-color:{t['border']}!important;margin:.5rem 0!important;}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

PAGES = [
    ("overview",  "⚡", "Operations Overview"),
    ("workflow",  "🔄", "Workflow Monitor"),
    ("triggers",  "🎯", "Trigger Center"),
    ("alerts",    "🚨", "Alert Center"),
    ("logs",      "🖥️",  "Execution Logs"),
]

def render_sidebar(df):
    t = T()
    if "page" not in st.session_state: st.session_state["page"] = "overview"
    if "filter_owner" not in st.session_state: st.session_state["filter_owner"] = "All"
    if "filter_vendor" not in st.session_state: st.session_state["filter_vendor"] = "All"
    if "filter_criticality" not in st.session_state: st.session_state["filter_criticality"] = "All"
    if "filter_license" not in st.session_state: st.session_state["filter_license"] = "All"
    if "view_mode" not in st.session_state: st.session_state["view_mode"] = "Contract"

    email_state = _load_json(EMAIL_STATE_FILE)
    n180 = sum(1 for f in email_state.values() if f.get("Alert_180")       == "SENT")
    n90  = sum(1 for f in email_state.values() if f.get("Alert_90")        == "SENT")
    n30  = sum(1 for f in email_state.values() if f.get("Alert_30")        == "SENT")
    ncr  = sum(1 for f in email_state.values() if f.get("Alert_Critical")  == "SENT")
    nhu  = sum(1 for f in email_state.values() if f.get("Alert_High_Util") == "SENT")
    nlu  = sum(1 for f in email_state.values() if f.get("Alert_Low_Util")  == "SENT")

    n_crit_csv = int((df["Days_to_Renewal"] <= 30).sum()) if not df.empty and "Days_to_Renewal" in df.columns else 0

    st.markdown(f"""
<div class='vf-brand'>
  <div style='display:flex;align-items:center;gap:6px;margin-bottom:3px'>
    <span style='font-size:1.1rem'>⚡</span>
    <span class='vf-brand-name'>VendorFlow AI</span>
  </div>
  <div class='vf-brand-sub'><span class='vf-pulse'></span>CRA · Live System</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div class='vf-nav-label'>Navigation</div>", unsafe_allow_html=True)
    for pid, icon, label in PAGES:
        if st.button(f"{icon}  {label}", key=f"nav_{pid}", width='stretch'):
            st.session_state["page"] = pid
            st.rerun()

    st.markdown("<div class='vf-nav-label' style='margin-top:.5rem;border-top:1px solid #1C2640;padding-top:.8rem'>Live Signals</div>",
                unsafe_allow_html=True)
    sigs = [
        ("180-Day Planning",   n180, "#3B82F6"),
        ("90-Day Escalation",  n90,  "#F59E0B"),
        ("30-Day Critical",    n30,  "#EF4444"),
        ("7-Day Expiring",     ncr,  "#8B5CF6"),
        ("High Utilization",   nhu,  "#F97316"),
        ("Low Utilization",    nlu,  "#06B6D4"),
    ]
    for lbl, cnt, clr in sigs:
        st.markdown(
            f"<div class='vf-sig-row'><span>{lbl}</span>"
            f"<span class='vf-sig-badge' style='background:{clr}'>{cnt}</span></div>",
            unsafe_allow_html=True)

    # Enterprise Filters
    st.markdown("<div class='vf-nav-label' style='margin-top:.5rem;border-top:1px solid #1C2640;padding-top:.8rem'>Filters</div>",
                unsafe_allow_html=True)
    
    # Owner filter
    if not df.empty and "Pending_With" in df.columns:
        owners = ["All"] + sorted(df["Pending_With"].dropna().unique().tolist())
        st.session_state["filter_owner"] = st.selectbox("Owner", owners, key="filter_owner_sb")
    
    # Vendor filter
    if not df.empty and "Vendor" in df.columns:
        vendors = ["All"] + sorted(df["Vendor"].dropna().unique().tolist())
        st.session_state["filter_vendor"] = st.selectbox("Vendor", vendors, key="filter_vendor_sb")
    
    # Criticality filter
    if not df.empty and "Days_to_Renewal" in df.columns:
        criticality = ["All", "Critical (≤7d)", "Urgent (≤30d)", "Normal (>30d)"]
        st.session_state["filter_criticality"] = st.selectbox("Criticality", criticality, key="filter_crit_sb")
    
    # License filter
    if not df.empty and "License_Type" in df.columns:
        licenses = ["All"] + sorted(df["License_Type"].dropna().unique().tolist())
        st.session_state["filter_license"] = st.selectbox("License Type", licenses, key="filter_license_sb")
    
    # View mode toggle
    st.markdown("<div class='vf-nav-label' style='margin-top:.5rem'>View Mode</div>", unsafe_allow_html=True)
    view_mode = st.radio("", ["Contract", "Vendor"], key="view_mode_rb", horizontal=True)
    st.session_state["view_mode"] = view_mode
    
    # Chart Items slider
    st.markdown("<div class='vf-nav-label' style='margin-top:.5rem'>Chart Items</div>", unsafe_allow_html=True)
    chart_items = st.slider("Items to Show", 5, 50, 20, key="chart_items_slider")
    st.session_state["chart_items"] = chart_items

    # Summary Report Button
    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
    if st.button("📊 View Summary Report", key="summary_report_btn", width='stretch'):
        st.session_state["show_summary"] = True
        st.rerun()

    st.markdown("<div style='flex:1;min-height:1rem'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════════

TITLES = {
    "overview":  ("⚡ Operations Overview",    "Mission control · Live workflows · KPIs"),
    "workflow":  ("🔄 Workflow Monitor",        "Node-level stage tracking · Execution state"),
    "triggers":  ("🎯 Trigger Center",          "All 6 trigger types · Controlled execution"),
    "alerts":    ("🚨 Alert Center",            "Critical contracts · Escalations · Util alerts"),
    "logs":      ("🖥️  Execution Logs",          "Audit trail · Email nodes · Agent activity"),
}

def render_topbar(pid, df):
    t = T()
    title, sub = TITLES.get(pid, ("Dashboard", ""))
    n_crit = int((df["Days_to_Renewal"] <= 30).sum()) if not df.empty and "Days_to_Renewal" in df.columns else 0
    alert_html = (f"<span class='vf-badge vf-badge-red' style='animation:vf-pulse 2s infinite'>"
                  f"🔴 {n_crit} Critical</span>") if n_crit else ""
    now = datetime.now().strftime("%H:%M")
    st.markdown(f"""
<div class='vf-topbar'>
  <div><div class='vf-topbar-title'>{title}</div><div class='vf-topbar-sub'>{sub}</div></div>
  <div style='display:flex;align-items:center;gap:10px'>
    {alert_html}
    <span class='vf-badge vf-badge-green'>{dot('green')} Online</span>
    <span style='font-size:.66rem;color:{t["muted"]}'>🕐 {now}</span>
  </div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# REFRESH PANEL (shown on every page)
# ══════════════════════════════════════════════════════════════════════════════

def render_refresh_panel():
    t = T()
    email_state  = _load_json(EMAIL_STATE_FILE)
    total_sent   = sum(
        1 for f in email_state.values()
        for k in ["Alert_180","Alert_90","Alert_30","Alert_Critical","Alert_High_Util","Alert_Low_Util"]
        if f.get(k) == "SENT"
    )

    st.markdown(f"""
<div style='background:{t["card"]};border:1px solid {t["border"]};border-radius:12px;
  padding:.8rem 1.2rem;margin-bottom:.8rem;display:flex;align-items:center;
  justify-content:space-between;gap:1rem;'>
  <div style='display:flex;align-items:center;gap:12px;'>
    <div>
      <div style='font-size:.65rem;color:{t["muted"]};font-weight:700;text-transform:uppercase;letter-spacing:.07em'>
        Controlled Execution
      </div>
      <div style='font-size:.8rem;font-weight:600;color:{t["text"]};margin-top:2px'>
        {dot("green")} {total_sent} triggers fired &nbsp;·&nbsp;
        Refresh fires 3 at a time to avoid Gmail limits
      </div>
    </div>
  </div>
  <div style='display:flex;align-items:center;gap:.5rem;font-size:.7rem;color:{t["muted"]}'>
    Each refresh = 3 new triggers max
  </div>
</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([1,4], gap="small")
    with col1:
        if st.button("🔄 Refresh (3)", key="refresh_3", width='stretch'):
            _run_refresh(3)
    with col2:
        st.markdown("<div class='vf-note'>Controlled batch refresh: up to 3 triggers only.</div>", unsafe_allow_html=True)


def _run_refresh(batch: int):
    try:
        resp = requests.post(f"{BACKEND_URL}/refresh?batch_size={batch}", timeout=10)
        data = resp.json()
        fired = data.get("fired", {})
        if fired:
            total = sum(fired.values())
            st.toast(f"✅ Refresh complete — {total} triggers fired", icon="⚡")
        else:
            st.toast("✅ No new triggers — all dispatched", icon="✓")
        # Force reload JSON states
        st.session_state["_force_reload"] = True
        time.sleep(0.5)
        st.rerun()
    except Exception:
        # Fallback: run locally
        try:
            from email_service import process as email_process
            fired = email_process(batch_size=batch)
            if fired:
                st.toast(f"✅ {sum(fired.values())} triggers fired", icon="⚡")
            else:
                st.toast("✅ No new triggers", icon="✓")
            # Force reload JSON states
            st.session_state["_force_reload"] = True
            st.rerun()
        except Exception as e:
            st.error(f"Refresh error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OPERATIONS OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def page_overview(df):
    t = T()
    agent_state = _load_json(STATE_FILE)
    trigger_log = _load_json(TRIGGER_LOG_FILE)
    email_state = _load_json(EMAIL_STATE_FILE)
    filtered_df = _apply_filters(df)
    filter_active = _filters_active()
    filtered_ids = set(filtered_df["Contract_ID"].astype(str).tolist()) if not filtered_df.empty else set()

    # Summary Report Modal
    if st.session_state.get("show_summary", False):
        st.markdown(f"""
<div class='vf-hero'>
  <div class='vf-hero-title'>📊 Executive Summary Report</div>
  <div class='vf-hero-sub'>VendorFlow AI Contract Renewal Agent · Generated {datetime.now().strftime("%d %b %Y %H:%M")}</div>
</div>""", unsafe_allow_html=True)
        
        # Summary metrics
        n_fired = sum(1 for cid, f in email_state.items() if cid in filtered_ids
                      for k in ["Alert_180","Alert_90","Alert_30","Alert_Critical","Alert_High_Util","Alert_Low_Util"]
                      if f.get(k) == "SENT")
        n_crit   = int((filtered_df["Days_to_Renewal"] <= 7).sum()) if not filtered_df.empty else 0
        n_urgent = int(((filtered_df["Days_to_Renewal"] > 7) & (filtered_df["Days_to_Renewal"] <= 30)).sum()) if not filtered_df.empty else 0
        n_high_u = int((filtered_df["Avg_Utilization_Pct"] > 80).sum()) if not filtered_df.empty else 0
        n_low_u  = int((filtered_df["Avg_Utilization_Pct"] < 70).sum()) if not filtered_df.empty else 0
        
        # Workflow stage distribution
        stage_dist = {}
        for cid, info in agent_state.items():
            if filter_active and cid not in filtered_ids:
                continue
            stage = info.get("Stage", "Planning")
            stage_dist[stage] = stage_dist.get(stage, 0) + 1
        
        col1, col2 = st.columns(2, gap="medium")
        
        with col1:
            sec("Trigger Execution Summary", "This Session")
            summary_data = {
                "Total Contracts": len(filtered_df) if not filtered_df.empty else 0,
                "Active Workflows": sum(1 for cid in agent_state if not filtered_ids or cid in filtered_ids),
                "Triggers Fired": n_fired,
                "Critical Contracts": n_crit,
                "Urgent Contracts": n_urgent,
                "High Utilization": n_high_u,
                "Low Utilization": n_low_u,
            }
            for k, v in summary_data.items():
                st.markdown(
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>{k}</span>"
                    f"<span style='margin-left:auto;font-weight:700'>{v}</span>"
                    f"</div>", unsafe_allow_html=True)
        
        with col2:
            sec("Workflow Stage Distribution", "Current State")
            for stage in ["Planning", "Budgeting", "Approval", "Execution", "Closed"]:
                count = stage_dist.get(stage, 0)
                pct = (count / len(agent_state) * 100) if agent_state else 0
                color = t["accent"] if stage == "Planning" else t["amber"] if stage == "Budgeting" else t["purple"] if stage == "Approval" else t["green"] if stage == "Execution" else t["muted"]
                st.markdown(
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>{stage}</span>"
                    f"<span style='margin-left:auto;font-weight:700'>{count} ({pct:.0f}%)</span>"
                    f"</div>", unsafe_allow_html=True)
                st.markdown(bar(pct, color), unsafe_allow_html=True)
        
        # Trigger breakdown
        sec("Trigger Type Breakdown", "Detailed")
        trigger_breakdown = {
            "180-Day Planning": sum(1 for cid, f in email_state.items() if cid in filtered_ids and f.get("Alert_180") == "SENT"),
            "90-Day Escalation": sum(1 for cid, f in email_state.items() if cid in filtered_ids and f.get("Alert_90") == "SENT"),
            "30-Day Critical": sum(1 for cid, f in email_state.items() if cid in filtered_ids and f.get("Alert_30") == "SENT"),
            "7-Day Expiring": sum(1 for cid, f in email_state.items() if cid in filtered_ids and f.get("Alert_Critical") == "SENT"),
            "High Utilization": sum(1 for cid, f in email_state.items() if cid in filtered_ids and f.get("Alert_High_Util") == "SENT"),
            "Low Utilization": sum(1 for cid, f in email_state.items() if cid in filtered_ids and f.get("Alert_Low_Util") == "SENT"),
        }
        trigger_df = pd.DataFrame([
            {"Trigger Type": k, "Fired": v, "Status": "✅ Active" if v > 0 else "⏳ Pending"}
            for k, v in trigger_breakdown.items()
        ])
        st.dataframe(trigger_df, width='stretch', height=250)
        
        if st.button("Close Summary", key="close_summary_btn"):
            st.session_state["show_summary"] = False
            st.rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        return

    # Toast for new critical alerts
    prev = st.session_state.get("_prev_es", {})
    for cid, flags in email_state.items():
        if filter_active and cid not in filtered_ids:
            continue
        for ak in ["Alert_30", "Alert_Critical"]:
            if flags.get(ak) == "SENT" and prev.get(cid, {}).get(ak) != "SENT":
                tdata  = trigger_log.get(cid, {}).get(ak, {})
                v      = tdata.get("vendor", cid) if isinstance(tdata, dict) else cid
                st.toast(f"🚨 Critical trigger → {v} ({cid})", icon="⚡")
    st.session_state["_prev_es"] = email_state

    # Hero
    n_fired = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids)
                  for k in ["Alert_180","Alert_90","Alert_30","Alert_Critical","Alert_High_Util","Alert_Low_Util"]
                  if f.get(k) == "SENT")
    n_crit   = int((filtered_df["Days_to_Renewal"] <= 7).sum()) if not filtered_df.empty else 0
    n_urgent = int(((filtered_df["Days_to_Renewal"] > 7) & (filtered_df["Days_to_Renewal"] <= 30)).sum()) if not filtered_df.empty else 0
    n_high_u = int((filtered_df["Avg_Utilization_Pct"] > 80).sum()) if not filtered_df.empty else 0
    n_low_u  = int((filtered_df["Avg_Utilization_Pct"] < 70).sum()) if not filtered_df.empty else 0

    st.markdown(f"""
<div class='vf-hero'>
  <div style='display:flex;align-items:center;gap:10px;margin-bottom:.5rem'>
    <span style='font-size:1.6rem'>⚡</span>
    <div>
      <div class='vf-hero-title'>VendorFlow AI — Operations Center</div>
      <div class='vf-hero-sub'>Contract Renewal Agent · All systems operational · {datetime.now().strftime("%d %b %Y")}</div>
    </div>
    <div style='margin-left:auto'>{badge("Live","green")}&nbsp;{badge(f"{len(df)} contracts","blue")}</div>
  </div>
</div>""", unsafe_allow_html=True)

    render_refresh_panel()

    # KPIs
    c1,c2,c3,c4,c5,c6 = st.columns(6, gap="small")
    c1.metric("Active Workflows",  sum(1 for cid in agent_state if not filtered_ids or cid in filtered_ids), delta="Running")
    c2.metric("Triggers Fired",    n_fired,           delta="This session")
    c3.metric("Expiring <7d",      n_crit,            delta="Immediate")
    c4.metric("Urgent 30d",        n_urgent,          delta="Exec alerted")
    c5.metric("High Utilization",  n_high_u,          delta=">80%")
    c6.metric("Low Utilization",   n_low_u,           delta="<70%")

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    # Trigger window summary
    sec("Active Trigger Windows", "Live")
    n180 = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_180")       == "SENT")
    n90  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_90")        == "SENT")
    n30  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_30")        == "SENT")
    ncr  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_Critical")  == "SENT")
    nhu  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_High_Util") == "SENT")
    nlu  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_Low_Util")  == "SENT")

    t1,t2,t3,t4,t5,t6 = st.columns(6, gap="small")
    for col, num, lbl, cls, sub in [
        (t1, n180, "180-Day Planning",   "vf-tc-blue",   "Procurement notified"),
        (t2, n90,  "90-Day Escalation",  "vf-tc-amber",  "Finance escalated"),
        (t3, n30,  "30-Day Exec Alert",  "vf-tc-red",    "Executive alerted"),
        (t4, ncr,  "Critical <7 Days",   "vf-tc-purple", "Immediate action"),
        (t5, nhu,  "High Util Risk",     "vf-tc-orange", ">80% capacity"),
        (t6, nlu,  "Low Util Alert",     "vf-tc-green",  "<70% usage"),
    ]:
        with col:
            st.markdown(
                f"<div class='vf-tc {cls}'>"
                f"<div class='vf-tc-num'>{num}</div>"
                f"<div class='vf-tc-lbl'>{lbl}</div>"
                f"<div class='vf-tc-sub'>{sub}</div>"
                f"</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # Enterprise Charts
    sec("Enterprise Operational Charts", "Live Analytics")
    
    # Apply filters
    filtered_df = df.copy()
    if st.session_state.get("filter_vendor", "All") != "All" and not df.empty:
        filtered_df = filtered_df[filtered_df["Vendor"] == st.session_state["filter_vendor"]]
    if st.session_state.get("filter_criticality", "All") != "All" and not df.empty:
        crit = st.session_state["filter_criticality"]
        if crit == "Critical (≤7d)":
            filtered_df = filtered_df[filtered_df["Days_to_Renewal"] <= 7]
        elif crit == "Urgent (≤30d)":
            filtered_df = filtered_df[filtered_df["Days_to_Renewal"] <= 30]
        elif crit == "Normal (>30d)":
            filtered_df = filtered_df[filtered_df["Days_to_Renewal"] > 30]
    if st.session_state.get("filter_license", "All") != "All" and not df.empty:
        filtered_df = filtered_df[filtered_df["License_Type"] == st.session_state["filter_license"]]
    
    chart_items = st.session_state.get("chart_items", 20)
    
    # Row 1: Trigger Distribution & Workflow Progress
    c1, c2 = st.columns(2, gap="medium")
    
    with c1:
        st.markdown(f"<div style='font-size:.78rem;font-weight:700;color:{t['text']};margin-bottom:.5rem'>📊 Trigger Distribution</div>", unsafe_allow_html=True)
        trigger_counts = {
            "180-Day": n180,
            "90-Day": n90,
            "30-Day": n30,
            "7-Day": ncr,
            "High Util": nhu,
            "Low Util": nlu,
        }
        if any(trigger_counts.values()):
            import plotly.express as px
            fig = px.pie(
                values=list(trigger_counts.values()),
                names=list(trigger_counts.keys()),
                hole=0.4,
                color_discrete_sequence=["#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6", "#F97316", "#06B6D4"]
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                height=250,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trigger data available")
    
    with c2:
        st.markdown(f"<div style='font-size:.78rem;font-weight:700;color:{t['text']};margin-bottom:.5rem'>🔄 Workflow Stage Distribution</div>", unsafe_allow_html=True)
        stage_dist = {}
        for info in agent_state.values():
            stage = info.get("Stage", "Planning")
            stage_dist[stage] = stage_dist.get(stage, 0) + 1
        if stage_dist:
            import plotly.express as px
            fig = px.bar(
                x=list(stage_dist.keys()),
                y=list(stage_dist.values()),
                color=list(stage_dist.keys()),
                color_discrete_map={
                    "Planning": "#3B82F6",
                    "Budgeting": "#F59E0B",
                    "Approval": "#8B5CF6",
                    "Execution": "#10B981",
                    "Closed": "#6B7280"
                }
            )
            fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                height=250,
                xaxis_title="",
                yaxis_title="Count",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No workflow data available")
    
    # Row 2: Renewal Timeline & Vendor Risk
    c3, c4 = st.columns(2, gap="medium")
    
    with c3:
        st.markdown(f"<div style='font-size:.78rem;font-weight:700;color:{t['text']};margin-bottom:.5rem'>📅 Renewal Timeline</div>", unsafe_allow_html=True)
        if not filtered_df.empty:
            timeline_df = filtered_df.nsmallest(chart_items, "Days_to_Renewal")[["Contract_ID", "Vendor", "Days_to_Renewal"]].copy()
            timeline_df["Renewal Date"] = (datetime.now() + pd.to_timedelta(timeline_df["Days_to_Renewal"], unit='D')).dt.strftime("%d %b %Y")
            st.dataframe(timeline_df, width='stretch', height=200)
        else:
            st.info("No contracts match current filters")
    
    with c4:
        st.markdown(f"<div style='font-size:.78rem;font-weight:700;color:{t['text']};margin-bottom:.5rem'>⚠️ Vendor Risk Overview</div>", unsafe_allow_html=True)
        if not filtered_df.empty:
            risk_df = filtered_df.copy()
            risk_df["Risk Score"] = (
                (risk_df["Days_to_Renewal"] <= 7).astype(int) * 3 +
                (risk_df["Days_to_Renewal"] <= 30).astype(int) * 2 +
                (risk_df["Avg_Utilization_Pct"] > 80).astype(int) * 2 +
                (risk_df["Avg_Utilization_Pct"] < 70).astype(int) * 1
            )
            risk_df = risk_df.nlargest(chart_items, "Risk Score")[["Contract_ID", "Vendor", "Days_to_Renewal", "Avg_Utilization_Pct", "Risk Score"]]
            st.dataframe(risk_df, width='stretch', height=200)
        else:
            st.info("No contracts match current filters")
    
    # Row 3: Trigger Execution Trend
    st.markdown(f"<div style='font-size:.78rem;font-weight:700;color:{t['text']};margin-bottom:.5rem'>📈 Trigger Execution Trend</div>", unsafe_allow_html=True)
    # Calculate execution trend from trigger log
    execution_trend = {}
    for cid, tdata in trigger_log.items():
        for ak in ["Alert_Critical","Alert_30","Alert_High_Util","Alert_90","Alert_Low_Util","Alert_180"]:
            info = tdata.get(ak)
            if isinstance(info, dict) and "ts" in info:
                try:
                    ts = info["ts"][:10]  # Get date part
                    execution_trend[ts] = execution_trend.get(ts, 0) + 1
                except:
                    pass
    if execution_trend:
        import plotly.express as px
        trend_df = pd.DataFrame([
            {"Date": k, "Triggers": v}
            for k, v in sorted(execution_trend.items())
        ])
        fig = px.line(trend_df, x="Date", y="Triggers", markers=True)
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            height=200,
            xaxis_title="",
            yaxis_title="Triggers Fired"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No execution trend data available")

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3,2], gap="medium")

    with col_l:
        sec("Live Workflow State", "Agent Running")
        rows = []
        for cid, info in agent_state.items():
            stage  = info.get("Stage", "Planning")
            owner  = info.get("Pending_With", "—")
            sent   = "✅ Sent" if info.get("Email_Sent") else "⏳ Pending"
            status = info.get("Execution_Status", "Running")
            row_csv = df[df["Contract_ID"] == cid] if not df.empty else pd.DataFrame()
            vendor  = row_csv.iloc[0]["Vendor"] if not row_csv.empty else "—"
            try: 
                days = int(row_csv.iloc[0]["Days_to_Renewal"])
                license_type = str(row_csv.iloc[0].get("License_Type", "Full"))
            except: 
                days = 999
                license_type = "Full"
            
            # Apply sidebar filters
            if st.session_state.get("filter_owner", "All") != "All" and owner != st.session_state["filter_owner"]:
                continue
            if st.session_state.get("filter_vendor", "All") != "All" and vendor != st.session_state["filter_vendor"]:
                continue
            if st.session_state.get("filter_criticality", "All") != "All":
                crit = st.session_state["filter_criticality"]
                if crit == "Critical (≤7d)" and days > 7:
                    continue
                elif crit == "Urgent (≤30d)" and days > 30:
                    continue
                elif crit == "Normal (>30d)" and days <= 30:
                    continue
            if st.session_state.get("filter_license", "All") != "All" and license_type != st.session_state["filter_license"]:
                continue
            
            rows.append({"Contract": cid, "Vendor": vendor, "Days": days,
                         "Stage": stage, "Pending With": owner, "Email": sent, "Status": status})
        if rows:
            wf_df = pd.DataFrame(rows).sort_values("Days")
            st.dataframe(wf_df, width='stretch', height=290)
        else:
            st.info("No active workflows match current filters. Adjust filters or click Refresh.")

    with col_r:
        sec("Live Activity Feed", "Recent Events")
        feed_items = []
        for cid, tdata in trigger_log.items():
            if filter_active and cid not in filtered_ids:
                continue
            for ak in ["Alert_Critical","Alert_30","Alert_High_Util","Alert_90","Alert_Low_Util","Alert_180"]:
                info = tdata.get(ak)
                if isinstance(info, dict):
                    status = info.get("status", "")
                    if status in ["Running", "Completed", "Failed"]:
                        status_icon = "🔄" if status == "Running" else "✅" if status == "Completed" else "❌"
                        feed_items.append({
                            "ts":  info.get("ts", ""),
                            "msg": f"{status_icon} {tdata.get('trigger_type','Trigger')} → {info.get('vendor',cid)} ({cid})",
                            "col": ("red"    if "Critical" in ak or "30" in ak else
                                    "amber"  if "90" in ak else
                                    "orange" if "High" in ak else
                                    "purple" if "Low" in ak else "blue"),
                        })
        feed_items.sort(key=lambda x: x["ts"], reverse=True)
        if feed_items:
            html = ""
            for fi in feed_items[:15]:
                dc = {"red":t["red"],"amber":t["amber"],"orange":t["orange"],
                      "purple":t["purple"],"blue":t["accent"]}.get(fi["col"], t["accent"])
                html += (f"<div class='vf-feed-item'>"
                         f"<div class='vf-dot' style='background:{dc};box-shadow:0 0 5px {dc};margin-top:3px'></div>"
                         f"<div style='flex:1;font-size:.71rem'>{fi['msg']}</div>"
                         f"<div class='vf-feed-ts'>{_ago(fi['ts'])}</div></div>")
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("No activity yet — click Refresh to start execution")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — WORKFLOW MONITOR (Node-level visibility)
# ══════════════════════════════════════════════════════════════════════════════

def page_workflow(df):
    t = T()
    agent_state = _load_json(STATE_FILE)
    email_state = _load_json(EMAIL_STATE_FILE)
    trigger_log = _load_json(TRIGGER_LOG_FILE)
    filtered_df = _apply_filters(df)
    filter_active = _filters_active()
    filtered_ids = set(filtered_df["Contract_ID"].astype(str).tolist()) if not filtered_df.empty else set()

    st.markdown(f"""
<div class='vf-hero'>
  <div class='vf-hero-title'>🔄 Workflow Monitor — Node-Level Execution Tracking</div>
  <div class='vf-hero-sub'>Live stage visibility for every active contract · Click any contract to expand</div>
</div>""", unsafe_allow_html=True)

    render_refresh_panel()

    # Stage counts
    stage_cnt = {s: 0 for s in STAGE_ORDER}
    for cid, info in agent_state.items():
        if filter_active and cid not in filtered_ids:
            continue
        s = info.get("Stage", "Planning")
        if s in stage_cnt:
            stage_cnt[s] += 1

    sec("5-Stage CRA Lifecycle Pipeline", "Workflow")
    pipe = "<div class='vf-pipe'>"
    for i, stage in enumerate(STAGE_ORDER):
        cnt = stage_cnt.get(stage, 0)
        cls = "active" if cnt > 0 else ""
        pipe += (
            f"<div class='vf-stage {cls}'>"
            f"<div class='vf-stage-num'>{i+1}</div>"
            f"<div style='font-weight:600'>{stage}</div>"
            f"<div style='font-size:.6rem;margin-top:2px;opacity:.8'>{cnt} active</div>"
            f"</div>"
        )
        if i < len(STAGE_ORDER) - 1:
            pipe += "<div class='vf-arrow'>→</div>"
    pipe += "</div>"
    st.markdown(pipe, unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5, gap="small")
    for col, stage in zip([c1,c2,c3,c4,c5], STAGE_ORDER):
        col.metric(stage, stage_cnt.get(stage, 0))

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # Contract-level node view
    sec("Contract Workflow Nodes", "Live State")

    if not agent_state:
        st.info("No active workflows. Click Refresh to populate.")
        return

    # Filter
    filter_stage = st.selectbox("Filter by Stage", ["All"] + STAGE_ORDER, key="wf_filter")

    for cid, info in agent_state.items():
        if filter_active and cid not in filtered_ids:
            continue
        stage         = info.get("Stage", "Planning")
        previous_stage = info.get("Previous_Stage", "—")
        pending_with  = info.get("Pending_With", "—")
        email_sent    = info.get("Email_Sent", False)
        exec_status   = info.get("Execution_Status", "Running")
        escalated     = info.get("Escalated", False)
        stage_history = info.get("Stage_History", [])
        last_trigger  = info.get("Last_Trigger", "—")
        last_trigger_ts = info.get("Last_Trigger_Timestamp", "—")

        if filter_stage != "All" and stage != filter_stage:
            continue

        row_csv = df[df["Contract_ID"] == cid] if not df.empty else pd.DataFrame()
        vendor  = row_csv.iloc[0]["Vendor"] if not row_csv.empty else "—"
        try:
            days     = int(row_csv.iloc[0]["Days_to_Renewal"])
            util_pct = float(row_csv.iloc[0]["Avg_Utilization_Pct"])
        except:
            days, util_pct = 999, 0

        # Severity
        if days <= 7:   sev_cls, sev_lbl = "critical", "Critical"
        elif days <= 30: sev_cls, sev_lbl = "high", "Urgent"
        else:            sev_cls, sev_lbl = "", ""

        cur_stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

        with st.expander(f"📋 {cid} — {vendor}  |  Stage: {stage}  |  {days}d left", expanded=(days <= 30)):

            # Workflow node pipeline for THIS contract
            node_html = "<div class='vf-pipe' style='margin:0 0 .8rem'>"
            for i, s in enumerate(STAGE_ORDER):
                if i < cur_stage_idx:
                    cls = "done"
                elif i == cur_stage_idx:
                    cls = "active"
                else:
                    cls = ""
                node_html += (
                    f"<div class='vf-stage {cls}'>"
                    f"<div class='vf-stage-num'>{'✓' if i < cur_stage_idx else i+1}</div>"
                    f"<div style='font-weight:600;font-size:.62rem'>{s}</div>"
                    f"</div>"
                )
                if i < len(STAGE_ORDER) - 1:
                    node_html += "<div class='vf-arrow' style='font-size:.6rem'>→</div>"
            node_html += "</div>"
            st.markdown(node_html, unsafe_allow_html=True)

            # Status details
            col_a, col_b, col_c = st.columns(3, gap="small")
            with col_a:
                st.markdown(
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Current Stage</span>"
                    f"<span style='margin-left:auto'>{badge(stage,'blue')}</span>"
                    f"</div>"
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Previous Stage</span>"
                    f"<span style='margin-left:auto;font-size:.7rem'>{previous_stage if previous_stage != '—' else '—'}</span>"
                    f"</div>"
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Pending With</span>"
                    f"<span style='margin-left:auto;font-size:.7rem'>{pending_with}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_b:
                email_badge = badge("✅ Email Sent","green") if email_sent else badge("⏳ Pending","amber")
                esc_badge   = badge("⚠️ Escalated","red") if escalated else badge("Normal","gray")
                exec_badge  = badge(exec_status,"green") if exec_status == "Completed" else badge(exec_status,"amber") if exec_status == "Running" else badge(exec_status,"red")
                st.markdown(
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Email Status</span>"
                    f"<span style='margin-left:auto'>{email_badge}</span>"
                    f"</div>"
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Execution Status</span>"
                    f"<span style='margin-left:auto'>{exec_badge}</span>"
                    f"</div>"
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Escalation</span>"
                    f"<span style='margin-left:auto'>{esc_badge}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_c:
                days_color = t["red"] if days <= 30 else t["amber"] if days <= 90 else t["green"]
                util_color = t["red"] if util_pct > 80 else t["purple"] if util_pct < 70 else t["green"]
                st.markdown(
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Days Left</span>"
                    f"<span style='margin-left:auto;color:{days_color};font-weight:700'>{days}d</span>"
                    f"</div>"
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Utilization</span>"
                    f"<span style='margin-left:auto;color:{util_color};font-weight:700'>{util_pct:.1f}%</span>"
                    f"</div>"
                    f"<div class='vf-status-row'>"
                    f"<span style='color:{t['muted']};font-weight:600'>Last Trigger</span>"
                    f"<span style='margin-left:auto;font-size:.65rem'>{last_trigger}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # Completed stages / Stage History
            if stage_history and len(stage_history) > 0:
                green_color = t["green"]
                accent_color = t["accent"]
                muted_color = t["muted"]
                
                # Handle both old format (list of strings) and new format (list of dicts)
                if stage_history and isinstance(stage_history[0], dict):
                    # New format: list of dicts with 'from', 'to', 'trigger', 'timestamp'
                    hist_parts = []
                    for h in stage_history:
                        from_stage = h.get("from", "—")
                        to_stage = h.get("to", "—")
                        trigger = h.get("trigger", "—")
                        hist_parts.append(f"{from_stage} → {to_stage} ({trigger})")
                    hist_html = " → ".join(
                        f"<span style='color:{green_color}'>{p}</span>" for p in hist_parts[:-1]
                    )
                    if hist_parts:
                        hist_html += f" → <span style='color:{accent_color};font-weight:700'>{hist_parts[-1]} (current)</span>"
                else:
                    # Old format: list of strings
                    hist_html = " → ".join(
                        f"<span style='color:{green_color}'>{s}</span>" for s in stage_history[:-1]
                    )
                    if stage_history:
                        hist_html += f" → <span style='color:{accent_color};font-weight:700'>{stage_history[-1]} (current)</span>"
                
                st.markdown(
                    f"<div style='font-size:.68rem;color:{muted_color};margin-top:.3rem'>"
                    f"Stage History: {hist_html}</div>",
                    unsafe_allow_html=True
                )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — TRIGGER CENTER
# ══════════════════════════════════════════════════════════════════════════════

def page_triggers(df):
    t = T()
    email_state = _load_json(EMAIL_STATE_FILE)
    trigger_log = _load_json(TRIGGER_LOG_FILE)
    filtered_df = _apply_filters(df)
    filter_active = _filters_active()
    filtered_ids = set(filtered_df["Contract_ID"].astype(str).tolist()) if not filtered_df.empty else set()

    st.markdown(f"""
<div class='vf-hero'>
  <div class='vf-hero-title'>🎯 Trigger Center — Execution Command</div>
  <div class='vf-hero-sub'>All 6 trigger types · Controlled batch execution · Live firing status</div>
</div>""", unsafe_allow_html=True)

    render_refresh_panel()

    # Counts with execution states
    n180 = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_180")       == "SENT")
    n90  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_90")        == "SENT")
    n30  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_30")        == "SENT")
    ncr  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_Critical")  == "SENT")
    nhu  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_High_Util") == "SENT")
    nlu  = sum(1 for cid, f in email_state.items() if (not filter_active or cid in filtered_ids) and f.get("Alert_Low_Util")  == "SENT")
    
    # Execution state counts
    exec_states = {"Running": 0, "Completed": 0, "Failed": 0}
    for cid, tdata in trigger_log.items():
        if filter_active and cid not in filtered_ids:
            continue
        for ak in ["Alert_Critical","Alert_30","Alert_High_Util","Alert_90","Alert_Low_Util","Alert_180"]:
            info = tdata.get(ak)
            if isinstance(info, dict):
                status = info.get("status", "")
                if status in exec_states:
                    exec_states[status] += 1

    # Pending from CSV
    n180_pending = n90_pending = n30_pending = ncr_pending = 0
    nhu_pending  = nlu_pending = 0
    if not filtered_df.empty:
        n180_pending = int(((filtered_df["Days_to_Renewal"] >  90) & (filtered_df["Days_to_Renewal"] <= 180)).sum()) - n180
        n90_pending  = int(((filtered_df["Days_to_Renewal"] >  30) & (filtered_df["Days_to_Renewal"] <=  90)).sum()) - n90
        n30_pending  = int(((filtered_df["Days_to_Renewal"] >   7) & (filtered_df["Days_to_Renewal"] <=  30)).sum()) - n30
        ncr_pending  = int((filtered_df["Days_to_Renewal"]  <=  7).sum()) - ncr
        nhu_pending  = int((filtered_df["Avg_Utilization_Pct"] > 80).sum()) - nhu
        nlu_pending  = int((filtered_df["Avg_Utilization_Pct"] < 70).sum())  - nlu

    sec("Renewal Trigger Windows", "Time-Based")
    tabs = st.tabs(["📅 180-Day Planning", "📊 90-Day Escalation", "🚨 30-Day Critical", "🔴 7-Day Expiring"])
    win_defs = [
        (tabs[0], "Alert_180", n180, n180_pending,
         (filtered_df["Days_to_Renewal"] >  90) & (filtered_df["Days_to_Renewal"] <= 180) if not filtered_df.empty else None,
         "180d", t["accent"]),
        (tabs[1], "Alert_90",  n90,  n90_pending,
         (filtered_df["Days_to_Renewal"] >  30) & (filtered_df["Days_to_Renewal"] <=  90) if not filtered_df.empty else None,
         "90d",  t["amber"]),
        (tabs[2], "Alert_30",  n30,  n30_pending,
         (filtered_df["Days_to_Renewal"] >   7) & (filtered_df["Days_to_Renewal"] <=  30) if not filtered_df.empty else None,
         "30d",  t["red"]),
        (tabs[3], "Alert_Critical", ncr, ncr_pending,
         filtered_df["Days_to_Renewal"] <=  7 if not filtered_df.empty else None,
         "7d",   t["purple"]),
    ]

    for tab, alert_key, n_sent, n_pend, mask, win, color in win_defs:
        with tab:
            c1, c2, c3 = st.columns(3, gap="small")
            c1.metric("Triggers Fired",   n_sent,                    delta="SENT")
            c2.metric("Pending",          max(0, n_pend),            delta="Awaiting refresh")
            total_window = n_sent + max(0, n_pend)
            pct_done = (n_sent / total_window * 100) if total_window > 0 else 0
            c3.metric("Coverage",         f"{pct_done:.0f}%",        delta=f"of {total_window}")

            st.markdown(f"""
<div style='margin:.5rem 0 .8rem'>
  <div style='display:flex;justify-content:space-between;font-size:.7rem;margin-bottom:3px'>
    <span>Execution Progress</span>
    <span style='color:{t["muted"]}'>{n_sent}/{total_window}</span>
  </div>
</div>""", unsafe_allow_html=True)
            st.markdown(bar(pct_done, color), unsafe_allow_html=True)

            if mask is not None and not filtered_df.empty:
                win_df = filtered_df[mask][["Contract_ID","Vendor","License_Type","Days_to_Renewal","Avg_Utilization_Pct","Budget_Status"]].copy()
                # Add execution status from trigger_log
                def get_exec_status(c):
                    tinfo = trigger_log.get(c, {}).get(alert_key, {})
                    if isinstance(tinfo, dict):
                        status = tinfo.get("status", "")
                        if status == "Running": return "🔄 Running"
                        elif status == "Completed": return "✅ SENT"
                        elif status == "Failed": return "❌ Failed"
                    return "⏳ Pending" if email_state.get(c, {}).get(alert_key) != "SENT" else "✅ SENT"
                win_df["Trigger Status"] = win_df["Contract_ID"].apply(get_exec_status)
                win_df = win_df.sort_values("Days_to_Renewal")
                st.dataframe(win_df.head(50), width='stretch', height=260)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # Live Execution States
    sec("Live Trigger Execution States", "Real-time")
    c1, c2, c3 = st.columns(3, gap="small")
    c1.metric("🔄 Running", exec_states["Running"], delta="In progress")
    c2.metric("✅ Completed", exec_states["Completed"], delta="Successfully sent")
    c3.metric("❌ Failed", exec_states["Failed"], delta="Retry required")

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    sec("Enterprise Triggers", "New Triggers")
    col_l, col_r = st.columns(2, gap="medium")

    with col_l:
        st.markdown(f"""
<div class='vf-card'>
  <div class='vf-card-title'>
    <span>🔥 High Utilization & Budget Risk</span>
    {badge("Active","orange")}
  </div>
  <div style='font-size:.72rem;color:{t["muted"]};margin-bottom:.8rem'>
    Fires when utilization > 80% or budget is exceeded.<br>
    Severity: 70–80% Warning · 80–90% High Risk · >90% Critical
  </div>
""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.metric("Fired", nhu)
        c2.metric("Pending", max(0, nhu_pending))

        st.markdown(bar(
            (nhu / (nhu + max(0, nhu_pending)) * 100) if (nhu + max(0, nhu_pending)) > 0 else 0,
            t["orange"]
        ), unsafe_allow_html=True)

        if not filtered_df.empty:
            hu_df = filtered_df[filtered_df["Avg_Utilization_Pct"] > 80][
                ["Contract_ID","Vendor","Avg_Utilization_Pct","Total_Annual_Budget_USD","Budget_Status","Days_to_Renewal"]
            ].copy()
            hu_df["Severity"] = hu_df["Avg_Utilization_Pct"].apply(
                lambda x: "🔴 Critical" if x >= 90 else "🟠 High Risk" if x >= 80 else "🟡 Warning"
            )
            def get_high_util_status(c):
                tinfo = trigger_log.get(c, {}).get("Alert_High_Util", {})
                if isinstance(tinfo, dict):
                    status = tinfo.get("status", "")
                    if status == "Running": return "🔄 Running"
                    elif status == "Completed": return "✅ SENT"
                    elif status == "Failed": return "❌ Failed"
                return "⏳ Pending" if email_state.get(c, {}).get("Alert_High_Util") != "SENT" else "✅ SENT"
            hu_df["Status"] = hu_df["Contract_ID"].apply(get_high_util_status)
            hu_df = hu_df.sort_values("Avg_Utilization_Pct", ascending=False)
            st.dataframe(hu_df.head(20), width='stretch', height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown(f"""
<div class='vf-card'>
  <div class='vf-card-title'>
    <span>📉 Underutilized License</span>
    {badge("Active","cyan")}
  </div>
  <div style='font-size:.72rem;color:{t["muted"]};margin-bottom:.8rem'>
    Fires when utilization < 70% (optimization opportunity).<br>
    Action: Optimization recommendation · Downgrade / removal suggestion
  </div>
""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.metric("Fired", nlu)
        c2.metric("Pending", max(0, nlu_pending))

        st.markdown(bar(
            (nlu / (nlu + max(0, nlu_pending)) * 100) if (nlu + max(0, nlu_pending)) > 0 else 0,
            t["cyan"]
        ), unsafe_allow_html=True)

        if not filtered_df.empty:
            lu_df = filtered_df[filtered_df["Avg_Utilization_Pct"] < 70][
                ["Contract_ID","Vendor","Avg_Utilization_Pct","Total_Annual_Budget_USD","Days_to_Renewal"]
            ].copy()
            lu_df["Recommendation"] = "Downgrade / Remove"
            def get_low_util_status(c):
                tinfo = trigger_log.get(c, {}).get("Alert_Low_Util", {})
                if isinstance(tinfo, dict):
                    status = tinfo.get("status", "")
                    if status == "Running": return "🔄 Running"
                    elif status == "Completed": return "✅ SENT"
                    elif status == "Failed": return "❌ Failed"
                return "⏳ Pending" if email_state.get(c, {}).get("Alert_Low_Util") != "SENT" else "✅ SENT"
            lu_df["Status"] = lu_df["Contract_ID"].apply(get_low_util_status)
            lu_df = lu_df.sort_values("Avg_Utilization_Pct")
            st.dataframe(lu_df.head(20), width='stretch', height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    # Escalation routing matrix
    sec("Trigger → Workflow Routing Matrix")
    routing = pd.DataFrame({
        "Trigger":        ["180-Day Planning","90-Day Escalation","30-Day Critical","7-Day Expiring","High Util Risk","Low Util Alert"],
        "Condition":      ["Days ≤ 180","Days ≤ 90","Days ≤ 30","Days ≤ 7","Util > 80%","Util < 70%"],
        "Routed To":      ["Procurement Team","Finance + Procurement","Executive Approver","All Stakeholders","Finance + Procurement","Procurement Team"],
        "Workflow Stage": ["Planning","Budgeting","Approval","Execution","Capacity Planning","Optimization Review"],
        "Severity":       ["ℹ️ Info","⚠️ Warning","🚨 Urgent","🔴 Critical","🟠 High Risk","🔵 Optimize"],
        "Fired":          [n180, n90, n30, ncr, nhu, nlu],
    })
    st.dataframe(routing, width='stretch', hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ALERT CENTER
# ══════════════════════════════════════════════════════════════════════════════

def page_alerts(df):
    t = T()
    email_state = _load_json(EMAIL_STATE_FILE)
    trigger_log = _load_json(TRIGGER_LOG_FILE)
    filtered_df = _apply_filters(df)
    filtered_ids = set(filtered_df["Contract_ID"].astype(str).tolist()) if not filtered_df.empty else set()

    st.markdown(f"""
<div class='vf-hero' style='background-image:radial-gradient(ellipse at top right,{t["red"]}0C,transparent 60%)'>
  <div class='vf-hero-title'>🚨 Alert Center — Critical Monitoring</div>
  <div class='vf-hero-sub'>Contracts requiring immediate attention · Escalations · Util risk alerts</div>
</div>""", unsafe_allow_html=True)

    render_refresh_panel()

    n_crit   = int((filtered_df["Days_to_Renewal"] <= 7).sum()) if not filtered_df.empty else 0
    n_30     = int(((filtered_df["Days_to_Renewal"] > 7) & (filtered_df["Days_to_Renewal"] <= 30)).sum()) if not filtered_df.empty else 0
    n_high_u = int((filtered_df["Avg_Utilization_Pct"] > 80).sum()) if not filtered_df.empty else 0
    n_low_u  = int((filtered_df["Avg_Utilization_Pct"] < 70).sum()) if not filtered_df.empty else 0
    n_over   = int((filtered_df["Budget_Status"] == "Exceeded").sum()) if not filtered_df.empty else 0

    c1,c2,c3,c4,c5 = st.columns(5, gap="small")
    c1.metric("Expiring <7d",    n_crit,   delta="CRITICAL")
    c2.metric("Urgent 30-Day",   n_30,     delta="Exec alerted")
    c3.metric("High Util >80%",  n_high_u, delta="Budget risk")
    c4.metric("Low Util <70%",   n_low_u,  delta="Optimize now")
    c5.metric("Budget Exceeded", n_over,   delta="Overspend")

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3,2], gap="medium")

    with col_l:
        sec("🔴 Critical Contracts", "≤7 Days")
        if not filtered_df.empty:
            crit_df = filtered_df[filtered_df["Days_to_Renewal"] <= 7][
                ["Contract_ID","Vendor","Days_to_Renewal","Avg_Utilization_Pct","Budget_Status","Stages"]
            ].sort_values("Days_to_Renewal").head(15)
            if not crit_df.empty:
                crit_df["Email Status"] = crit_df["Contract_ID"].apply(
                    lambda c: "✅ SENT" if email_state.get(c, {}).get("Alert_Critical") == "SENT" else "⏳ Pending"
                )
                st.dataframe(crit_df, width='stretch', height=220)
            else:
                st.success("No contracts expiring within 7 days ✅")

        sec("🟠 High Utilization Risk", ">80%")
        if not filtered_df.empty:
            hu_df = filtered_df[filtered_df["Avg_Utilization_Pct"] > 80][
                ["Contract_ID","Vendor","Avg_Utilization_Pct","Total_Annual_Budget_USD","Budget_Status","Days_to_Renewal"]
            ].sort_values("Avg_Utilization_Pct", ascending=False).head(15)
            if not hu_df.empty:
                hu_df["Severity"] = hu_df["Avg_Utilization_Pct"].apply(
                    lambda x: "🔴 Critical" if x >= 90 else "🟠 High Risk"
                )
                hu_df["Alert Status"] = hu_df["Contract_ID"].apply(
                    lambda c: "✅ SENT" if email_state.get(c, {}).get("Alert_High_Util") == "SENT" else "⏳ Pending"
                )
                st.dataframe(hu_df, width='stretch', height=220)
            else:
                st.success("No high utilization contracts ✅")

    with col_r:
        sec("Alert Feed", "Real-time")
        alerts_html = ""
        if not df.empty:
            for _, row in df[df["Days_to_Renewal"] <= 7].head(4).iterrows():
                alerts_html += (
                    f"<div class='vf-alert-card vf-alert-crit'>"
                    f"<div class='vf-alert-title'>🔴 CRITICAL — {row.get('Vendor','?')} ({row['Contract_ID']})</div>"
                    f"<div class='vf-alert-body'>{int(row['Days_to_Renewal'])} days · "
                    f"Stage: {row.get('Stages','?')} · Util: {row.get('Avg_Utilization_Pct',0):.1f}%</div>"
                    f"</div>")
            for _, row in df[(df["Days_to_Renewal"] > 7) & (df["Days_to_Renewal"] <= 30)].head(3).iterrows():
                alerts_html += (
                    f"<div class='vf-alert-card vf-alert-warn'>"
                    f"<div class='vf-alert-title'>🟡 URGENT — {row.get('Vendor','?')} ({row['Contract_ID']})</div>"
                    f"<div class='vf-alert-body'>{int(row['Days_to_Renewal'])} days · Budget: {row.get('Budget_Status','?')}</div>"
                    f"</div>")
            for _, row in df[df["Avg_Utilization_Pct"] > 90].head(3).iterrows():
                sev = "CRITICAL" if row["Avg_Utilization_Pct"] >= 90 else "HIGH RISK"
                alerts_html += (
                    f"<div class='vf-alert-card vf-alert-crit'>"
                    f"<div class='vf-alert-title'>🟠 HIGH UTIL [{sev}] — {row.get('Vendor','?')} ({row['Contract_ID']})</div>"
                    f"<div class='vf-alert-body'>Utilization: {row['Avg_Utilization_Pct']:.1f}% · {int(row['Days_to_Renewal'])}d left</div>"
                    f"</div>")
            for _, row in df[df["Avg_Utilization_Pct"] < 70].head(3).iterrows():
                alerts_html += (
                    f"<div class='vf-alert-card vf-alert-purple'>"
                    f"<div class='vf-alert-title'>📉 LOW UTIL — {row.get('Vendor','?')} ({row['Contract_ID']})</div>"
                    f"<div class='vf-alert-body'>Only {row['Avg_Utilization_Pct']:.1f}% utilized · Recommend downgrade</div>"
                    f"</div>")

        st.markdown(alerts_html if alerts_html else
                    f"<div class='vf-alert-card vf-alert-info'><div class='vf-alert-title'>✅ All Clear</div><div class='vf-alert-body'>No critical alerts. Click Refresh to check.</div></div>",
                    unsafe_allow_html=True)

    sec("📉 Underutilized Licenses", "<70% Usage — Optimization Opportunities")
    if not filtered_df.empty:
        low_df = filtered_df[filtered_df["Avg_Utilization_Pct"] < 70][
            ["Contract_ID","Vendor","Avg_Utilization_Pct","Total_Annual_Budget_USD","Days_to_Renewal","Stages"]
        ].sort_values("Avg_Utilization_Pct").head(25)
        if not low_df.empty:
            low_df["Recommendation"] = "Downgrade / Remove"
            low_df["Alert Status"] = low_df["Contract_ID"].apply(
                lambda c: "✅ SENT" if email_state.get(c, {}).get("Alert_Low_Util") == "SENT" else "⏳ Pending"
            )
            st.dataframe(low_df, width='stretch', height=250)
            st.download_button("⬇ Download Optimization Report",
                low_df.to_csv(index=False).encode(), "low_util.csv", "text/csv")
        else:
            st.success("No underutilized contracts ✅")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — EXECUTION LOGS
# ══════════════════════════════════════════════════════════════════════════════

def page_logs(df):
    t = T()
    agent_state = _load_json(STATE_FILE)
    trigger_log = _load_json(TRIGGER_LOG_FILE)
    email_state = _load_json(EMAIL_STATE_FILE)

    st.markdown(f"""
<div class='vf-hero'>
  <div class='vf-hero-title'>🖥️ Execution Logs — Full Audit Trail</div>
  <div class='vf-hero-sub'>Workflow execution · Email node status · Agent activity · Complete traceability</div>
</div>""", unsafe_allow_html=True)

    render_refresh_panel()

    # System health
    sec("System Component Status")
    comps = [
        ("FastAPI Backend",      "Online",                     "green"),
        ("Email Trigger Engine", "Active",                     "green"),
        ("Agent State Machine",  f"{len(agent_state)} workflows", "blue"),
        ("Trigger Log",          f"{len(trigger_log)} events",    "blue"),
        ("Email State",          f"{len(email_state)} contracts",  "green"),
        ("Gmail SMTP",
         "Simulation" if not (os.getenv("SMTP_PASSWORD","") and os.getenv("SMTP_PASSWORD","") not in {"your_app_password","your_16_char_app_password"})
                      else "Connected",
         "amber"),
        ("CSV Data",             f"{len(df)} contracts" if not df.empty else "Not loaded", "blue"),
    ]
    rows_html = "".join(
        f"<tr><td style='font-weight:600'>{n}</td><td>{badge(s,c)}</td></tr>"
        for n, s, c in comps
    )
    st.markdown(
        f"<table class='vf-tbl'><thead><tr><th>Component</th><th>Status</th></tr></thead>"
        f"<tbody>{rows_html}</tbody></table>",
        unsafe_allow_html=True)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2, gap="medium")

    with col_l:
        sec("Workflow Execution by Stage")
        total_wf = max(len(agent_state), 1)
        stage_cnt_map = {}
        for v in agent_state.values():
            s = v.get("Stage", "Planning")
            stage_cnt_map[s] = stage_cnt_map.get(s, 0) + 1
        clr_map = {"Planning": t["accent"], "Budgeting": t["amber"], "Approval": t["purple"],
                   "Execution": t["green"], "Closed": t["muted"]}
        for stage in STAGE_ORDER:
            cnt = stage_cnt_map.get(stage, 0)
            pct = cnt / total_wf * 100
            c   = clr_map.get(stage, t["accent"])
            st.markdown(
                f"<div style='margin-bottom:.6rem'>"
                f"<div style='display:flex;justify-content:space-between;font-size:.72rem;margin-bottom:3px'>"
                f"<span style='color:{t['text']};font-weight:600'>{stage}</span>"
                f"<span style='color:{t['muted']}'>{cnt} workflows ({pct:.0f}%)</span></div>"
                + bar(pct, c) + "</div>",
                unsafe_allow_html=True)

    with col_r:
        sec("Email Alert Breakdown")
        ALERT_LABELS = {
            "Alert_180":      "180-Day Planning",
            "Alert_90":       "90-Day Escalation",
            "Alert_60":       "60-Day Warning",
            "Alert_30":       "30-Day Exec",
            "Alert_Critical": "Critical 7-Day",
            "Alert_High_Util":"High Util Risk",
            "Alert_Low_Util": "Low Util Alert",
        }
        ALERT_COLORS = {
            "Alert_180":      t["accent"],
            "Alert_90":       t["amber"],
            "Alert_60":       t["amber"],
            "Alert_30":       t["red"],
            "Alert_Critical": t["purple"],
            "Alert_High_Util":t["orange"],
            "Alert_Low_Util": t["cyan"],
        }
        acnts = {}
        for flags in email_state.values():
            for ak, lbl in ALERT_LABELS.items():
                if flags.get(ak) == "SENT":
                    acnts[lbl] = acnts.get(lbl, 0) + 1
        total_a = max(sum(acnts.values()), 1)
        if acnts:
            for ak, lbl in ALERT_LABELS.items():
                cnt = acnts.get(lbl, 0)
                pct = cnt / total_a * 100
                c   = ALERT_COLORS.get(ak, t["accent"])
                st.markdown(
                    f"<div style='margin-bottom:.6rem'>"
                    f"<div style='display:flex;justify-content:space-between;font-size:.72rem;margin-bottom:3px'>"
                    f"<span style='color:{t['text']}'>{lbl}</span>"
                    f"<span style='color:{t['muted']}'>{cnt}</span></div>"
                    + bar(pct, c) + "</div>",
                    unsafe_allow_html=True)
        else:
            st.info("No email alerts logged yet. Click Refresh.")

    # Terminal
    sec("📟 Trigger Execution Terminal", "Audit Log")
    log_lines = []
    for cid, tdata in trigger_log.items():
        for ak, cls_key in [
            ("Alert_Critical", "err"),
            ("Alert_30",       "err"),
            ("Alert_High_Util","warn"),
            ("Alert_90",       "warn"),
            ("Alert_Low_Util", "purple"),
            ("Alert_180",      "info"),
        ]:
            info = tdata.get(ak)
            if isinstance(info, dict):
                status = info.get("status", "")
                if status in ["Running", "Completed", "Failed"]:
                    ts     = info.get("ts", "")[:19].replace("T", " ")
                    vendor = info.get("vendor", cid)
                    status_icon = "🔄" if status == "Running" else "✅" if status == "Completed" else "❌"
                    cls_key = "info" if status == "Running" else "ok" if status == "Completed" else "err"
                    log_lines.append((
                        ts, cls_key,
                        f"{status_icon} [{tdata.get('trigger_type','TRIGGER')}] {vendor} ({cid}) → {status} → {tdata.get('lifecycle_stage','?')}"
                    ))
    log_lines.sort(key=lambda x: x[0], reverse=True)

    if log_lines:
        lines_html = "".join(
            f"<div><span class='ts'>{ts}</span><span class='{cls}'>{msg}</span></div>"
            for ts, cls, msg in log_lines[:60]
        )
        st.markdown(f"<div class='vf-terminal'>{lines_html}</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='vf-terminal'>"
            f"<div><span class='ts'>--:--:--</span><span class='info'>[SYSTEM] No trigger events logged yet</span></div>"
            f"<div><span class='ts'>--:--:--</span><span class='info'>[SYSTEM] Click 'Refresh (3)' to start execution</span></div>"
            f"<div><span class='ts'>--:--:--</span><span class='info'>[SYSTEM] Or: python seed_state.py to pre-populate</span></div>"
            f"</div>", unsafe_allow_html=True)

    # Full email log
    sec("Full Email Execution Log")
    email_rows = []
    for cid, flags in email_state.items():
        row_csv = df[df["Contract_ID"] == cid] if not df.empty else pd.DataFrame()
        vendor  = row_csv.iloc[0]["Vendor"] if not row_csv.empty else "—"
        for ak, lbl in ALERT_LABELS.items():
            if flags.get(ak) == "SENT":
                tinfo = trigger_log.get(cid, {}).get(ak, {})
                ts    = tinfo.get("ts", "—")[:19].replace("T", " ") if isinstance(tinfo, dict) else "—"
                status = "✅ SENT"
                if isinstance(tinfo, dict):
                    exec_status = tinfo.get("status", "")
                    if exec_status == "Running": status = "🔄 Running"
                    elif exec_status == "Failed": status = "❌ Failed"
                email_rows.append({
                    "Contract": cid, "Vendor": vendor,
                    "Trigger": lbl, "Status": status, "Timestamp": ts,
                })
    if email_rows:
        em_df = pd.DataFrame(email_rows)
        st.dataframe(em_df, width='stretch', height=280)
        st.download_button("⬇ Download Full Log",
            em_df.to_csv(index=False).encode(), "email_log.csv", "text/csv")
    else:
        st.info("No email events recorded. Click Refresh to start.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Force reload states if requested
    if st.session_state.get("_force_reload", False):
        _force_reload_states()
        st.session_state["_force_reload"] = False
    
    # One-time email service seed on first load
    if "es_ran" not in st.session_state:
        try:
            from email_service import process as email_process
            email_process(batch_size=3)
        except Exception:
            pass
        st.session_state["es_ran"] = True

    inject_css()

    df = _load_csv()
    df = _enrich_df_with_agent_state(df)

    nav_col, content_col = st.columns([1, 5], gap="small")

    with nav_col:
        render_sidebar(df)

    with content_col:
        pid = st.session_state.get("page", "overview")
        render_topbar(pid, df)
        st.markdown("<div class='vf-main'>", unsafe_allow_html=True)

        if df.empty:
            st.warning(f"⚠️ CSV data not found at `{CSV_FILE}`. Make sure DATA_DIR is correct.")
        else:
            if   pid == "overview":  page_overview(df)
            elif pid == "workflow":  page_workflow(df)
            elif pid == "triggers":  page_triggers(df)
            elif pid == "alerts":    page_alerts(df)
            elif pid == "logs":      page_logs(df)

        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
