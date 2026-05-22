# VendorFlow AI — Contract Renewal Agent (CRA) v3.0

## Quick Start

### 1. Setup environment
```bash
cd vendorflow_final
cp .env.example .env
# Edit .env with your Gmail credentials and email addresses
```

Important: this project is intended to run under Python 3.11 only. Use the `py -3.11` interpreter when installing dependencies and launching services.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed initial state (run once)
```bash
python seed_state.py
```
This pre-populates `data/agent_state.json`, `data/email_state.json`, and `data/trigger_log.json` so the dashboard shows data immediately on first launch.

### 4. Start the FastAPI backend (Terminal 1)
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Start the dashboard (Terminal 2)
```bash
streamlit run app_v9.py
```
The dashboard opens at **http://localhost:8501**

---

## Project Structure

```
vendorflow_final/
├── app_v9.py           ← Main Streamlit dashboard (5 pages)
├── main.py             ← FastAPI backend (triggers, status, webhook)
├── agent_logic.py      ← 5-stage workflow state machine
├── email_service.py    ← All 6 trigger types + controlled refresh
├── seed_state.py       ← Pre-populate data for first run
├── adk_agent.py        ← Optional ADK intelligence agent
├── requirements.txt
├── .env.example
└── data/
    ├── merged_dataset_FINAL_fabricated_1341_util_adjusted.csv
    ├── agent_state.json     (auto-created)
    ├── email_state.json     (auto-created)
    └── trigger_log.json     (auto-created)
```

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| ⚡ Operations Overview | KPIs, live workflow table, activity feed, trigger window summary |
| 🔄 Workflow Monitor | Node-level stage visibility per contract, expandable cards |
| 🎯 Trigger Center | All 6 triggers with execution state, controlled refresh |
| 🚨 Alert Center | Critical contracts, high/low util alerts, real-time feed |
| 🖥️ Execution Logs | Terminal audit trail, email log, system status |

---

## Trigger Types

| Trigger | Condition | Severity |
|---------|-----------|----------|
| 180-Day Planning | Days ≤ 180 | Info |
| 90-Day Escalation | Days ≤ 90 | Warning |
| 30-Day Critical | Days ≤ 30 | Urgent |
| 7-Day Expiring | Days ≤ 7 | Critical |
| High Utilization | Util > 80% | Warning/High/Critical |
| Low Utilization | Util < 70% | Optimize |

---

## Controlled Refresh

**DO NOT** click Refresh repeatedly — each refresh fires only **3 triggers at a time** to avoid Gmail rate limits.

- `Refresh (3)` → fires 3 new triggers
- `Refresh (5)` → fires 5 new triggers  
- `Auto 10s` → fires 3 every 10 seconds automatically

---

## Gmail Setup

1. Go to https://myaccount.google.com/apppasswords
2. Create an App Password for "Mail"
3. Copy the 16-character password into `.env` as `SMTP_PASSWORD`
4. Set `SMTP_EMAIL` to your Gmail address
5. Set `PROCUREMENT_EMAIL`, `FINANCE_EMAIL`, `EXECUTIVE_EMAIL` to recipient addresses

Without Gmail configured, the system runs in **simulation mode** — all emails are logged but not sent.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/status` | Full state snapshot (used by dashboard) |
| POST | `/refresh?batch_size=3` | Fire N new triggers (controlled) |
| GET | `/pending` | Count of pending triggers |
| POST | `/webhook` | Gmail Pub/Sub push |
| GET | `/action/{id}/{stage}` | Email action button handler |

---

## 5-Stage Workflow

```
Planning → Budgeting → Approval → Execution → Closed
   ↑           ↑           ↑           ↑          ↑
 180-day     90-day      30-day      7-day    Completed
 trigger     trigger    trigger    trigger
```

Each stage sends a role-specific HTML email with a single-click action button to advance the workflow.
