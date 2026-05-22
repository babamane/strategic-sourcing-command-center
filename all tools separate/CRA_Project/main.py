"""
main.py — VendorFlow AI / CRA FastAPI Backend
================================================
Endpoints:
  POST /webhook                    — Gmail Pub/Sub push notification
  GET  /action/{id}/{stage}        — Single-click stage transition from email buttons
  GET  /status                     — Live JSON snapshot for dashboard polling
  GET  /health                     — Liveness probe
  POST /refresh                    — Controlled batch trigger execution (2-3 at a time)
  GET  /pending                    — Count of pending triggers
"""

import os
import json
import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Enforce Python 3.11 for backend execution
import sys
# Temporarily disabled for testing on Python 3.14
# if sys.version_info[:2] != (3, 11):
#     sys.stderr.write(f"ERROR: VendorFlow AI backend requires Python 3.11, found {sys.version}\n")
#     raise SystemExit(1)

from agent_logic import ContractAgent, STATE_FILE
from email_service import (
    CSV_FILE, TRIGGER_LOG_FILE, EMAIL_STATE_FILE,
    process as email_process, get_pending_count,
    _load_json, _save_json, AGENT_STATE_FILE,
)
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="VendorFlow AI — Contract Renewal Agent",
    description="CRA orchestration backend: triggers, stage transitions, status API.",
    version="3.0.0",
)

agent = ContractAgent()


def _load_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _pick_contracts(df: pd.DataFrame, low: int, high: int, limit: int) -> list:
    mask = (df["Days_to_Renewal"] > low) & (df["Days_to_Renewal"] <= high)
    return df[mask]["Contract_ID"].dropna().tolist()[:limit]


# ── Startup ────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """
    On startup: load existing state (do NOT clear) and trigger a small
    initial batch (2-3 contracts) so dashboard shows data immediately.
    """
    print("[CRA] Starting VendorFlow AI CRA backend …")

    if not os.path.exists(CSV_FILE):
        print(f"[CRA] WARNING: CSV not found at {CSV_FILE}")
        return

    try:
        df = pd.read_csv(CSV_FILE)
        df["Days_to_Renewal"] = pd.to_numeric(df["Days_to_Renewal"], errors="coerce")

        # Only seed if agent state is empty
        if not agent.state:
            contracts_180 = _pick_contracts(df, 90, 180, 3)
            contracts_90  = _pick_contracts(df, 30,  90, 2)
            contracts_30  = _pick_contracts(df,  0,  30, 2)

            for cid in contracts_180:
                await agent.execute_agent_loop({"contract_id": cid})
            for cid in contracts_90:
                agent.call_tool_update_stage(cid, "Budgeting")
                await agent.execute_agent_loop({"contract_id": cid})
            for cid in contracts_30:
                agent.call_tool_update_stage(cid, "Approval")
                await agent.execute_agent_loop({"contract_id": cid})

        print("[CRA] Startup complete.")
    except Exception as e:
        print(f"[CRA] Startup error: {e}")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "VendorFlow AI CRA"}


@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
        print(f"[Webhook] Received: {payload}")
        await agent.execute_agent_loop(payload)
        return {"status": "success", "message": "Agent processing initiated."}
    except Exception as e:
        print(f"[Webhook] Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/action/{contract_id}/{stage_action}", response_class=HTMLResponse)
async def handle_stage_action(contract_id: str, stage_action: str):
    """
    Called when stakeholder clicks action button in email.
    Updates workflow stage, resets Email_Sent flag, and IMMEDIATELY triggers next-stage email.
    Returns HTML success page instead of JSON for better UX.
    """
    print(f"[Action] {contract_id} -> {stage_action}")
    
    # Update workflow stage
    agent.call_tool_update_stage(contract_id, stage_action)
    
    # Immediately trigger next-stage email for this specific contract
    # This ensures the user gets the next phase email instantly without manual refresh
    try:
        # Load current state to get the new stage
        agent_state = _load_json(AGENT_STATE_FILE)
        current_stage = agent_state.get(contract_id, {}).get("Stage", stage_action)
        
        # Trigger email for this specific contract only
        # We'll call a targeted email send for this contract
        await _trigger_immediate_email(contract_id, current_stage)
        
        success_message = f"Contract {contract_id} successfully transitioned to '{stage_action}'. Next phase email has been sent."
    except Exception as e:
        print(f"[Action] Error triggering immediate email: {e}")
        success_message = f"Contract {contract_id} transitioned to '{stage_action}'. Email will be sent shortly."
    
    # Return HTML success page instead of JSON
    html_response = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Action Completed - VendorFlow AI</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }}
        .success-icon {{
            width: 80px;
            height: 80px;
            background: #10B981;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
        }}
        .success-icon::before {{
            content: "✓";
            color: white;
            font-size: 48px;
            font-weight: bold;
        }}
        h1 {{
            color: #1F2937;
            margin: 0 0 16px;
            font-size: 28px;
        }}
        p {{
            color: #6B7280;
            margin: 0 0 32px;
            font-size: 16px;
            line-height: 1.6;
        }}
        .contract-info {{
            background: #F3F4F6;
            border-radius: 8px;
            padding: 16px;
            margin: 0 0 24px;
        }}
        .contract-info strong {{
            color: #1F2937;
            display: block;
            margin-bottom: 8px;
        }}
        .contract-info span {{
            color: #6B7280;
            font-size: 14px;
        }}
        .btn {{
            display: inline-block;
            background: #667eea;
            color: white;
            text-decoration: none;
            padding: 12px 32px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #5568d3;
        }}
        .footer {{
            margin-top: 32px;
            color: #9CA3AF;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon"></div>
        <h1>Action Completed</h1>
        <p>{success_message}</p>
        <div class="contract-info">
            <strong>Contract ID: {contract_id}</strong>
            <span>Current Stage: {stage_action}</span>
        </div>
        <a href="http://localhost:8502" class="btn">Return to Dashboard</a>
        <div class="footer">
            VendorFlow AI · Contract Renewal Agent
        </div>
    </div>
</body>
</html>
    """
    return html_response


