"""
email_service.py — VendorFlow AI / CRA
=======================================
Handles all trigger-based email dispatch for the Contract Renewal Agent.

Trigger windows:
  • 180-day  → Planning alert to Procurement Team
  • 90-day   → Finance escalation + renewal draft
  • 30-day   → Executive escalation
  • 7-day    → Critical daily reminder
  • High Util (>80%) → High Utilization & Budget Risk Trigger
  • Low Util (<70%)  → Underutilized License Trigger

Refresh-based controlled execution:
  process(batch_size=3) — only fires N triggers per call to avoid Gmail spam
"""

import os
import csv
import smtplib
import json
from email.mime.text import MIMEText
import random
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR         = os.getenv("DATA_DIR", "data")
CSV_FILE         = os.path.join(DATA_DIR, "merged_dataset_FINAL_fabricated_1341_util_adjusted.csv")
EMAIL_STATE_FILE = os.path.join(DATA_DIR, "email_state.json")
TRIGGER_LOG_FILE = os.path.join(DATA_DIR, "trigger_log.json")
ROTATION_STATE_FILE = os.path.join(DATA_DIR, "rotation_state.json")
AGENT_STATE_FILE = os.path.join(DATA_DIR, "agent_state.json")

# ── SMTP ───────────────────────────────────────────────────────────────────────
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER  = os.getenv("SMTP_EMAIL")
EMAIL_PASS  = os.getenv("SMTP_PASSWORD")

# ── Stakeholder routing ────────────────────────────────────────────────────────
PROCUREMENT_EMAIL = os.getenv("PROCUREMENT_EMAIL")
FINANCE_EMAIL     = os.getenv("FINANCE_EMAIL")
EXECUTIVE_EMAIL   = os.getenv("EXECUTIVE_EMAIL")

# ── Vendor name mapping ────────────────────────────────────────────────────────
VENDORS = [
    "OpenAI",
    "Atlassify",
    "Cloudora",
    "Nexaflow",
    "Veloxa",
    "Prismly",
    "Databridge",
    "Salesforce",
    "Microsoft",
    "AWS",
]

VENDOR_EMAIL_MAP = {v: PROCUREMENT_EMAIL for v in VENDORS}
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

C1064_ACTION_LABELS = {
    "Planning":  "Start Budgeting",
    "Budgeting": "Send for Approval",
    "Approval":  "Approve Execution",
    "Execution": "Close Renewal",
}

C1064_NEXT_STAGE = {
    "Planning":  "Budgeting",
    "Budgeting": "Approval",
    "Approval":  "Execution",
    "Execution": "Closed",
}

WORKFLOW_STAGES = ["Planning", "Budgeting", "Approval", "Execution", "Closed"]
WORKFLOW_ACTION_LABELS = {
    "Planning":  "Start Budgeting",
    "Budgeting": "Send for Approval",
    "Approval":  "Approve Execution",
    "Execution": "Close Renewal",
}
WORKFLOW_NEXT_STAGE = {
    "Planning":  "Budgeting",
    "Budgeting": "Approval",
    "Approval":  "Execution",
    "Execution": "Closed",
}

# ── License Type validation ─────────────────────────────────────────────────────
VALID_LICENSE_TYPES = {"Full", "Contributor", "Collaborator"}

def _validate_license_type(license_type: str) -> str:
    """Normalize and validate license type to allowed values."""
    if not license_type:
        return "Full"
    
    # Normalize the input
    normalized = str(license_type).strip()
    
    # Direct match
    if normalized in VALID_LICENSE_TYPES:
        return normalized
    
    # Case-insensitive match
    for valid in VALID_LICENSE_TYPES:
        if normalized.lower() == valid.lower():
            return valid
    
    # Default to Full if invalid
    print(f"WARNING: Invalid license type '{license_type}' - defaulting to 'Full'")
    return "Full"

CONTRACT_DOCS = {
    "C-1064": (
        "https://agivantechnologiespvtltd-my.sharepoint.com/:w:/g/personal/"
        "pallanti_vatsal_agivant_com/IQB-Ndnt9mr0R4NtdGuEXG8iARX_gD85A84wbCHx5-xK9pQ?e=STFrfU"
    )
}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _map_vendor_name(orig_vendor: str, contract_id: str) -> str:
    if not isinstance(orig_vendor, str):
        return orig_vendor
    if orig_vendor.lower().startswith("vendor"):
        digits = "".join(ch for ch in str(contract_id) if ch.isdigit())
        try:
            idx = int(digits) if digits else 0
        except Exception:
            idx = 0
        return VENDORS[idx % len(VENDORS)]
    return orig_vendor


def _c1064_stage_to_alert(stage: str) -> str | None:
    return {
        "Planning": "Alert_180",
        "Budgeting": "Alert_90",
        "Approval": "Alert_30",
        "Execution": "Alert_Critical",
        "Closed": "Alert_Closed",
    }.get(stage)


