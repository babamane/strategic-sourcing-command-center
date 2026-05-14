import sys
import os
import re
import json
import requests
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import random
import smtplib
from email.mime.text import MIMEText
from flask import render_template
from dotenv import load_dotenv

load_dotenv()


if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

INPUT_FILE = "alerts.xlsx"
OUTPUT_FILE = "output.xlsx"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2:1.5b")

VALID_CLASSES = [
    "ACCEPT_RISK",
    "CONTRACT_REVIEW",
    "VENDOR_AMENDMENT",
    "DISABLE_FEATURE",
    "ADJUST_CONFIGURATIONS",
]

RISK_TYPE_MAP = {
    "Security Advisory": "Security & Vulnerability Risk",
    "Policy Update": "Compliance & Policy Risk",
    "Changelog": "Model & Governance Risk",
    "Feature Release": "Model & Governance Risk",
    "Pricing Update": "Financial Risk",
    "Terms Update": "Legal & Contractual Risk",
}


def get_next_vendor_number():
    if not os.path.exists(INPUT_FILE):
        return 1

    try:
        df = pd.read_excel(INPUT_FILE)

        if df.empty or "vendor" not in df.columns:
            return 1

        numbers = []

        for v in df["vendor"]:
            match = re.search(r"Vendor (\d+)", str(v))
            if match:
                numbers.append(int(match.group(1)))

        return max(numbers) + 1 if numbers else 1

    except:
        return 1


def clean_html(text):
    if pd.isna(text):
        return ""
    return re.sub(r"<.*?>", "", str(text)).strip()


def build_prompt(
    vendor, title, description, action, risk_level, resource_type, business_unit
):
    return f"""
You are a senior enterprise vendor risk analyst.

Analyze the alert deeply and provide a detailed, structured remediation plan.

⚠️ IMPORTANT:
- Be detailed but clear
- Use professional enterprise language
- Do NOT be too short
- Provide practical, actionable insights

Vendor: {vendor}
Alert Title: {title}
Description: {description}
Action Item: {action}
Risk Level: {risk_level}
Type: {resource_type}
Business Unit: {business_unit}

Return ONLY JSON:

{{
  "remedy_type": "one of: CONTRACT_REVIEW, VENDOR_AMENDMENT, ACCEPT_RISK, DISABLE_FEATURE, ADJUST_CONFIGURATIONS",

  "confidence": <integer between 60 and 95>,

  "summary": "Write a detailed explanation (7-8 lines) explaining the risk, impact, and why it matters to the business.",

  "tags": ["<tag1>", "<tag2>", "<tag3>", "<tag4>"],

  "rationale": "Explain in 5-6 lines WHY this remediation is the best choice, including business and technical reasoning.",

  "steps": [
    "Step 1: Detailed actionable step",
    "Step 2: Include technical or operational action",
    "Step 3: Include monitoring or validation step",
    "Step 4: Include stakeholder or compliance step",
    "Step 5: Risk mitigation step",
    "Step 6: Final verification step"
  ],

  "success_criteria": "Write a clear success condition explaining how we know the risk is resolved (2-3 lines).",

  "sla": "1 week"
}}
"""


def call_ollama(prompt):
    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 600},
            },
            timeout=300,
        )
        if res.status_code != 200:
            return None
        return res.json().get("response", "")
    except Exception as e:
        print(f"[ERROR] Ollama request failed: {e}")
        return None


def parse_plan(text):
    if not text:
        return None
    try:
        clean = re.sub(r"```json|```", "", text).strip()
        data = json.loads(clean)
        if data.get("remedy_type") in VALID_CLASSES:
            return data
    except Exception:
        pass

    for cls in VALID_CLASSES:
        if cls in text:
            return {
                "remedy_type": cls,
                "confidence": 60,
                "summary": "Could not fully parse AI response.",
                "tags": [],
                "rationale": "Fallback classification.",
                "steps": ["Manual review required"],
                "success_criteria": "Risk addressed.",
                "sla": "2 weeks",
            }
    return None


