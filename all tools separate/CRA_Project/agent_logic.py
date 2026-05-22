"""
agent_logic.py — VendorFlow AI / CRA
=====================================
Stateful Contract Renewal Agent.

5-stage gated workflow:
  Planning → Budgeting → Approval → Execution → Closed

State persisted in data/agent_state.json.
Role-based relay emails sent at each stage transition.
"""

import json
import os
import smtplib
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import adk_agent
except Exception:
    adk_agent = None

import pandas as pd

from email_service import _map_vendor_name, CSV_FILE

load_dotenv()

# Enforce Python 3.11 for agent runtime
import sys
# Temporarily disabled for testing on Python 3.14
# if sys.version_info[:2] != (3, 11):
#     sys.stderr.write(f"ERROR: VendorFlow AI agent requires Python 3.11, found {sys.version}\n")
#     raise SystemExit(1)

# ── Paths & credentials ────────────────────────────────────────────────────────
DATA_DIR      = os.getenv("DATA_DIR", "data")
STATE_FILE    = os.path.join(DATA_DIR, "agent_state.json")
BASE_URL      = os.getenv("BASE_URL", "http://localhost:8000")

SMTP_EMAIL    = os.getenv("SMTP_EMAIL",    "your_gmail@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")

ALIAS_EMAIL_MAP = {
    "Procurement Team":   os.getenv("PROCUREMENT_EMAIL", SMTP_EMAIL),
    "Executive Approver": os.getenv("APPROVER_EMAIL",   SMTP_EMAIL),
    "Finance Team":       os.getenv("FINANCE_EMAIL",    SMTP_EMAIL),
}

# ── 5-stage workflow ───────────────────────────────────────────────────────────
WORKFLOW_MAP = {
    "Planning": {
        "actor":       "Procurement Team",
        "action_text": "Start Budgeting",
        "next_state":  "Budgeting",
    },
    "Budgeting": {
        "actor":       "Procurement Team",
        "action_text": "Submit for Approval",
        "next_state":  "Approval",
    },
    "Approval": {
        "actor":       "Executive Approver",
        "action_text": "Authorize Execution",
        "next_state":  "Execution",
    },
    "Execution": {
        "actor":       "Procurement Team",
        "action_text": "Confirm PO Received",
        "next_state":  "Closed",
    },
    "Closed": {
        "actor":       "Procurement Team",
        "action_text": "Archive Workflow",
        "next_state":  "Archived",
    },
}

_SMTP_PLACEHOLDERS = {
    "your_gmail@gmail.com",
    "your_app_password",
    "##__YOUR_GMAIL_ADDRESS__##",
    "##__YOUR_GMAIL_APP_PASSWORD__##",
}

# Stage → Node labels for dashboard visibility
STAGE_NODES = {
    "Planning":  ["Planning", "Budgeting", "Approval", "Execution", "Closed"],
    "Budgeting": ["Planning", "Budgeting", "Approval", "Execution", "Closed"],
    "Approval":  ["Planning", "Budgeting", "Approval", "Execution", "Closed"],
    "Execution": ["Planning", "Budgeting", "Approval", "Execution", "Closed"],
    "Closed":    ["Planning", "Budgeting", "Approval", "Execution", "Closed"],
}