def _build_c1064_special_trigger(row: dict, c_state: dict, email_state: dict) -> dict | None:
    stage = c_state.get("Stage", "Planning")
    if stage not in {"Planning", "Budgeting", "Approval", "Execution", "Closed"}:
        return None
    # Check if email has already been sent for this stage
    if c_state.get("Email_Sent", False):
        return None

    alert_key = _c1064_stage_to_alert(stage)
    if not alert_key:
        return None
    # C-1064 manual lifecycle emails are controlled by the agent state email flag,
    # not by prior standard trigger delivery history. This preserves the original
    # lifecycle action-button flow even when the same alert key was previously sent.
    # However, we also check email_state to avoid duplicate sends if both states are out of sync

    if stage == "Planning":
        title = "180-Day Renewal Planning"
        message = (
            "ℹ️ 180 days to renewal. Procurement team notified. "
            "Initial renewal planning initiated. Long-term strategy review."
        )
    elif stage == "Budgeting":
        title = "90-Day Renewal Escalation"
        message = (
            "⚠️ 90 days to renewal. Finance and procurement teams notified. "
            "Budget approval workflow initiated. Escalation tracking enabled."
        )
    elif stage == "Approval":
        title = "30-Day Critical Renewal — Executive Escalation"
        message = (
            "🚨 30 days to renewal. Executive escalation initiated. Urgent renewal "
            "status update dispatched. Daily tracking enabled."
        )
    elif stage == "Execution":
        title = "CRITICAL — Contract Expiring in 7 Days"
        message = (
            "🔴 Contract is expiring within 7 days. Immediate action required. "
            "All stakeholders have been notified."
        )
    else:  # Closed
        title = "Contract Renewal Completed"
        message = (
            "✅ Contract renewal process completed successfully. "
            "All stages finalized. Vendor acknowledgment received."
        )

    action_label = C1064_ACTION_LABELS.get(stage)
    action_stage = C1064_NEXT_STAGE.get(stage)

    
    return {
        "alert_key": alert_key,
        "ttype": f"C-1064 {stage} Lifecycle",
        "lifecycle": f"{stage} Workflow",
        "build_fn": lambda r=row, t=title, m=message, a=action_label, s=action_stage: build_email(r, t, m, action_label=a, action_stage=s),
        "targets": _get_recipients(row, row.get("Vendor", "")),
        "priority": 0,
    }


def _get_contract_workflow_state(contract_id: str, agent_state: dict) -> tuple[str, bool]:
    state = agent_state.get(contract_id, {})
    stage = state.get("Stage", "Planning")
    if stage not in WORKFLOW_STAGES:
        stage = "Planning"
    return stage, bool(state.get("Email_Sent", False))


def _build_lifecycle_trigger(row: dict, stage: str, recipients: list[str]) -> dict:
    alert_key = _c1064_stage_to_alert(stage)
    if not alert_key:
        return {}

    if stage == "Planning":
        title = "180-Day Renewal Planning"
        message = (
            "ℹ️ 180 days to renewal. Procurement team notified. "
            "Initial renewal planning initiated. Long-term strategy review."
        )
    elif stage == "Budgeting":
        title = "90-Day Renewal Budgeting"
        message = (
            "⚠️ Budgeting phase pending. Finance and procurement teams notified. "
            "Budget approval workflow initiated. Escalation tracking enabled."
        )
    elif stage == "Approval":
        title = "30-Day Executive Approval Pending"
        message = (
            "🚨 Executive approval is pending. Urgent renewal status update dispatched. "
            "Leadership review and sign-off are required before execution."
        )
    elif stage == "Execution":
        title = "Execution / Finalization Pending"
        message = (
            "🔴 Execution is pending. Final renewal steps are ready. "
            "All stakeholders have been notified and final confirmation is required."
        )
    else:  # Closed
        title = "Contract Renewal Completed"
        message = (
            "✅ Contract renewal process completed successfully. "
            "All stages finalized. Vendor acknowledgment received."
        )

    action_label = WORKFLOW_ACTION_LABELS.get(stage)
    action_stage = WORKFLOW_NEXT_STAGE.get(stage)
    if stage == "Closed":
        action_label = None
        action_stage = None

    return {
        "alert_key": alert_key,
        "ttype": f"{stage} Lifecycle",
        "lifecycle": f"{stage} Workflow",
        "build_fn": lambda r=row, t=title, m=message, a=action_label, s=action_stage: build_email(r, t, m, action_label=a, action_stage=s),
        "targets": recipients,
        "priority": 0,
    }


def get_renewal_month_year(end_date_str: str) -> str:
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(end_date_str, fmt).strftime("%B %Y")
        except Exception:
            pass
    return end_date_str


def fmt_number(val) -> str:
    try:
        return f"{int(float(val)):,}"
    except Exception:
        return str(val)


def fmt_currency(val) -> str:
    try:
        return f"${float(val):,.2f}"
    except Exception:
        return str(val)


# ══════════════════════════════════════════════════════════════════════════════
# STATE PERSISTENCE
# ══════════════════════════════════════════════════════════════════════════════

def _load_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_json(path: str, data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"WARNING: Could not save {path}: {e}")