# ✅ NEW: ALERT GENERATION
def generate_full_alert():
    prompt = """
You are a vendor risk monitoring system.

Generate ONE realistic vendor alert.

STRICT RULES:
- DO NOT use real company names
- Keep it generic and enterprise-like

Return ONLY JSON:

{
  "vendor": "Vendor",
  "vendor_domain": "vendor-domain.com",
  "alertTitle": "Alert title",
  "alertDescription": "Alert description",
  "risk_level": "high/medium/low",
  "resource_type": "Security/API/Policy",
  "business_unit": "IT Security/Finance/Legal/Finance/Engineering"
}
"""

    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7},
            },
            timeout=120,
        )

        text = res.json().get("response", "")
        clean = re.sub(r"```json|```", "", text).strip()
        data = json.loads(clean)

        # ✅ GET NEXT NUMBER (INSIDE TRY)
        vendor_number = get_next_vendor_number()

        # ✅ ASSIGN VALUES
        data["vendor"] = f"Vendor {vendor_number}"
        data["vendor_id"] = f"V-{1000 + vendor_number}"
        data["vendor_domain"] = f"vendor{vendor_number}.com"

        # ✅ SYSTEM FIELDS
        data["alert_id"] = str(random.randint(100000, 999999))
        data["submittedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return data

    except Exception as e:
        print(f"[ERROR] Alert generation failed: {e}")
        return None


def save_alert_to_excel(alert):
    print("Saving alert:", alert)

    df = pd.DataFrame([alert])

    if os.path.exists(INPUT_FILE):
        existing = pd.read_excel(INPUT_FILE)
        df = pd.concat([df, existing], ignore_index=True)  # ✅ FIX HERE

    df.to_excel(INPUT_FILE, index=False)

    print("Saved to Excel successfully")


def create_jira_ticket(row):
    print("👉 Jira function called")

    jira_base = os.getenv("JIRA_BASE_URL", "")
    url = f"{jira_base}/rest/api/3/issue"

    auth = (
        os.getenv("JIRA_EMAIL", ""),
        os.getenv("JIRA_API_TOKEN", ""),
    )

    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    summary = f"{row['vendor']} - {row['risk_level']} Risk Alert"

    description = f"""
Vendor: {row['vendor']}
Domain: {row['vendor_domain']}

Alert:
{row['alertTitle']}

Description:
{row['alertDescription']}

Remedy:
{row['remedy']}

Summary:
{row.get('summary', '')}

Confidence: {row['confidence']}%
"""

    payload = {
        "fields": {
            "project": {"key": os.getenv("JIRA_PROJECT_KEY", "KAN")},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
            "issuetype": {"name": "Task"},
        }
    }

    try:
        res = requests.post(url, json=payload, headers=headers, auth=auth)

        print("👉 Jira response:", res.status_code)
        print("👉 Jira response body:", res.text)

        if res.status_code == 201:
            issue_key = res.json().get("key")  # ✅ IMPORTANT
            jira_link = f"{os.getenv('JIRA_BASE_URL', '')}/browse/{issue_key}"

            print("✅ Jira ticket created:", jira_link)

            return jira_link  # ✅ RETURN LINK

        else:
            print("❌ Jira failed")
            return None

    except Exception as e:
        print("❌ Jira error:", e)
        return None


# ✅Approved email send
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_approved_email(row):
    sender_email = os.getenv("EMAIL_SENDER", "")
    receiver_email = os.getenv("EMAIL_RECEIVER", "")
    app_password = os.getenv("EMAIL_APP_PASSWORD", "")

    subject = f"✅ Risk Alert Approved - {row.get('vendor')}"

    # ✅ Safe values
    remedy = row.get("remedy") or "Not available"
    summary = row.get("summary") or "Not available"
    rationale = row.get("rationale") or "Not available"
    success = row.get("success_criteria") or "Not available"
    jira_link = row.get("jira_link") or "#"

    # ✅ Steps handling (string → list)
    try:
        steps = json.loads(row.get("steps", "[]"))
    except:
        steps = []

    steps_html = ""
    for i, step in enumerate(steps, 1):
        steps_html += f"<li>{step}</li>"

    # ✅ Risk color
    risk = row.get("risk_level", "").lower()
    color = {"high": "red", "medium": "orange", "low": "green"}.get(risk, "black")

    # ✅ HTML EMAIL
    html_body = f"""
    <html>
    <body style="font-family: Arial; line-height:1.6;">

        <h2 style="color:green;">✅ Risk Alert Approved</h2>

        <p><b>Vendor:</b> {row.get('vendor')}</p>
        <p><b>Vendor ID:</b> {row.get('vendor_id')}</p>
        <p><b>Risk Level:</b> <span style="color:{color}; font-weight:bold;">
            {row.get('risk_level')}
        </span></p>

        <hr>

        <h3>📌 Alert Title</h3>
        <p><b>{row.get('alertTitle')}</b></p>

        <h3>📄 Description</h3>
        <p>{row.get('alertDescription')}</p>

        <h3>🛠 Remedy</h3>
        <p>{remedy}</p>

        <h3>📊 Summary</h3>
        <p>{summary}</p>

        <hr>

        <h3>🧠 Rationale</h3>
        <p>{rationale}</p>

        <h3>📋 Steps</h3>
        <ol>
            {steps_html if steps_html else "<li>No steps available</li>"}
        </ol>

        <h3>✅ Success Criteria</h3>
        <p>{success}</p>

        <hr>

        <h3>🔗 Jira Task</h3>
        <p>
            <a href="{jira_link}" target="_blank">{jira_link}</a>
        </p>

        <hr>

        <p>
        🔗 <b>Dashboard:</b><br>
        <a href="http://localhost:5000">Open Risk Analyzer</a>
        </p>

    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)

        print("✅ Approved Email sent successfully")

    except Exception as e:
        print("❌ Approved Email failed:", e)


# ✅Rejected email send
def send_email_notification(row):
    sender_email = os.getenv("EMAIL_SENDER", "")
    receiver_email = os.getenv("EMAIL_RECEIVER", "")
    app_password = os.getenv("EMAIL_APP_PASSWORD", "")

    subject = f"🚨 Risk Alert Rejected - {row['vendor']}"

    body = f"""
Vendor: {row['vendor']}
Risk Level: {row['risk_level']}

Alert:
{row['alertTitle']}

Description:
{row['alertDescription']}


Dashboard:
http://localhost:5000
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)

        print("✅ Email sent")

    except Exception as e:
        print("❌ Email failed:", e)


