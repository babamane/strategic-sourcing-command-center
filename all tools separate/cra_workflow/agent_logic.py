import json
import os
import smtplib
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "data")
STATE_FILE = os.path.join(DATA_DIR, "agent_state.json")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Authentication
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "your_gmail@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")

ALIAS_EMAIL_MAP = {
    "Procurement Team": os.getenv("PROCUREMENT_EMAIL", SMTP_EMAIL),
    "Executive Approver": os.getenv("APPROVER_EMAIL", SMTP_EMAIL)
}

WORKFLOW_MAP = {
    "Planning": {
        "actor": "Procurement Team",
        "action_text": "Start Budgeting",
        "next_state": "Budgeting"
    },
    "Budgeting": {
        "actor": "Procurement Team",
        "action_text": "Submit for Approval",
        "next_state": "Approval"
    },
    "Approval": {
        "actor": "Executive Approver",
        "action_text": "Authorize Execution",
        "next_state": "Execution"
    },
    "Execution": {
        "actor": "Procurement Team",
        "action_text": "Confirm PO Received",
        "next_state": "Closed"
    },
    "Closed": {
        "actor": "Procurement Team",
        "action_text": "Archive Workflow",
        "next_state": "Archived"
    }
}

class ContractAgent:
    def __init__(self):
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    self.state = json.load(f)
            except Exception:
                self.state = {}
        else:
            self.state = {}

    def save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=4)

    def get_contract_state(self, contract_id: str, default_stage="Planning"):
        """Returns the current state dictionary for the contract."""
        self.load_state() # Reload to pick up manual edits
        return self.state.get(contract_id, {"Stage": default_stage, "Pending_With": WORKFLOW_MAP.get(default_stage, {}).get("actor", "Closed"), "Email_Sent": False})

    def observe(self, payload: dict):
        """
        Parses incoming Webhook alert.
        We expect the webhook to give us a Contract ID.
        """
        # In a real system, you'd parse the base64 email body via Pub/Sub payload.
        contract_id = payload.get("contract_id", "C-1064")
        return contract_id

    def plan(self, current_stage: str):
        """
        Agent decides what action is required next based on the workflow state.
        """
        return WORKFLOW_MAP.get(current_stage, None)

    def call_tool_update_stage(self, contract_id: str, new_stage: str):
        """Updates the contract phase persistently in memory via json."""
        self.load_state() # Reload to pick up current state before modification
        actor = WORKFLOW_MAP.get(new_stage, {}).get("actor", "None") if new_stage in WORKFLOW_MAP else "Completed"
        self.state[contract_id] = {
            "Stage": new_stage,
            "Pending_With": actor,
            "Email_Sent": False
        }
        self.save_state()

    def call_tool_send_relay_email(self, contract_id: str, current_stage: str, next_step: dict, contract_metrics: dict):
        """
        Sends an HTML email acting as an orchestrator relay.
        Features a stylish box button for the action.
        """
        recipient_username = next_step['actor']
        # Route email based on the alias mapped to the actual email address
        recipient_email = ALIAS_EMAIL_MAP.get(recipient_username, SMTP_EMAIL)

        action_url = f"{BASE_URL}/action/{contract_id}/{next_step['next_state']}"
        report_link = "https://agivantechnologiespvtltd-my.sharepoint.com/:w:/g/personal/pallanti_vatsal_agivant_com/IQB-Ndnt9mr0R4NtdGuEXG8iAeGtQOoE4nLx2ctS7Xykgp4?e=nbdTgX"

        if current_stage == "Planning":
            stage_title = "180-Day Renewal Planning Alert"
            stage_message = "The contract is 180 days from expiration. Please review the vendor performance and begin the initial budgeting estimates."
            dynamic_sections = f"""
                    <div class="section-title">📊 Current Utilization</div>
                    <table>
                        <tr><td>Licenses Used</td><td><span class="highlight">{contract_metrics.get('Licenses_Used', '0')}</span> out of <span class="highlight">{contract_metrics.get('Licenses_Total', '0')}</span> total licenses</td></tr>
                        <tr><td>Utilization Rate</td><td class="highlight">{contract_metrics.get('Utilization_Rate', '0.00%')}</td></tr>
                        <tr><td>Vendor Performance</td><td class="highlight" style="color: #059669;">4.2 / 5.0 (Good)</td></tr>
                    </table>

                    <div class="section-title">💰 Financial Baseline</div>
                    <table>
                        <tr><td>Previous Annual Budget</td><td>${contract_metrics.get('Previous_Budget', '0.00')}</td></tr>
                    </table>
            """
        elif current_stage == "Budgeting":
            stage_title = "Budget Submission Required"
            stage_message = "The initial planning is complete. Please review the AI recommendations below and submit the optimized budget for approval."
            report_link = "https://agivantechnologiespvtltd-my.sharepoint.com/:w:/g/personal/pallanti_vatsal_agivant_com/IQDbqetbKrNkTq3mJGx3EiWvAaPwqprx8TBlPjy_MA06hjs?e=qe50kC"
            dynamic_sections = f"""
                    <div class="section-title">📈 AI Optimization Recommendations</div>
                    <table>
                        <tr><td>Current Utilization</td><td>{contract_metrics.get('Utilization_Rate', '0.00%')}</td></tr>
                        <tr><td>Recommended Licenses</td><td class="highlight">20,000 (Reduction of 4,571)</td></tr>
                        <tr><td>Projected Growth</td><td>+5% YoY expected</td></tr>
                    </table>

                    <div class="section-title">💰 Budget Proposal</div>
                    <table>
                        <tr><td>Previous Budget</td><td style="text-decoration: line-through; color: #6b7280;">${contract_metrics.get('Previous_Budget', '0.00')}</td></tr>
                        <tr><td>Optimized Renewal Estimate</td><td class="highlight" style="color: #059669;">$2,300,000.00</td></tr>
                        <tr><td>Estimated Savings</td><td class="highlight" style="color: #059669;">$549,052.00</td></tr>
                    </table>
            """
        elif current_stage == "Approval":
            stage_title = "Executive Approval Required"
            stage_message = "The optimized budget has been submitted. Please review the financial requests and authorize the contract renewal execution."
            dynamic_sections = f"""
                    <div class="section-title">⚖️ Executive Summary</div>
                    <table>
                        <tr><td>Requested Budget</td><td class="highlight" style="color: #111827;">$2,300,000.00</td></tr>
                        <tr><td>Variance vs Previous</td><td class="highlight" style="color: #059669;">-19.2% (Cost Savings)</td></tr>
                        <tr><td>Strategic Value</td><td>High - Core Infrastructure</td></tr>
                    </table>

                    <div class="section-title">🛡️ Risk Assessment</div>
                    <table>
                        <tr><td>Vendor Risk</td><td style="color: #059669;">Low</td></tr>
                        <tr><td>Legal Review</td><td style="color: #059669;">Cleared - Standard Terms</td></tr>
                    </table>
            """
        elif current_stage == "Execution":
            stage_title = "Contract Execution Pending"
            stage_message = "The contract renewal budget is fully approved. Please finalize the paperwork and send the Purchase Order to the vendor."
            dynamic_sections = f"""
                    <div class="section-title">📝 Execution Details</div>
                    <table>
                        <tr><td>Approved Amount</td><td class="highlight">$2,300,000.00</td></tr>
                        <tr><td>Purchase Order #</td><td class="highlight">PO-2026-8910</td></tr>
                        <tr><td>Vendor Email</td><td>renewals@vendor2.com</td></tr>
                        <tr><td>Execution Deadline</td><td class="highlight" style="color: #dc2626;">May 15, 2026</td></tr>
                    </table>
            """
        elif current_stage == "Closed":
            stage_title = "PO Received & Vendor Acknowledgment"
            stage_message = "We have received a confirmation email back from the vendor acknowledging the Purchase Order. The renewal process is now finalized."
            dynamic_sections = f"""
                    <div class="section-title">📩 Vendor Acknowledgment Details</div>
                    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 6px; font-size: 14px; color: #166534; margin-bottom: 20px;">
                        <strong>Vendor Message:</strong> "We have received PO-2026-8910 and confirmed the renewal of your licenses for the next term. Thank you for your continued partnership."
                    </div>

                    <div class="section-title">🧾 Transaction Receipt (Dummy)</div>
                    <table style="border: 1px solid #eaeaea; background-color: #fafafa;">
                        <tr><td>Receipt Number</td><td class="highlight">RCP-992834-X</td></tr>
                        <tr><td>Transaction Date</td><td>{contract_metrics.get('Execution_Date', 'April 27, 2026')}</td></tr>
                        <tr><td>Amount Paid</td><td class="highlight">$2,300,000.00</td></tr>
                        <tr><td>Payment Method</td><td>Corporate Wire Transfer</td></tr>
                        <tr><td>Status</td><td style="color: #059669; font-weight: bold;">PAID & CLOSED</td></tr>
                    </table>

                    <div class="section-title">✅ Completion Summary</div>
                    <table>
                        <tr><td>Final Status</td><td class="highlight" style="color: #059669;">Successfully Renewed</td></tr>
                        <tr><td>Next Renewal Date</td><td class="highlight">April 27, 2027</td></tr>
                    </table>
            """
        else:
            stage_title = f"Action Required: {current_stage}"
            stage_message = "Please process the next step for this contract."
            dynamic_sections = ""

        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ padding-bottom: 20px; border-bottom: 1px solid #eaeaea; margin-bottom: 20px; }}
                    .header h2 {{ margin: 0; color: #1f2937; margin-bottom: 15px; font-weight: 500; }}
                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
                    td {{ padding: 10px 0; border-bottom: 1px solid #f3f4f6; }}
                    td:first-child {{ font-weight: 500; color: #6b7280; width: 40%; }}
                    .section-title {{ font-size: 16px; font-weight: bold; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid #eaeaea; padding-bottom: 5px; }}
                    
                    /* The box button requested by the user */
                    .action-button-container {{ text-align: left; margin: 30px 0; }}
                    .btn-primary {{
                        display: inline-block;
                        background-color: #1d4ed8;
                        color: white !important;
                        text-decoration: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-family: inherit;
                        border: none;
                    }}
                    .btn-primary:hover {{ background-color: #1e40af; cursor: pointer; }}
                    
                    .report-link {{ font-size: 13px; color: #6b7280; margin-top: 10px; display: inline-block; text-decoration: none; }}
                    .highlight {{ font-weight: bold; color: #111827; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{stage_title}</h2>
                        <div style="background-color: #f9fafb; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 15px; border-radius: 0 4px 4px 0; color: #4b5563;">
                            {stage_message}
                        </div>
                        <table>
                            <tr><td>Contract ID</td><td class="highlight">{contract_id}</td></tr>
                            <tr><td>Vendor</td><td>{contract_metrics.get('Vendor', 'Unknown')}</td></tr>
                            <tr><td>License Type</td><td>{contract_metrics.get('License_Type', 'Unknown')}</td></tr>
                            <tr><td>Renewal Month</td><td>{contract_metrics.get('Renewal_Month', 'Unknown')}</td></tr>
                            <tr><td>Days Remaining</td><td class="highlight">{contract_metrics.get('Days_Remaining', '180 days')}</td></tr>
                        </table>
                    </div>

                    {dynamic_sections}

                    <div class="section-title">📄 AI Contract Intelligence Report</div>
                    <p style="color: #4b5563; font-size: 14px; margin-bottom: 20px;">
                        The full AI-generated summary report for <strong>{contract_id}</strong> is available below.
                    </p>
                    <a href="{report_link}" style="color: #2563eb; font-weight: bold; text-decoration: underline;" target="_blank">View Summarized Contract Report</a>
                    
                    <div class="action-button-container" style="margin-top: 40px;">
                        <a href="{action_url}" class="btn-primary" target="_blank">
                            {next_step['action_text']} — {contract_id}
                        </a>
                        <br/>
                        <span class="report-link">Automated Sequence via Anti Gravity Orchestrator</span>
                    </div>
                </div>
            </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Action Required: Contract {contract_id} - Phase: {current_stage}"
        msg["From"] = SMTP_EMAIL
        msg["To"] = recipient_email

        html_mime = MIMEText(html_content, "html")
        msg.attach(html_mime)

        # Check if credentials are provided and not just placeholder defaults
        placeholders = ["your_gmail@gmail.com", "your_app_password", "##__YOUR_GMAIL_ADDRESS__##", "##__YOUR_GMAIL_APP_PASSWORD__##"]
        if SMTP_EMAIL and SMTP_PASSWORD and SMTP_EMAIL not in placeholders and SMTP_PASSWORD not in placeholders:
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, recipient_email, msg.as_string())
                server.quit()
                print(f"Agent Action: Email dispatched to {recipient_email} for action '{next_step['action_text']}'")
                return True
            except Exception as e:
                print(f"❌ SMTP Error: {str(e)}")
                return False
        else:
            print("⚠️ SIMULATION MODE: SMTP credentials missing or using placeholders in .env")
            print(f"   Recipient: {recipient_email}")
            print(f"   Subject: {msg['Subject']}")
            print(f"   Action URL: {action_url}")
            return True # In simulation, we treat it as 'sent' for flow purposes, but maybe we shouldn't? 
            # Actually, let's return False so the user can see it's not working and fix it.
            # But wait, if we return False, it will keep retrying every webhook. 
            # Let's return True for simulation so it doesn't spam, but print a clear warning.
            # Actually, the user wants it to work. Let's return False if it's simulation but they are expecting a mail.
            # Better: let's return True if it's simulation to avoid infinite loops, 
            # but the primary issue is it failing silently.

    async def execute_agent_loop(self, payload: dict):
        contract_id = self.observe(payload)
        
        # Determine the current stage in our agent state. 
        # Default starting point acts as the initial state trigger.
        current_state_info = self.get_contract_state(contract_id, "Planning")
        current_stage = current_state_info["Stage"]
        email_sent = current_state_info.get("Email_Sent", False)
        
        # Agent reasoning logic
        next_step = self.plan(current_stage)
        
        if next_step and not email_sent:
            print(f"[Agent Reasoning] Determined Action: '{next_step['action_text']}'. Awaiting interaction...")
            
            # Simulated dummy metrics for email
            metrics = {
                "Vendor": "Vendor 2",
                "License_Type": "License 2",
                "Renewal_Month": "June 2026",
                "Days_Remaining": "180 days",
                "Licenses_Used": "18,151",
                "Licenses_Total": "24,571",
                "Utilization_Rate": "73.90%",
                "Previous_Budget": "2,849,052.00"
            }
            
            sent_success = self.call_tool_send_relay_email(contract_id, current_stage, next_step, metrics)
            if sent_success:
                current_state_info["Email_Sent"] = True
                self.state[contract_id] = current_state_info
                self.save_state()
            else:
                print(f"[Agent Reasoning] Failed to send email for {contract_id}. Will retry on next trigger.")
        else:
            if email_sent:
                print(f"[Agent Reasoning] Email already sent for phase '{current_stage}'. Ignoring repeater webhook.")
            else:
                print(f"[Agent Reasoning] Contract {contract_id} is in phase '{current_stage}'. No further action needed.")
