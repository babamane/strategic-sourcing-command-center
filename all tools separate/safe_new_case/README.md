# SAFE — Software Assets Forecasting Engine

**SAFE** is an AI-powered SaaS license management platform built on a local LLM (Ollama/Gemma2). It gives procurement and IT teams a conversational interface to query license forecasts, renewal liabilities, at-risk users, budget spend, and demand planning — all from a single chat UI embedded in a Tableau dashboard.

---

## Project Structure

```
safe_new_case/
│
├── app_v3.py                        # Main entry point — Gradio chat UI + Tableau embed
├── rag_engine_v4.py                 # RAG query engine — intent detection, SQL, LLM
├── case2_engine_v1.py               # Case 2: strategic sourcing / demand planning logic
├── case2_workspace_v1.py            # Streamlit demand discovery workspace (auto-launched)
│
├── data/                            # All data files (CSV, JSON, SQLite)
│   ├── saas_data.db                 # SQLite database (migrated from MySQL)
│   ├── hr_data_v1.csv               # Employee / HR data
│   ├── case2_role_license_mapping_v1.csv
│   ├── case2_vendor_catalog_v1.csv
│   ├── matching_logic.json
│   ├── vendor_benchmarks.csv
│   ├── case2_workspace_context.json # Written at runtime by case2_engine
│   └── license_data_v9_20000.csv
│
├── migrate_to_sqlite.py             # One-time MySQL → SQLite migration script
├── requirements.txt                 # Python dependencies
├── .env                             # Secrets (never commit this)
└── .gitignore
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.11 | 3.14 tested |
| [Ollama](https://ollama.com) | latest | Local LLM runtime |
| Gemma2 9B model | — | Pulled via Ollama |

---

## Setup — Step by Step

### 1. Clone / copy the project

```bash
# If using git
git clone <your-repo-url>
cd safe_new_case
```

### 2. Create and activate a virtual environment *(recommended)*

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the `.env` file

Create a file named `.env` in the project root with the following content.  
**Never commit this file.**

```env
# SQLite database filename (inside the data/ folder)
SQLITE_DB_PATH=saas_data.db

# Gemini API key (optional — app defaults to local Ollama)
GEMINI_API_KEY=your_gemini_api_key_here

# Email credentials (Gmail + App Password)
SENDER_EMAIL=your_email@gmail.com
SENDER_APP_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=recipient@example.com

# Google Form link for at-risk email notifications
GOOGLE_FORM_LINK=https://forms.gle/your-form-link
```

> **Gmail App Password**: Go to [Google Account → Security → 2-Step Verification → App passwords](https://myaccount.google.com/apppasswords) and generate one for "Mail".

### 5. Set up the local LLM (Ollama)

```bash
# Install Ollama from https://ollama.com, then pull the model:
ollama pull gemma2:9b

# Verify it's running
ollama list
```

### 6. Prepare the database

**Option A — `saas_data.db` already provided** *(recommended)*  
The `data/saas_data.db` file is included. Skip this step entirely.

**Option B — Migrate from a MySQL source**  
Only needed if you have a live MySQL `saas_analytics` database and want to re-sync it.  
Add the MySQL credentials to `.env` first:

```env
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=saas_analytics
```

Then run:

```bash
python migrate_to_sqlite.py
```

This performs `SELECT *` on all three source tables and writes them to `data/saas_data.db`. Expected output:

```
[OK] Connected to MySQL: localhost:3306/saas_analytics
[OK] SQLite target: ...\data\saas_data.db

-> Migrating [fct_renewal_liability] ...
   [OK] 748 rows written to SQLite

-> Migrating [fct_license_forecast] ...
   [OK] 2,448 rows written to SQLite

-> Migrating [stg_at_risk_pool] ...
   [OK] 592 rows written to SQLite

[DONE] Migration complete
```

---

## Running the Application

### Start the main app

```bash
python app_v3.py
```

This launches the **Gradio chat UI** at `http://localhost:7860` and opens it in your browser automatically.  
The Tableau dashboard is embedded at the top of the page.

---

## Using the Chat Interface

Click the 🤖 button (bottom-right) to open the chat panel.

### Quick query chips

| Chip | What it does |
|---|---|
| 💰 Forecast | New license acquisition forecast for a vendor + month |
| 🔄 Renewal Split | Contracts expiring, broken down by tier |
| ⚠️ Churn Users | At-risk users with low engagement |
| 📊 Overview | Sends a summary report email + shows overview |
| 💡 Budget | Full budget forecast (new + renewals + combined) |