# ✅ EXISTING LOADER
def load_alerts():
    file = INPUT_FILE
    if not os.path.exists(file):
        return []

    df = pd.read_excel(file)
    alerts = []

    for i, row in df.iterrows():
        resource_type = clean_html(row.get("resource_type", ""))

        alerts.append(
            {
                "id": clean_html(row.get("alert_id", str(i))),
                "vendor": clean_html(row.get("vendor", f"Vendor {i+1}")),
                "domain": clean_html(row.get("vendor_domain", "")),
                "title": clean_html(row.get("alertTitle", "")),
                "description": clean_html(row.get("alertDescription", "")),
                "action": clean_html(row.get("action_item", "")),
                "risk_level": clean_html(row.get("risk_level", "medium")),
                "resource_type": resource_type,
                "risk_category": RISK_TYPE_MAP.get(resource_type, "General Risk"),
                "business_unit": clean_html(row.get("business_unit", "")),
                "submitted_at": str(row.get("submittedAt", "")),
                "remedy_type": clean_html(row.get("remedy", "")),
                "reason": clean_html(row.get("reason", "")),
                "confidence": (
                    float(row.get("confidence", 0)) if "confidence" in df.columns else 0
                ),
            }
        )

    return alerts


# ── ROUTES ─────────────────────────────────────────────────