async def _trigger_immediate_email(contract_id: str, stage: str):
    """
    Immediately trigger the next-stage email for a specific contract.
    This is called after a manual stage transition to ensure instant email delivery.
    """
    import csv
    import random
    from datetime import datetime, timezone
    
    # Load CSV to get contract data
    if not os.path.exists(CSV_FILE):
        print(f"[ImmediateEmail] CSV not found: {CSV_FILE}")
        return
    
    # Load states
    email_state = _load_json(EMAIL_STATE_FILE)
    agent_state = _load_json(AGENT_STATE_FILE)
    
    # Find the contract in CSV
    with open(CSV_FILE, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("Contract_ID") == contract_id:
                # Found the contract, trigger the email
                from email_service import (
                    _map_vendor_name, _validate_license_type, _get_recipients,
                    build_email, send_email, _c1064_stage_to_alert,
                    WORKFLOW_STAGES, WORKFLOW_ACTION_LABELS, WORKFLOW_NEXT_STAGE,
                )
                
                # Prepare contract data
                vendor = _map_vendor_name(row.get("Vendor", ""), contract_id)
                row["Vendor"] = vendor
                license_type = _validate_license_type(row.get("License_Type", "Full"))
                row["License_Type"] = license_type
                
                # Get recipients
                recipients = _get_recipients(row, vendor)
                
                # Map stage to alert key
                alert_key = _c1064_stage_to_alert(stage)
                if not alert_key:
                    print(f"[ImmediateEmail] No alert key for stage: {stage}")
                    return
                
                # Check if email already sent
                if email_state.get(contract_id, {}).get(alert_key) == "SENT":
                    print(f"[ImmediateEmail] Email already sent for {contract_id} stage {stage}")
                    return
                
                # Build email
                action_label = WORKFLOW_ACTION_LABELS.get(stage)
                action_stage = WORKFLOW_NEXT_STAGE.get(stage)
                if stage == "Closed":
                    action_label = None
                    action_stage = None
                
                subject, body = build_email(row, stage, f"Action required for {stage}", action_label, action_stage)
                
                # Send email
                success = any(send_email(r, subject, body) for r in recipients)
                
                if success:
                    # Update email state
                    email_state.setdefault(contract_id, {})
                    email_state[contract_id][alert_key] = "SENT"
                    _save_json(EMAIL_STATE_FILE, email_state)
                    
                    # Update agent state
                    agent_state = _load_json(AGENT_STATE_FILE)
                    if contract_id in agent_state:
                        agent_state[contract_id]["Email_Sent"] = True
                        agent_state[contract_id]["Execution_Status"] = "Email Sent"
                        agent_state[contract_id]["Last_Trigger"] = alert_key
                        agent_state[contract_id]["Last_Trigger_Timestamp"] = datetime.now(timezone.utc).isoformat()
                        _save_json(AGENT_STATE_FILE, agent_state)
                    
                    print(f"[ImmediateEmail] Email sent successfully for {contract_id} stage {stage}")
                else:
                    print(f"[ImmediateEmail] Failed to send email for {contract_id} stage {stage}")
                
                return
    
    print(f"[ImmediateEmail] Contract {contract_id} not found in CSV")


@app.post("/refresh")
async def refresh_triggers(batch_size: int = 3):
    """
    Controlled refresh — fires only batch_size new trigger emails.
    Avoids Gmail rate limits by executing gradually.
    """
    fired = email_process(batch_size=batch_size)
    pending = get_pending_count()
    return {
        "status":    "ok",
        "fired":     fired,
        "total_new": sum(fired.values()),
        "pending":   pending,
    }


@app.get("/pending")
async def get_pending():
    """Returns count of contracts still awaiting trigger emails."""
    return {"pending": get_pending_count()}


@app.get("/status")
async def get_status():
    """
    Unified JSON snapshot for dashboard polling.
    """
    agent_state = _load_json(STATE_FILE)
    trigger_log = _load_json(TRIGGER_LOG_FILE)
    email_state = _load_json(EMAIL_STATE_FILE)

    window_counts = {"180d": 0, "90d": 0, "30d": 0, "critical": 0,
                     "high_util": 0, "low_util": 0}
    total_fired   = 0
    for flags in email_state.values():
        if flags.get("Alert_180")      == "SENT": window_counts["180d"]     += 1; total_fired += 1
        if flags.get("Alert_90")       == "SENT": window_counts["90d"]      += 1; total_fired += 1
        if flags.get("Alert_30")       == "SENT": window_counts["30d"]      += 1; total_fired += 1
        if flags.get("Alert_Critical") == "SENT": window_counts["critical"] += 1; total_fired += 1
        if flags.get("Alert_High_Util")== "SENT": window_counts["high_util"]+= 1; total_fired += 1
        if flags.get("Alert_Low_Util") == "SENT": window_counts["low_util"] += 1; total_fired += 1

    return JSONResponse(content={
        "agent_state":            agent_state,
        "trigger_log":            trigger_log,
        "email_state":            email_state,
        "total_active_workflows": len(agent_state),
        "total_triggers_fired":   total_fired,
        "trigger_window_counts":  window_counts,
        "pending_triggers":       get_pending_count(),
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