def _update_workflow_stage(contract_id: str, alert_key: str, vendor: str, days: int, util: float) -> None:
    """
    Update the workflow stage in agent_state.json when a trigger fires.
    This synchronizes trigger execution with workflow progression.
    
    IMPORTANT: For lifecycle alerts (180/90/30/7/Closed), we DO NOT auto-advance the Stage.
    The Stage is only advanced when the user clicks the action button in the email.
    This function only marks Email_Sent=True for lifecycle alerts to prevent duplicate sends.
    
    Mapping:
    - Alert_180 (180-day) → Planning
    - Alert_90 (90-day) → Budgeting
    - Alert_30 (30-day) → Approval
    - Alert_Critical (7-day) → Execution
    - Alert_High_Util → Risk Monitoring (special lifecycle)
    - Alert_Low_Util → Optimization Recommendation (special lifecycle)
    """
    agent_state = _load_json(AGENT_STATE_FILE)
    
    # Determine the appropriate workflow stage based on trigger type
    stage_mapping = {
        "Alert_180": "Planning",
        "Alert_90": "Budgeting",
        "Alert_30": "Approval",
        "Alert_Critical": "Execution",
        "Alert_High_Util": "Risk Monitoring",
        "Alert_Low_Util": "Optimization Recommendation",
    }
    
    # Actor mapping for each stage
    actor_mapping = {
        "Planning": "Procurement Team",
        "Budgeting": "Procurement Team",
        "Approval": "Executive Approver",
        "Execution": "Procurement Team",
        "Risk Monitoring": "Procurement Team",
        "Optimization Recommendation": "Procurement Team",
    }
    
    new_stage = stage_mapping.get(alert_key, "Planning")
    actor = actor_mapping.get(new_stage, "Procurement Team")

    # Get existing state or create default
    existing = agent_state.get(contract_id, {})
    previous_stage = existing.get("Stage", "Planning")
    stage_history = existing.get("Stage_History", [])

    lifecycle_keys = {"Alert_180", "Alert_90", "Alert_30", "Alert_Critical", "Alert_Closed"}

    # For lifecycle alerts (180/90/30/7/Closed) we MUST NOT auto-advance the Stage.
    # The Stage is only advanced when the user clicks the action button.
    # This function only marks Email_Sent=True and updates metadata.
    if alert_key in lifecycle_keys:
        if not existing:
            # Initialize state for a contract not previously tracked
            # Only initialize if this is the first lifecycle trigger
            previous_stage = "Planning"
            stage_history = []
            agent_state[contract_id] = {
                "Stage": new_stage,
                "Previous_Stage": previous_stage,
                "Pending_With": actor,
                "Email_Sent": True,
                "Execution_Status": "Email Sent",
                "Escalated": False,
                "Stage_History": stage_history,
                "Last_Trigger": alert_key,
                "Last_Trigger_Timestamp": datetime.now(timezone.utc).isoformat(),
                "Vendor": vendor,
                "Days_to_Renewal": days,
                "Avg_Utilization_Pct": util,
            }
            print(f"[Workflow] Initialized {contract_id} stage to {new_stage} (trigger: {alert_key})")
        else:
            # Preserve existing Stage; only mark email sent and update metadata
            # DO NOT change the Stage - it's controlled by manual button clicks
            existing["Email_Sent"] = True
            existing["Execution_Status"] = "Email Sent"
            existing["Last_Trigger"] = alert_key
            existing["Last_Trigger_Timestamp"] = datetime.now(timezone.utc).isoformat()
            # Update vendor/days/util metadata but preserve Stage
            existing["Vendor"] = vendor
            existing["Days_to_Renewal"] = days
            existing["Avg_Utilization_Pct"] = util
            agent_state[contract_id] = existing
            print(f"[Workflow] Marked Email_Sent for {contract_id} at stage {existing.get('Stage')} (trigger: {alert_key})")
    else:
        # Non-lifecycle alerts (e.g., high/low util) may update stage
        # These are informational alerts that don't follow the manual approval flow
        if previous_stage != new_stage:
            stage_history.append({
                "from": previous_stage,
                "to": new_stage,
                "trigger": alert_key,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        agent_state[contract_id] = {
            "Stage": new_stage,
            "Previous_Stage": previous_stage,
            "Pending_With": actor,
            "Email_Sent": True,  # Email was just sent
            "Execution_Status": "Running",
            "Escalated": existing.get("Escalated", False),
            "Stage_History": stage_history,
            "Last_Trigger": alert_key,
            "Last_Trigger_Timestamp": datetime.now(timezone.utc).isoformat(),
            "Vendor": vendor,
            "Days_to_Renewal": days,
            "Avg_Utilization_Pct": util,
        }

    _save_json(AGENT_STATE_FILE, agent_state)


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL SEND
# ══════════════════════════════════════════════════════════════════════════════

_SMTP_PLACEHOLDERS = {
    "your_gmail@gmail.com",
    "your_16_char_app_password",
    "##__YOUR_GMAIL_ADDRESS__##",
    "##__YOUR_GMAIL_APP_PASSWORD__##",
}


def _smtp_configured() -> bool:
    return bool(
        EMAIL_USER
        and EMAIL_PASS
        and EMAIL_USER not in _SMTP_PLACEHOLDERS
        and EMAIL_PASS not in _SMTP_PLACEHOLDERS
    )


def send_email(to_email: str, subject: str, body: str) -> bool:
    if not to_email:
        print("WARNING: Missing recipient - skipping send.")
        return False

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_USER or "vendorflow@simulation.local"
    msg["To"]      = to_email

    if not _smtp_configured():
        print(f"SIM send to {to_email} | {subject}")
        return True

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"Sent -> {to_email}")
        return True
    except Exception as e:
        print(f"SMTP error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

def build_email(contract: dict, stage: str, message: str, action_label: str | None = None, action_stage: str | None = None):
    contract_id   = contract.get("Contract_ID", "N/A")
    vendor        = contract.get("Vendor", "N/A")
    license_type  = contract.get("License_Type", "N/A")
    days          = contract.get("Days_to_Renewal", "N/A")
    renewal_month = get_renewal_month_year(contract.get("End_Date", ""))
    total_users   = fmt_number(contract.get("Total_Users", "N/A"))
    active_users  = fmt_number(contract.get("Active_Users", "N/A"))

    utilization = contract.get("Avg_Utilization_Pct", "N/A")
    try:
        util_display = f"{float(str(utilization).replace('%','').strip()):.2f}%"
    except Exception:
        util_display = str(utilization)

    budget     = fmt_currency(contract.get("Total_Annual_Budget_USD", "N/A"))
    report_url = CONTRACT_DOCS.get(contract_id, "")
    action_section = ""
    # Support action buttons for ALL contracts in workflow stages, not just C-1064
    if action_label and action_stage:
        action_url = f"{BASE_URL}/action/{contract_id}/{action_stage}"
        action_section = f"""
  <div style=\"text-align:center;margin:24px 0;\">
    <a href=\"{action_url}\" style=\"display:inline-block;padding:14px 22px;background:#1a73e8;color:#fff;text-decoration:none;border-radius:8px;font-size:15px;font-weight:700;\">
      {action_label}
    </a>
  </div>"""

    # Link to the contract summary report endpoint for all contracts
    report_url_endpoint = f"{BASE_URL}/report/{contract_id}"
    report_section = f"""
<hr style="border:none;border-top:1px solid #eee;margin:16px 0">
<h4 style="margin-bottom:10px;color:#333">🤖 AI Generated Summary Analysis</h4>
<a href="{report_url_endpoint}" style="display:inline-block;padding:10px 20px;background:#1a73e8;
   color:#fff;text-decoration:none;border-radius:6px;font-size:13px;font-weight:bold">
   View Summary Report — {contract_id}
</a>"""

    subject = f"{stage} Alert — Nexaflow | {contract_id}"

    body = f"""
<div style="font-family:Arial,sans-serif;max-width:620px;padding:24px;
            border:1px solid #e5e7eb;border-radius:8px;background:#fff">

  <div style="border-left:4px solid #1d4ed8;padding-left:14px;margin-bottom:20px">
    <h2 style="margin:0 0 4px;color:#1f2937;font-size:20px">{stage}</h2>
    <span style="font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.5px">
      VendorFlow AI · Contract Renewal Agent
    </span>
  </div>

  <p style="background:#eff6ff;border-left:4px solid #3b82f6;padding:12px;
             border-radius:0 6px 6px 0;color:#1e40af;font-size:14px;margin-bottom:20px">
    {message}
  </p>

  <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
    <tr><td style="padding:8px 0;color:#6b7280;width:42%;font-weight:600">Contract ID</td>
        <td style="color:#111827;font-weight:700">{contract_id}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Vendor</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">Nexaflow</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">License Type</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{license_type}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Renewal Month</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{renewal_month}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Days Remaining</td>
        <td style="color:#dc2626;font-weight:700;border-top:1px solid #f3f4f6">{days} days</td></tr>
  </table>

  <h4 style="color:#374151;margin-bottom:8px;border-bottom:1px solid #f3f4f6;padding-bottom:6px">
    📊 License Utilization
  </h4>
  <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
    <tr><td style="padding:7px 0;color:#6b7280;width:42%;font-weight:600">Licenses Used</td>
        <td style="color:#111827"><b>{active_users}</b> of <b>{total_users}</b></td></tr>
    <tr><td style="padding:7px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Utilization Rate</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6"><b>{util_display}</b></td></tr>
  </table>

  <h4 style="color:#374151;margin-bottom:8px;border-bottom:1px solid #f3f4f6;padding-bottom:6px">
    💰 Budget
  </h4>
  <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
    <tr><td style="padding:7px 0;color:#6b7280;width:42%;font-weight:600">Annual Budget</td>
        <td style="color:#111827">{budget}</td></tr>
  </table>

  {action_section}
  {report_section}

  <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
  <p style="font-size:11px;color:#9ca3af;text-align:center">
    Automated by VendorFlow AI · Contract Renewal Agent · Do not reply
  </p>
</div>"""

    return subject, body


def build_high_util_email(contract: dict, util_pct: float, severity: str):
    """Email template for High Utilization & Budget Risk trigger."""
    contract_id  = contract.get("Contract_ID", "N/A")
    vendor       = contract.get("Vendor", "N/A")
    license_type = contract.get("License_Type", "N/A")
    budget       = fmt_currency(contract.get("Total_Annual_Budget_USD", 0))
    actual_spend = fmt_currency(contract.get("Total_Actual_Spend_USD", 0))
    budget_status = contract.get("Budget_Status", "Unknown")
    days         = contract.get("Days_to_Renewal", "N/A")

    color_map = {"Warning": "#f59e0b", "High Risk": "#f97316", "Critical": "#ef4444"}
    color = color_map.get(severity, "#ef4444")

    subject = f"⚠️ HIGH UTILIZATION ALERT [{severity}] — {vendor} | {contract_id}"
    body = f"""
<div style="font-family:Arial,sans-serif;max-width:620px;padding:24px;
            border:2px solid {color};border-radius:8px;background:#fff">

  <div style="background:{color};padding:12px 16px;border-radius:6px;margin-bottom:20px">
    <h2 style="margin:0;color:#fff;font-size:18px">⚠️ High Utilization & Budget Risk</h2>
    <span style="color:#fff;opacity:.85;font-size:12px">{severity} — VendorFlow AI · CRA</span>
  </div>

  <p style="background:#fff7ed;border-left:4px solid {color};padding:12px;
             border-radius:0 6px 6px 0;color:#7c2d12;font-size:14px;margin-bottom:20px">
    License utilization for <strong>{vendor}</strong> has reached <strong>{util_pct:.1f}%</strong>,
    triggering a <strong>{severity}</strong> alert. Immediate stakeholder review required.
  </p>

  <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
    <tr><td style="padding:8px 0;color:#6b7280;width:42%;font-weight:600">Contract ID</td>
        <td style="color:#111827;font-weight:700">{contract_id}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Vendor</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{vendor}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">License Type</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{license_type}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Utilization Rate</td>
        <td style="color:{color};font-weight:700;border-top:1px solid #f3f4f6">{util_pct:.1f}%</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Severity</td>
        <td style="border-top:1px solid #f3f4f6">
          <span style="background:{color};color:#fff;padding:2px 10px;border-radius:999px;
                       font-size:12px;font-weight:700">{severity}</span>
        </td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Annual Budget</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{budget}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Actual Spend</td>
        <td style="color:#dc2626;font-weight:700;border-top:1px solid #f3f4f6">{actual_spend}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Budget Status</td>
        <td style="color:#dc2626;font-weight:700;border-top:1px solid #f3f4f6">{budget_status}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Days to Renewal</td>
        <td style="color:#dc2626;font-weight:700;border-top:1px solid #f3f4f6">{days} days</td></tr>
  </table>

  <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:14px;margin-bottom:16px">
    <h4 style="margin:0 0 8px;color:#7f1d1d">🚨 Recommended Actions</h4>
    <ul style="margin:0;padding-left:18px;color:#7f1d1d;font-size:13px">
      <li>Review license allocation and identify unused seats</li>
      <li>Negotiate seat expansion with vendor before renewal</li>
      <li>Evaluate budget reallocation to cover overage risk</li>
      <li>Escalate to Finance team for budget revision approval</li>
    </ul>
  </div>

  <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
  <p style="font-size:11px;color:#9ca3af;text-align:center">
    Automated by VendorFlow AI · High Utilization Trigger · Do not reply
  </p>
</div>"""

    return subject, body


def build_low_util_email(contract: dict, util_pct: float):
    """Email template for Underutilized License trigger."""
    contract_id  = contract.get("Contract_ID", "N/A")
    vendor       = contract.get("Vendor", "N/A")
    license_type = contract.get("License_Type", "N/A")
    budget       = fmt_currency(contract.get("Total_Annual_Budget_USD", 0))
    total_users  = fmt_number(contract.get("Total_Users", 0))
    active_users = fmt_number(contract.get("Active_Users", 0))
    days         = contract.get("Days_to_Renewal", "N/A")

    subject = f"📉 UNDERUTILIZED LICENSE — Optimization Opportunity | {vendor} | {contract_id}"
    body = f"""
<div style="font-family:Arial,sans-serif;max-width:620px;padding:24px;
            border:2px solid #8b5cf6;border-radius:8px;background:#fff">

  <div style="background:linear-gradient(135deg,#7c3aed,#4f46e5);padding:12px 16px;
              border-radius:6px;margin-bottom:20px">
    <h2 style="margin:0;color:#fff;font-size:18px">📉 Underutilized License Detected</h2>
    <span style="color:#fff;opacity:.85;font-size:12px">Optimization Opportunity — VendorFlow AI · CRA</span>
  </div>

  <p style="background:#f5f3ff;border-left:4px solid #8b5cf6;padding:12px;
             border-radius:0 6px 6px 0;color:#4c1d95;font-size:14px;margin-bottom:20px">
    License utilization for <strong>{vendor}</strong> is only <strong>{util_pct:.1f}%</strong> —
    well below the 70% activity threshold. This represents a significant cost optimization opportunity.
  </p>

  <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
    <tr><td style="padding:8px 0;color:#6b7280;width:42%;font-weight:600">Contract ID</td>
        <td style="color:#111827;font-weight:700">{contract_id}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Vendor</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{vendor}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">License Type</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{license_type}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Utilization Rate</td>
        <td style="color:#7c3aed;font-weight:700;border-top:1px solid #f3f4f6">{util_pct:.1f}%</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Active Users</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{active_users} of {total_users}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Annual Budget</td>
        <td style="color:#111827;border-top:1px solid #f3f4f6">{budget}</td></tr>
    <tr><td style="padding:8px 0;color:#6b7280;border-top:1px solid #f3f4f6;font-weight:600">Days to Renewal</td>
        <td style="color:#7c3aed;font-weight:700;border-top:1px solid #f3f4f6">{days} days</td></tr>
  </table>

  <div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:8px;padding:14px;margin-bottom:16px">
    <h4 style="margin:0 0 8px;color:#4c1d95">💡 Optimization Recommendations</h4>
    <ul style="margin:0;padding-left:18px;color:#4c1d95;font-size:13px">
      <li>Consider downgrading to a lower license tier</li>
      <li>Identify and deprovision inactive user accounts</li>
      <li>Evaluate license removal at next renewal</li>
      <li>Consolidate with other team licenses if possible</li>
      <li>Request vendor pricing review based on actual usage</li>
    </ul>
  </div>

  <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
  <p style="font-size:11px;color:#9ca3af;text-align:center">
    Automated by VendorFlow AI · Underutilization Trigger · Do not reply
  </p>
</div>"""

    return subject, body


# ══════════════════════════════════════════════════════════════════════════════
# RECIPIENT ROUTING
# ══════════════════════════════════════════════════════════════════════════════

def _get_recipients(row: dict, mapped_vendor: str) -> list:
    try:
        val = float(row.get("Total_Annual_Budget_USD", 0) or 0)
    except Exception:
        val = 0.0

    if val >= 2_000_000 and EXECUTIVE_EMAIL:
        recipients = [EXECUTIVE_EMAIL]
        if FINANCE_EMAIL:
            recipients.append(FINANCE_EMAIL)
    elif val >= 500_000 and FINANCE_EMAIL:
        recipients = [FINANCE_EMAIL]
        if PROCUREMENT_EMAIL:
            recipients.append(PROCUREMENT_EMAIL)
    else:
        fallback = VENDOR_EMAIL_MAP.get(mapped_vendor) or PROCUREMENT_EMAIL
        recipients = [fallback] if fallback else []

    seen = set()
    out  = []
    for r in recipients:
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# ALERT FIELDS
# ══════════════════════════════════════════════════════════════════════════════

ALERT_FIELDS = [
    "Alert_180", "Alert_90", "Alert_60",
    "Alert_30",  "Alert_Critical",
    "Alert_Closed",
    "Alert_Under_Utilized", "Alert_License_Exhaustion",
    "Alert_High_Util",      "Alert_Low_Util",
]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PROCESS — Controlled Refresh-Based Execution
# ══════════════════════════════════════════════════════════════════════════════

def process(batch_size: int = 3) -> dict:
    """
    Scan contracts and fire trigger emails — controlled execution with rotation.
    Only fires `batch_size` NEW triggers per call to avoid Gmail limits.
    Rotates through all 6 trigger types to ensure balanced execution.

    Returns a summary dict of what was fired in this batch.
    """
    if not os.path.exists(CSV_FILE):
        print(f"WARNING: CSV not found: {CSV_FILE}")
        return {}

    email_state = _load_json(EMAIL_STATE_FILE)
    trigger_log = _load_json(TRIGGER_LOG_FILE)
    rotation_state = _load_json(ROTATION_STATE_FILE)
    agent_state = _load_json(AGENT_STATE_FILE)

    c1064_state = agent_state.get("C-1064", {})
    c1064_row = None

    fired_this_run = {}
    total_fired    = 0
    now_ts         = datetime.now(timezone.utc).isoformat()

    # Track which trigger types to prioritize in this rotation cycle
    # Lifecycle triggers must be prioritized over util alerts.
    # The order is rotated to avoid repeated domination by a single category.
    trigger_priority_order = [
        "Alert_180",       # 180-Day Planning
        "Alert_90",        # 90-Day Budgeting
        "Alert_30",        # 30-Day Approval
        "Alert_Critical",  # 7-Day Execution
        "Alert_Closed",    # Closed confirmation
    ]
    util_priority_order = ["Alert_High_Util", "Alert_Low_Util"]
    
    # Get current rotation index for lifecycle categories (0-4)
    rotation_idx = rotation_state.get("rotation_index", 0)
    rotated_lifecycle_priority = trigger_priority_order[rotation_idx:] + trigger_priority_order[:rotation_idx]
    rotation_state["rotation_index"] = (rotation_idx + 1) % len(trigger_priority_order)

    # Get current rotation index for util categories (0-1)
    util_rotation_idx = rotation_state.get("util_rotation_index", 0)
    rotated_util_priority = util_priority_order[util_rotation_idx:] + util_priority_order[:util_rotation_idx]
    rotation_state["util_rotation_index"] = (util_rotation_idx + 1) % len(util_priority_order)

    _save_json(ROTATION_STATE_FILE, rotation_state)

    with open(CSV_FILE, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows   = list(reader)

    lifecycle_keys = {"Alert_180", "Alert_90", "Alert_30", "Alert_Critical", "Alert_Closed"}
    util_keys = {"Alert_High_Util", "Alert_Low_Util"}

    lifecycle_candidates = []
    util_candidates = []

    for row in rows:
        try:
            days = int(float(row.get("Days_to_Renewal", -1) or -1))
        except (ValueError, TypeError):
            days = -1

        if days < 0:
            continue

        cid    = row.get("Contract_ID", "unknown")
        vendor = _map_vendor_name(row.get("Vendor", ""), cid)
        row["Vendor"] = vendor
        
        # Validate and normalize license type
        license_type = row.get("License_Type", "Full")
        row["License_Type"] = _validate_license_type(license_type)

        try:
            util = float(str(row.get("Avg_Utilization_Pct", "0")).replace("%", "").strip())
        except Exception:
            util = 0.0

        recipients = _get_recipients(row, vendor)

        # Restore persisted alert flags
        c_state = email_state.get(cid, {})
        for f in ALERT_FIELDS:
            row[f] = c_state.get(f, "")

        if cid == "C-1064":
            c1064_row = row
            continue

        current_stage, current_email_sent = _get_contract_workflow_state(cid, agent_state)

        # If a lifecycle stage email is pending, prioritize it and skip util alerts
        if not current_email_sent and current_stage in WORKFLOW_STAGES:
            stage_trigger = _build_lifecycle_trigger(row, current_stage, recipients)
            if stage_trigger:
                lifecycle_candidates.append({
                    "cid": cid,
                    "vendor": vendor,
                    "days": days,
                    "util": util,
                    "trig": stage_trigger,
                })
            continue

        # High Utilization (only if no lifecycle stage email is pending)
        if util > 80 and row.get("Alert_High_Util") != "SENT":
            if util >= 90:
                severity = "Critical"
            elif util >= 80:
                severity = "High Risk"
            else:
                severity = "Warning"
            util_candidates.append({
                "cid": cid,
                "vendor": vendor,
                "days": days,
                "util": util,
                "trig": {
                    "alert_key": "Alert_High_Util",
                    "ttype": f"High Utilization {severity}",
                    "lifecycle": "Capacity Planning",
                    "build_fn": lambda r=row, u=util, s=severity: build_high_util_email(r, u, s),
                    "targets": recipients,
                    "priority": 4,
                },
            })

        # Low Utilization
        if util < 70 and row.get("Alert_Low_Util") != "SENT":
            util_candidates.append({
                "cid": cid,
                "vendor": vendor,
                "days": days,
                "util": util,
                "trig": {
                    "alert_key": "Alert_Low_Util",
                    "ttype": "Underutilized License",
                    "lifecycle": "Optimization Review",
                    "build_fn": lambda r=row, u=util: build_low_util_email(r, u),
                    "targets": recipients,
                    "priority": 5,
                },
            })

    # Randomize pending lifecycle and util candidates separately
    random.shuffle(lifecycle_candidates)
    random.shuffle(util_candidates)

    grouped_lifecycle = {}
    grouped_util = {}
    for pt in lifecycle_candidates:
        key = pt["trig"]["alert_key"]
        grouped_lifecycle.setdefault(key, []).append(pt)
    for pt in util_candidates:
        key = pt["trig"]["alert_key"]
        grouped_util.setdefault(key, []).append(pt)

    for key in grouped_lifecycle:
        random.shuffle(grouped_lifecycle[key])
    for key in grouped_util:
        random.shuffle(grouped_util[key])

    selected = []
    seen_cids = set()
    seen_alert_keys = set()
    trigger_type_counts = {}
    total_fired = 0

    # LIFECYCLE-FIRST STRATEGY: Prioritize lifecycle triggers over util alerts
    # This ensures the manual approval workflow progresses properly
    # Only fill remaining batch slots with util alerts if no lifecycle triggers are pending
    
    # First pass: Select lifecycle triggers in rotated order
    for key in rotated_lifecycle_priority:
        if total_fired >= batch_size:
            break
        lst = grouped_lifecycle.get(key, [])
        if not lst:
            continue

        # Limit each lifecycle trigger type to 1 per batch to ensure rotation
        if trigger_type_counts.get(key, 0) >= 1:
            continue

        while lst and total_fired < batch_size:
            candidate = lst.pop(0)
            cid = candidate["cid"]
            alert_key = candidate["trig"]["alert_key"]

            if cid in seen_cids:
                continue
            
            if alert_key in seen_alert_keys:
                continue

            latest_email_state = _load_json(EMAIL_STATE_FILE)
            latest_agent_state = _load_json(AGENT_STATE_FILE)
            
            # Check if email already sent for this stage
            if latest_email_state.get(cid, {}).get(alert_key) == "SENT":
                continue
            if latest_agent_state.get(cid, {}).get("Email_Sent", False):
                continue

            selected.append(candidate)
            seen_cids.add(cid)
            seen_alert_keys.add(alert_key)
            trigger_type_counts[key] = trigger_type_counts.get(key, 0) + 1
            total_fired += 1

    # Second pass: Fill remaining batch slots with util alerts (rotated order)
    if total_fired < batch_size:
        for key in rotated_util_priority:
            if total_fired >= batch_size:
                break
            lst = grouped_util.get(key, [])
            if not lst:
                continue

            # Limit each util trigger type to 1 per batch to ensure rotation
            if trigger_type_counts.get(key, 0) >= 1:
                continue

            while lst and total_fired < batch_size:
                candidate = lst.pop(0)
                cid = candidate["cid"]
                alert_key = candidate["trig"]["alert_key"]

                if cid in seen_cids:
                    continue
                
                if alert_key in seen_alert_keys:
                    continue

                latest_email_state = _load_json(EMAIL_STATE_FILE)
                if latest_email_state.get(cid, {}).get(alert_key) == "SENT":
                    continue

                selected.append(candidate)
                seen_cids.add(cid)
                seen_alert_keys.add(alert_key)
                trigger_type_counts[key] = trigger_type_counts.get(key, 0) + 1
                total_fired += 1

    # Fire selected triggers
    total_fired = 0
    for pt in selected:
        if total_fired >= batch_size:
            break
        cid = pt["cid"]
        vendor = pt["vendor"]
        days = pt["days"]
        util = pt["util"]
        trig = pt["trig"]

        alert_key = trig["alert_key"]
        ttype = trig["ttype"]
        lifecycle = trig["lifecycle"]
        build_fn = trig["build_fn"]
        targets = trig["targets"]

        trigger_log.setdefault(cid, {})
        trigger_log[cid][alert_key] = {
            "status": "Running",
            "days":   days,
            "vendor": vendor,
            "ts":     now_ts,
        }
        trigger_log[cid]["trigger_type"] = ttype
        trigger_log[cid]["lifecycle_stage"] = lifecycle
        _save_json(TRIGGER_LOG_FILE, trigger_log)

        subj, body = build_fn()
        ok = any(send_email(r, subj, body) for r in targets)
        if ok:
            email_state.setdefault(cid, {})
            email_state[cid][alert_key] = "SENT"
            _save_json(EMAIL_STATE_FILE, email_state)

            _update_workflow_stage(cid, alert_key, vendor, days, util)

            total_fired += 1
            trigger_log[cid][alert_key]["status"] = "Completed"
            trigger_log[cid][alert_key]["completed_ts"] = datetime.now(timezone.utc).isoformat()
            fired_this_run[alert_key] = fired_this_run.get(alert_key, 0) + 1
        else:
            trigger_log[cid][alert_key]["status"] = "Failed"
            trigger_log[cid][alert_key]["error"] = "Email send failed"
        _save_json(TRIGGER_LOG_FILE, trigger_log)

    # Always include special C-1064 lifecycle mail if it is pending and manual.
    if c1064_row is None and c1064_state:
        # Fallback row for C-1064 in case the CSV row is not present or was skipped.
        c1064_row = {
            "Contract_ID": "C-1064",
            "Vendor": c1064_state.get("Vendor", "Unknown"),
            "License_Type": c1064_state.get("License_Type", "Full"),
            "Days_to_Renewal": c1064_state.get("Days_to_Renewal", 180),
            "Avg_Utilization_Pct": c1064_state.get("Avg_Utilization_Pct", 0),
            "Total_Annual_Budget_USD": c1064_state.get("Total_Annual_Budget_USD", 0),
            "End_Date": c1064_state.get("End_Date", ""),
        }

    if c1064_row is not None:
        special_trigger = _build_c1064_special_trigger(c1064_row, c1064_state, email_state)
        if special_trigger:
            cid = "C-1064"
            vendor = c1064_row.get("Vendor", "")
            days = int(float(c1064_row.get("Days_to_Renewal", -1) or -1))
            util = float(str(c1064_row.get("Avg_Utilization_Pct", "0")).replace("%", "") or 0)
            alert_key = special_trigger["alert_key"]
            trigger_log.setdefault(cid, {})
            trigger_log[cid][alert_key] = {
                "status": "Running",
                "days":   days,
                "vendor": vendor,
                "ts":     now_ts,
            }
            trigger_log[cid]["trigger_type"] = special_trigger["ttype"]
            trigger_log[cid]["lifecycle_stage"] = special_trigger["lifecycle"]
            _save_json(TRIGGER_LOG_FILE, trigger_log)

            subj, body = special_trigger["build_fn"]()
            ok = any(send_email(r, subj, body) for r in special_trigger["targets"])
            if ok:
                email_state.setdefault(cid, {})
                email_state[cid][alert_key] = "SENT"
                _save_json(EMAIL_STATE_FILE, email_state)
                # For C-1064, do NOT call _update_workflow_stage because the stage
                # is already set by manual action. Only update agent_state Email_Sent flag.
                agent_state = _load_json(AGENT_STATE_FILE)
                if cid in agent_state:
                    agent_state[cid]["Email_Sent"] = True
                    agent_state[cid]["Execution_Status"] = "Email Sent"
                    _save_json(AGENT_STATE_FILE, agent_state)
                trigger_log[cid][alert_key]["status"] = "Completed"
                trigger_log[cid][alert_key]["completed_ts"] = datetime.now(timezone.utc).isoformat()
                fired_this_run[alert_key] = fired_this_run.get(alert_key, 0) + 1
                print(f"C-1064 special workflow mail fired: {alert_key}")
            else:
                trigger_log[cid][alert_key]["status"] = "Failed"
                trigger_log[cid][alert_key]["error"] = "Email send failed"
            _save_json(TRIGGER_LOG_FILE, trigger_log)

    if fired_this_run:
        print(f"Batch done. Fired: {fired_this_run}")
    else:
        print("Batch done. No new triggers (all dispatched or batch_size=0).")

    return fired_this_run


def get_pending_count() -> int:
    """Return number of contracts still awaiting at least one alert."""
    if not os.path.exists(CSV_FILE):
        return 0
    email_state = _load_json(EMAIL_STATE_FILE)
    agent_state = _load_json(AGENT_STATE_FILE)
    pending = 0
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                try:
                    days = int(float(row.get("Days_to_Renewal", -1) or -1))
                except Exception:
                    continue
                if days < 0:
                    continue
                cid = row.get("Contract_ID", "")
                c_state = email_state.get(cid, {})
                try:
                    util = float(str(row.get("Avg_Utilization_Pct", "0")).replace("%", "").strip())
                except Exception:
                    util = 0.0

                needs = False
                if 0 <= days <= 7   and c_state.get("Alert_Critical") != "SENT": needs = True
                if 8 <= days <= 30  and c_state.get("Alert_30") != "SENT":       needs = True
                if 31 <= days <= 90 and c_state.get("Alert_90") != "SENT":       needs = True
                if 91 <= days <= 180 and c_state.get("Alert_180") != "SENT":     needs = True
                if util > 80  and c_state.get("Alert_High_Util") != "SENT":      needs = True
                if util < 70   and c_state.get("Alert_Low_Util") != "SENT":       needs = True
                if cid == "C-1064":
                    c1064_state = agent_state.get(cid, {})
                    c1064_stage = c1064_state.get("Stage")
                    c1064_email_sent = c1064_state.get("Email_Sent", False)
                    if c1064_stage in {"Planning", "Budgeting", "Approval", "Execution", "Closed"} and not c1064_email_sent:
                        needs = True
                if needs:
                    pending += 1
    except Exception as e:
        print(f"WARNING: pending_count error: {e}")
    return pending


# ── Standalone run ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    process(batch_size=3)