# api new dashboard
@app.route("/api/decision", methods=["POST"])
def save_decision():
    data = request.json or {}

    alert_id = data.get("id")
    decision = data.get("decision")
    plan = data.get("plan", {})

    alerts_df = pd.read_excel(INPUT_FILE)
    alert_row = alerts_df[alerts_df["alert_id"] == alert_id]

    if alert_row.empty:
        return jsonify({"error": "Alert not found"}), 404

    alert = alert_row.iloc[0]

    jira_link = ""

    if decision == "approved":
        try:
            combined = {
                **alert.to_dict(),
                "remedy": plan.get("remedy_type"),
                "summary": plan.get("summary"),
                "confidence": plan.get("confidence"),
            }
            jira_link = create_jira_ticket(combined) or ""
        except Exception as e:
            print("❌ Jira failed but continuing:", e)

    row = {
        "alert_id": alert.get("alert_id"),
        "vendor_id": alert.get("vendor_id"),
        "vendor": alert.get("vendor"),
        "vendor_domain": alert.get("vendor_domain"),
        "alertTitle": alert.get("alertTitle"),
        "alertDescription": alert.get("alertDescription"),
        "risk_level": alert.get("risk_level"),
        "resource_type": alert.get("resource_type"),
        "business_unit": alert.get("business_unit"),
        "status": decision,
        "rationale": plan.get("rationale"),
        "steps": json.dumps(plan.get("steps", [])),
        "success_criteria": plan.get("success_criteria"),
        "remedy": plan.get("remedy_type"),
        "summary": plan.get("summary"),
        "confidence": plan.get("confidence"),
        "jira_link": jira_link,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    df = pd.DataFrame([row])
    file = OUTPUT_FILE

    try:
        if os.path.exists(file):
            existing = pd.read_excel(file)
        else:
            existing = pd.DataFrame()

        if not existing.empty and "alert_id" in existing.columns:
            existing = existing[existing["alert_id"] != alert_id]

        final_df = pd.concat([existing, df], ignore_index=True)
        final_df.to_excel(file, index=False)

        if decision == "approved":
            send_approved_email(row)

        if decision == "rejected":
            send_email_notification(row)

    except Exception as e:
        print("❌ ERROR saving decision:", e)
        return jsonify({"error": "failed"}), 500

    return jsonify({"status": "saved"})


@app.route("/")
def dashboard_home():
    return render_template("dashboard.html")


@app.route("/details")
def details():
    alert_id = request.args.get("id")
    return render_template("old_dashboard.html", alert_id=alert_id)


@app.route("/api/alerts")
def get_alerts():
    return jsonify(load_alerts())


@app.route("/old")
def old_dashboard():
    return render_template("old_dashboard.html")


# ✅ NEW: GENERATE ALERT
@app.route("/api/generate-alert", methods=["POST"])
def generate_alert():
    alert = generate_full_alert()

    if not alert:
        return jsonify({"error": "Failed"}), 500

    save_alert_to_excel(alert)
    return jsonify(alert)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    body = request.json or {}
    alert_id = body.get("id", "")

    alerts = load_alerts()
    alert = next((a for a in alerts if a["id"] == alert_id), None)

    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    prompt = build_prompt(
        alert["vendor"],
        alert["title"],
        alert["description"],
        alert["action"],
        alert["risk_level"],
        alert["resource_type"],
        alert["business_unit"],
    )

    raw = call_ollama(prompt)
    plan = parse_plan(raw)

    if not plan:
        return jsonify({"error": "AI analysis failed"}), 500

    return jsonify(plan)


@app.route("/api/status")
def status():
    try:
        res = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
        models = [m["name"] for m in res.json().get("models", [])]
        return jsonify({"ollama": True, "models": models, "selected": MODEL})
    except:
        return jsonify({"ollama": False, "models": [], "selected": MODEL})


@app.route("/api/dashboard")
def dashboard_data():
    data = []

    alerts = pd.read_excel(INPUT_FILE) if os.path.exists(INPUT_FILE) else pd.DataFrame()
    output = (
        pd.read_excel(OUTPUT_FILE) if os.path.exists(OUTPUT_FILE) else pd.DataFrame()
    )

    alerts = alerts.fillna("")
    output = output.fillna("")

    if "alert_id" in alerts.columns:
        alerts["alert_id"] = alerts["alert_id"].astype(str)

    if not output.empty and "alert_id" in output.columns:
        output["alert_id"] = output["alert_id"].astype(str)

    for _, row in alerts.iterrows():
        alert_id = str(row.get("alert_id", ""))

        status = "pending"
        jira_link = ""

        if not output.empty:
            match = output[output["alert_id"] == alert_id]
            if not match.empty:
                latest = match.iloc[-1]
                raw_status = str(latest.get("status", "pending")).lower()

                if raw_status == "approved":
                    status = "Accepted"
                elif raw_status == "rejected":
                    status = "Rejected"
                else:
                    status = "Pending"
                jira_link = latest.get("jira_link", "")

        data.append(
            {
                "id": alert_id,
                "vendor": str(row.get("vendor", "")),
                "vendor_id": str(row.get("vendor_id", "")),
                "alertTitle": str(row.get("alertTitle", "")),
                "risk_level": str(row.get("risk_level", "")),
                "resource_type": str(row.get("resource_type", "")),
                "business_unit": str(row.get("business_unit", "")),
                "status": status,
                "jira_link": jira_link,
                "timestamp": str(row.get("submittedAt", "")),
            }
        )

    return jsonify(data)


if __name__ == "__main__":
    print("=" * 50)
    print("  Vendor Risk Analyzer — Backend")
    print(f"  Model : {MODEL}")
    print(f"  Data  : {INPUT_FILE}")
    print("  URL   : http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, port=5000)