### Example queries you can type

```
What is my Forecast for May for vendor_1?
Show renewal split for vendor_2 for June
Who are my at-risk users for vendor_1?
What would be my Budget forecast for vendor_1 for the upcoming quarter?
I want to buy new licenses for vendor_3
```

---

## Case 2 — Demand Discovery Workspace

When you ask about **buying / procuring new licenses** (e.g. `"I want to buy new licenses for vendor_3"`,`"I want to procure Compliance Enterprise (V2-LEG-ENT) from vendor_2"`), the system:

1. Detects the **Case 2: Strategic Sourcing** intent
2. Runs the demand analysis engine (`case2_engine_v1.py`)
3. **Auto-launches** the Streamlit workspace at `http://localhost:8501`
4. Returns a summary with a clickable **[Open Demand Discovery Workspace](http://localhost:8501)** link

The Streamlit workspace shows:
- KPIs: total demand, active employees, estimated annual spend, negotiation delta
- Sourcing & negotiation insights
- 4 interactive charts: demand breakdown, departmental mix, tier optimisation, market pricing
- Downloadable procurement report (`.docx`)

---

## Architecture Overview

```
User (browser)
     │
     ▼
app_v3.py  ──────────────────────────  Gradio UI + Tableau embed
     │
     ▼
rag_engine_v4.py  ─── Intent detection ──► build_context()
     │                                          │
     │                                     SQLite queries
     │                                     (data/saas_data.db)
     │
     ├── Case 1 (forecast/renewal/budget/at-risk)
     │        └── Ollama Gemma2 9B ──► LLM response
     │
     └── Case 2 (new license procurement)
              └── case2_engine_v1.py
                       ├── CSV/JSON data (data/ folder)
                       ├── Auto-launch: case2_workspace_v1.py (Streamlit)
                       └── http://localhost:8501
```

---

## Key Files Reference

| File | Role |
|---|---|
| `app_v3.py` | **Run this** — Gradio UI entry point |
| `rag_engine_v4.py` | Core RAG engine, SQL queries, email, LLM calls |
| `case2_engine_v1.py` | Demand planning logic + Streamlit auto-launcher |
| `case2_workspace_v1.py` | Streamlit app (launched automatically, no manual run needed) |
| `migrate_to_sqlite.py` | One-time DB migration (only if re-syncing from MySQL) |
| `.env` | All secrets — **never commit** |
| `data/saas_data.db` | Local SQLite database (replaces MySQL dependency) |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SQLITE_DB_PATH` | Yes | SQLite filename inside `data/` (default: `saas_data.db`) |
| `GEMINI_API_KEY` | Optional | Gemini API key (app uses Ollama by default) |
| `SENDER_EMAIL` | Yes (email features) | Gmail address used to send emails |
| `SENDER_APP_PASSWORD` | Yes (email features) | Gmail App Password (not your account password) |
| `RECIPIENT_EMAIL` | Yes (email features) | Address that receives notifications |
| `GOOGLE_FORM_LINK` | Yes (email features) | Google Form URL embedded in at-risk emails |
| `DB_USER` / `DB_PASSWORD` | Migration only | MySQL credentials for `migrate_to_sqlite.py` |
| `DB_HOST` / `DB_PORT` / `DB_NAME` | Migration only | MySQL connection details |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your venv |
| Ollama not responding | Run `ollama serve` in a separate terminal, then retry |
| Email not sending | Check `SENDER_APP_PASSWORD` — must be a Gmail App Password, not your login password |
| `saas_data.db not found` | Either copy the `data/` folder from the source or run `migrate_to_sqlite.py` |
| Streamlit workspace not opening | Wait 3–5 seconds after the chat response; Streamlit takes a moment to start |
| Port 8501 already in use | Stop the existing Streamlit process or change `STREAMLIT_PORT` in `case2_engine_v1.py` |

---

## Notes

- The application requires **no internet connection** for LLM inference — it runs fully locally via Ollama.
- The Gemini API key is present in `.env` but the current LLM backend is **Ollama (Gemma2 9B)**.
- `saas_data.db` uses SQLite — a file-based database with **no server required**.
- The Streamlit workspace is **automatically launched** when a Case 2 intent is detected; there is no need to run `streamlit run` manually.