class ContractAgent:
    """Stateful agent that orchestrates the CRA 5-stage workflow."""

    def __init__(self):
        self.load_state()

    # ── Persistence ────────────────────────────────────────────────────────────

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
                return
            except Exception:
                pass
        self.state = {}

    def save_state(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=4)

    # ── State helpers ──────────────────────────────────────────────────────────

    def get_contract_state(self, contract_id: str, default_stage: str = "Planning") -> dict:
        self.load_state()
        default_actor = WORKFLOW_MAP.get(default_stage, {}).get("actor", "Procurement Team")
        return self.state.get(
            contract_id,
            {"Stage": default_stage, "Pending_With": default_actor, "Email_Sent": False,
             "Execution_Status": "Pending", "Escalated": False},
        )

    def call_tool_update_stage(self, contract_id: str, new_stage: str):
        """Advance contract to new stage and reset Email_Sent."""
        self.load_state()
        actor = WORKFLOW_MAP.get(new_stage, {}).get("actor", "Completed")
        existing = self.state.get(contract_id, {})
        previous_stage = existing.get("Stage", "Planning")
        stage_history = existing.get("Stage_History", [])
        
        # Only add to history if stage is actually changing
        if previous_stage != new_stage:
            stage_history.append({
                "from": previous_stage,
                "to": new_stage,
                "trigger": f"Manual Action to {new_stage}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Determine alert key for this stage
        alert_key = {
            "Planning": "Alert_180",
            "Budgeting": "Alert_90",
            "Approval": "Alert_30",
            "Execution": "Alert_Critical",
            "Closed": "Alert_Closed"
        }.get(new_stage, "")
        
        self.state[contract_id] = {
            "Stage": new_stage,
            "Previous_Stage": previous_stage,
            "Pending_With": actor,
            "Email_Sent": False,  # Reset to False so next lifecycle email can be sent
            "Execution_Status": "Running",
            "Escalated": existing.get("Escalated", False),
            "Stage_History": stage_history,
            "Last_Trigger": alert_key,
            "Last_Trigger_Timestamp": datetime.now(timezone.utc).isoformat(),
            "Vendor": existing.get("Vendor", "Unknown"),
            "Days_to_Renewal": existing.get("Days_to_Renewal", 180),
            "Avg_Utilization_Pct": existing.get("Avg_Utilization_Pct", 0.0),
        }
        self.save_state()
        
        # Also clear the email_state for the new stage's alert key to ensure consistency
        # This ensures the next refresh will send the email for the new stage
        email_state_file = os.path.join(DATA_DIR, "email_state.json")
        try:
            if os.path.exists(email_state_file):
                with open(email_state_file, "r", encoding="utf-8") as f:
                    email_state = json.load(f)
            else:
                email_state = {}
            
            if alert_key and contract_id in email_state:
                # Clear the alert key for the new stage so it will be sent
                email_state[contract_id][alert_key] = ""
                with open(email_state_file, "w", encoding="utf-8") as f:
                    json.dump(email_state, f, indent=4)
                print(f"[Agent] Cleared email_state for {contract_id}: {alert_key} (stage transition to {new_stage})")
        except Exception as e:
            print(f"[Agent] Failed to clear email_state: {e}")

    # ── Agent loop ─────────────────────────────────────────────────────────────

    def observe(self, payload: dict) -> str:
        return payload.get("contract_id") or "C-1064"

    def plan(self, current_stage: str) -> dict | None:
        return WORKFLOW_MAP.get(current_stage)

    async def execute_agent_loop(self, payload: dict):
        contract_id = self.observe(payload)
        current_info  = self.get_contract_state(contract_id, "Planning")
        current_stage = current_info["Stage"]
        email_sent    = current_info.get("Email_Sent", False)
        next_step     = self.plan(current_stage)

        if next_step and not email_sent:
            print(f"[Agent] {contract_id} | stage={current_stage} | action={next_step['action_text']}")
            metrics = self._load_metrics(contract_id)

            # ADK intelligence on Planning stage
            if current_stage == "Planning" and adk_agent is not None:
                sample_alert = (
                    f"Contract ID: {contract_id}\n"
                    f"Vendor: {metrics.get('Vendor', 'Unknown')}\n"
                    f"Days Remaining: {metrics.get('Days_Remaining', '180')}"
                )
                try:
                    adk_agent.check_connection()
                except Exception:
                    pass
                try:
                    asyncio.create_task(adk_agent.run_agent(sample_alert))
                except Exception as e:
                    print(f"[Agent] ADK error: {e}")

            sent = await self.call_tool_send_relay_email(contract_id, current_stage, next_step, metrics)
            if sent:
                current_info["Email_Sent"]       = True
                current_info["Execution_Status"] = "Email Sent"
                self.state[contract_id]           = current_info
                self.save_state()
                # Also update email_state.json for C-1064 lifecycle synchronization
                self._update_email_state_for_lifecycle(contract_id, current_stage)
            else:
                print(f"[Agent] Email failed for {contract_id} — will retry.")
        else:
            if email_sent:
                print(f"[Agent] {contract_id} | email already sent for '{current_stage}' — skipping.")
            else:
                print(f"[Agent] {contract_id} | stage '{current_stage}' has no further action.")

    def _update_email_state_for_lifecycle(self, contract_id: str, stage: str):
        """Update email_state.json to mark the lifecycle alert as sent."""
        email_state_file = os.path.join(DATA_DIR, "email_state.json")
        try:
            if os.path.exists(email_state_file):
                with open(email_state_file, "r", encoding="utf-8") as f:
                    email_state = json.load(f)
            else:
                email_state = {}
            
            # Map stage to alert key
            alert_key = {
                "Planning": "Alert_180",
                "Budgeting": "Alert_90",
                "Approval": "Alert_30",
                "Execution": "Alert_Critical",
                "Closed": "Alert_Closed"
            }.get(stage, "")
            
            if alert_key:
                email_state.setdefault(contract_id, {})
                email_state[contract_id][alert_key] = "SENT"
                with open(email_state_file, "w", encoding="utf-8") as f:
                    json.dump(email_state, f, indent=4)
                print(f"[Agent] Updated email_state for {contract_id}: {alert_key} = SENT")
        except Exception as e:
            print(f"[Agent] Failed to update email_state: {e}")

    # ── Metrics loader ─────────────────────────────────────────────────────────

    def _load_metrics(self, contract_id: str) -> dict:
        metrics = {
            "Vendor":           "Unknown",
            "License_Type":     "Unknown",
            "Renewal_Month":    "Unknown",
            "Days_Remaining":   "Unknown",
            "Licenses_Used":    "0",
            "Licenses_Total":   "0",
            "Utilization_Rate": "0.00%",
            "Previous_Budget":  "0.00",
            "Execution_Date":   "N/A",
        }
        try:
            if os.path.exists(CSV_FILE):
                df  = pd.read_csv(CSV_FILE)
                row = df[df["Contract_ID"] == contract_id]
                if not row.empty:
                    r = row.iloc[0]
                    orig_vendor = r.get("Vendor", "")
                    metrics["Vendor"]        = _map_vendor_name(str(orig_vendor), contract_id)
                    metrics["License_Type"]  = str(r.get("License_Type", "Unknown"))
                    metrics["Renewal_Month"] = str(r.get("End_Date", "Unknown"))
                    metrics["Days_Remaining"]= str(r.get("Days_to_Renewal", "Unknown")) + " days"
                    metrics["Licenses_Used"] = f"{int(r.get('Active_Users', 0)):,}"
                    metrics["Licenses_Total"]= f"{int(r.get('Total_Users',  0)):,}"
                    try:
                        util = float(str(r.get("Avg_Utilization_Pct", "0")).replace("%", "").strip())
                        metrics["Utilization_Rate"] = f"{util:.2f}%"
                    except Exception:
                        metrics["Utilization_Rate"] = str(r.get("Avg_Utilization_Pct", "0.00%"))
                    metrics["Previous_Budget"] = f"{float(r.get('Total_Annual_Budget_USD', 0)):,.2f}"
        except Exception as e:
            print(f"[Agent] Could not load metrics for {contract_id}: {e}")
        return metrics

    # ── Relay email ────────────────────────────────────────────────────────────

    async def call_tool_send_relay_email(
        self,
        contract_id: str,
        current_stage: str,
        next_step: dict,
        contract_metrics: dict,
    ) -> bool:

        recipient_alias = next_step["actor"]
        recipient_email = ALIAS_EMAIL_MAP.get(recipient_alias, SMTP_EMAIL)
        action_url      = f"{BASE_URL}/action/{contract_id}/{next_step['next_state']}"
        report_link     = (
            "https://agivantechnologiespvtltd-my.sharepoint.com/:w:/g/personal/"
            "pallanti_vatsal_agivant_com/IQB-Ndnt9mr0R4NtdGuEXG8iAeGtQOoE4nLx2ctS7Xykgp4?e=nbdTgX"
        )

        if current_stage == "Planning":
            stage_title   = "180-Day Renewal Planning Alert"
            stage_message = (
                "The contract is 180 days from expiration. An AI Intelligence Report has been "
                "generated. Please review the utilization and budget baseline below."
            )
            dynamic_sections = f"""
<div class="section-title">📊 Current Utilization</div>
<table>
  <tr><td>Licenses Used</td>
      <td><span class="hi">{contract_metrics.get('Licenses_Used','0')}</span> of
          <span class="hi">{contract_metrics.get('Licenses_Total','0')}</span></td></tr>
  <tr><td>Utilization Rate</td>
      <td class="hi">{contract_metrics.get('Utilization_Rate','0.00%')}</td></tr>
  <tr><td>Vendor Performance</td>
      <td class="hi" style="color:#059669">4.2 / 5.0 (Good)</td></tr>
</table>
<div class="section-title">💰 Financial Baseline</div>
<table>
  <tr><td>Previous Annual Budget</td>
      <td>${contract_metrics.get('Previous_Budget','0.00')}</td></tr>
</table>"""

        elif current_stage == "Budgeting":
            stage_title   = "Budget Submission Required — 90-Day Escalation"
            stage_message = (
                "The contract is 90 days from renewal. Finance stakeholders have been escalated. "
                "Please review the AI recommendations and submit an optimized budget."
            )
            report_link = (
                "https://agivantechnologiespvtltd-my.sharepoint.com/:w:/g/personal/"
                "pallanti_vatsal_agivant_com/IQDbqetbKrNkTq3mJGx3EiWvAaPwqprx8TBlPjy_MA06hjs?e=qe50kC"
            )
            dynamic_sections = f"""
<div class="section-title">📈 AI Optimization Recommendations</div>
<table>
  <tr><td>Current Utilization</td><td>{contract_metrics.get('Utilization_Rate','0.00%')}</td></tr>
  <tr><td>Recommended Seats</td><td class="hi">Reduce by ~18% based on usage trends</td></tr>
  <tr><td>Projected Growth</td><td>+5% YoY expected</td></tr>
</table>
<div class="section-title">💰 Budget Proposal</div>
<table>
  <tr><td>Previous Budget</td>
      <td style="text-decoration:line-through;color:#9ca3af">${contract_metrics.get('Previous_Budget','0.00')}</td></tr>
  <tr><td>Optimised Renewal Estimate</td><td class="hi" style="color:#059669">$2,300,000.00</td></tr>
  <tr><td>Estimated Savings</td><td class="hi" style="color:#059669">$549,052.00</td></tr>
</table>"""

        elif current_stage == "Approval":
            stage_title   = "Executive Approval Required — 30-Day Critical Window"
            stage_message = (
                "30 days to renewal. Executive escalation initiated. Please review the financial "
                "request and authorize contract renewal execution."
            )
            dynamic_sections = """
<div class="section-title">⚖️ Executive Summary</div>
<table>
  <tr><td>Requested Budget</td><td class="hi" style="color:#111827">$2,300,000.00</td></tr>
  <tr><td>Variance vs Previous</td><td class="hi" style="color:#059669">−19.2% (Cost Savings)</td></tr>
  <tr><td>Strategic Value</td><td>High — Core Infrastructure</td></tr>
</table>
<div class="section-title">🛡️ Risk Assessment</div>
<table>
  <tr><td>Vendor Risk</td><td style="color:#059669">Low</td></tr>
  <tr><td>Legal Review</td><td style="color:#059669">Cleared — Standard Terms</td></tr>
</table>"""

        elif current_stage == "Execution":
            stage_title   = "Contract Execution Pending"
            stage_message = (
                "The renewal budget is approved. Please finalise the paperwork and send the "
                "Purchase Order to the vendor."
            )
            vendor_email = (
                f"renewals@{str(contract_metrics.get('Vendor','vendor')).lower().replace(' ','')}.com"
            )
            dynamic_sections = f"""
<div class="section-title">📝 Execution Details</div>
<table>
  <tr><td>Approved Amount</td><td class="hi">${contract_metrics.get('Previous_Budget','2,300,000.00')}</td></tr>
  <tr><td>Purchase Order #</td><td class="hi">PO-2026-8910</td></tr>
  <tr><td>Vendor Email</td><td>{vendor_email}</td></tr>
  <tr><td>Execution Deadline</td><td class="hi" style="color:#dc2626">30 days from today</td></tr>
</table>"""

        elif current_stage == "Closed":
            stage_title   = "PO Received & Vendor Acknowledgment"
            stage_message = (
                "We have received confirmation from the vendor acknowledging the Purchase Order. "
                "The renewal process is finalised."
            )
            dynamic_sections = f"""
<div style="background:#f0fdf4;border:1px solid #bbf7d0;padding:12px;border-radius:6px;
            font-size:14px;color:#166534;margin-bottom:20px">
  <strong>Vendor Message:</strong>
  "We have received PO-2026-8910 and confirmed the renewal of your licences for the next term.
  Thank you for your continued partnership."
</div>
<div class="section-title">🧾 Transaction Receipt</div>
<table style="border:1px solid #eaeaea;background:#fafafa">
  <tr><td>Receipt Number</td><td class="hi">RCP-992834-X</td></tr>
  <tr><td>Amount Paid</td><td class="hi">$2,300,000.00</td></tr>
  <tr><td>Status</td><td style="color:#059669;font-weight:700">PAID & CLOSED</td></tr>
</table>
<div class="section-title">✅ Completion Summary</div>
<table>
  <tr><td>Final Status</td><td class="hi" style="color:#059669">Successfully Renewed</td></tr>
  <tr><td>Next Renewal Date</td><td class="hi">12 months from today</td></tr>
</table>"""

        else:
            stage_title      = f"Action Required: {current_stage}"
            stage_message    = "Please process the next step for this contract."
            dynamic_sections = ""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body  {{ font-family:'Helvetica Neue',Helvetica,Arial,sans-serif; color:#333; margin:0; }}
  .wrap {{ max-width:620px; margin:0 auto; padding:28px; }}
  .hdr  {{ border-bottom:1px solid #eaeaea; margin-bottom:20px; padding-bottom:16px; }}
  .hdr h2   {{ margin:0 0 6px; color:#1f2937; font-size:20px; font-weight:600; }}
  .badge    {{ display:inline-block; background:#1d4ed8; color:#fff; font-size:11px;
               padding:3px 10px; border-radius:12px; font-weight:700; letter-spacing:.4px; }}
  .alert    {{ background:#eff6ff; border-left:4px solid #3b82f6; padding:14px;
               margin-bottom:20px; border-radius:0 6px 6px 0; color:#1e40af; font-size:14px; }}
  table     {{ width:100%; border-collapse:collapse; margin-bottom:28px; }}
  td        {{ padding:9px 0; border-bottom:1px solid #f3f4f6; }}
  td:first-child {{ font-weight:600; color:#6b7280; width:42%; }}
  .section-title {{ font-size:15px; font-weight:700; margin:28px 0 12px;
                    border-bottom:2px solid #f3f4f6; padding-bottom:6px; color:#374151; }}
  .hi       {{ font-weight:700; color:#111827; }}
  .btn      {{ display:inline-block; background:#1d4ed8; color:#fff !important;
               text-decoration:none; padding:13px 28px; border-radius:7px;
               font-weight:700; font-size:15px; font-family:inherit; }}
  .foot     {{ font-size:11px; color:#9ca3af; margin-top:32px;
               border-top:1px solid #f3f4f6; padding-top:14px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <span class="badge">VendorFlow AI · CRA</span>
    <h2 style="margin-top:12px">{stage_title}</h2>
  </div>
  <div class="alert">{stage_message}</div>
  <table>
    <tr><td>Contract ID</td>    <td class="hi">{contract_id}</td></tr>
    <tr><td>Vendor</td>         <td>{contract_metrics.get('Vendor','Unknown')}</td></tr>
    <tr><td>License Type</td>   <td>{contract_metrics.get('License_Type','Unknown')}</td></tr>
    <tr><td>Renewal Month</td>  <td>{contract_metrics.get('Renewal_Month','Unknown')}</td></tr>
    <tr><td>Days Remaining</td> <td class="hi" style="color:#dc2626">{contract_metrics.get('Days_Remaining','N/A')}</td></tr>
  </table>
  {dynamic_sections}
  <div class="section-title">📄 AI Contract Intelligence Report</div>
  <p style="color:#4b5563;font-size:14px;margin-bottom:16px">
    The full AI-generated summary for <strong>{contract_id}</strong> is available below.
  </p>
  <a href="{report_link}" style="color:#2563eb;font-weight:700;text-decoration:underline"
     target="_blank">View Summarised Contract Report</a>
  <div style="margin-top:36px">
    <a href="{action_url}" class="btn" target="_blank">
      {next_step['action_text']} — {contract_id}
    </a>
  </div>
  <div class="foot">
    Automated by VendorFlow AI · Contract Renewal Agent &nbsp;|&nbsp;
    Pending with: <strong>{recipient_alias}</strong>
  </div>
</div>
</body>
</html>"""

        msg             = MIMEMultipart("alternative")
        msg["Subject"]  = f"Action Required: {contract_id} — Phase: {current_stage}"
        msg["From"]     = SMTP_EMAIL
        msg["To"]       = recipient_email
        msg.attach(MIMEText(html_content, "html"))

        if (
            SMTP_EMAIL
            and SMTP_PASSWORD
            and SMTP_EMAIL    not in _SMTP_PLACEHOLDERS
            and SMTP_PASSWORD not in _SMTP_PLACEHOLDERS
        ):
            try:
                server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, recipient_email, msg.as_string())
                server.quit()
                print(f"[Agent] Email sent to {recipient_email} for '{next_step['action_text']}'")
                return True
            except Exception as e:
                print(f"[Agent] SMTP error: {e}")
                return False
        else:
            print(f"[Agent] SIM send to {recipient_email} | {msg['Subject']}")
            print(f"[Agent] Action URL: {action_url}")
            return True
