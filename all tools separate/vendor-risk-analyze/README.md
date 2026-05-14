# 🛡️ Vendor Risk Analyzer

An AI-powered vendor risk management dashboard that automatically analyzes alerts, generates remediation plans using a local LLM (Ollama), creates Jira tickets on approval, and sends email notifications — all running **100% locally**.

---

## 📋 Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Step 1 — Install Ollama &amp; Pull Model](#step-1--install-ollama--pull-model)
5. [Step 2 — Clone &amp; Install Dependencies](#step-2--clone--install-dependencies)
6. [Step 3 — Set Up the .env File](#step-3--set-up-the-env-file)
7. [Step 4 — Jira Integration Setup](#step-4--jira-integration-setup)
8. [Step 5 — Gmail Email Integration Setup](#step-5--gmail-email-integration-setup)
9. [Step 6 — Add Your Alert Data](#step-6--add-your-alert-data)
10. [Step 7 — Run the App](#step-7--run-the-app)
11. [How the App Works](#how-the-app-works)
12. [API Endpoints](#api-endpoints)
13. [Switching Models](#switching-models)
14. [Troubleshooting](#troubleshooting)

---

## 🛠 Tech Stack

| Layer            | Technology                              |
| ---------------- | --------------------------------------- |
| Backend          | Python, Flask, Flask-CORS               |
| AI / LLM         | Ollama (local) — Qwen2, Gemma3, etc.   |
| Frontend         | HTML, CSS, Vanilla JavaScript           |
| Data Storage     | Excel (`.xlsx`) via Pandas + openpyxl |
| Jira Integration | Jira REST API v3                        |
| Email            | Gmail SMTP (SSL)                        |
| Config           | python-dotenv (`.env` file)           |

---

## 📁 Project Structure

```
vendor-risk-analyzer/
├── backend.py          # Flask server — all API routes & business logic
├── data.py             # Utility: convert raw alerts to Vendor format
├── alerts.xlsx         # Input: raw vendor alerts
├── output.xlsx         # Output: approved/rejected decisions
├── requirements.txt    # Python dependencies
├── .env                # 🔐 Secrets & config (you create this)
├── static/
│   ├── script.js       # Dashboard JS logic
│   └── style.css       # Dashboard styling
└── templates/
    ├── dashboard.html  # New dashboard (decision view)
    └── old_dashboard.html  # Alert detail & analysis view
```

---

## ✅ Prerequisites

- Python 3.9 or higher → [Download Python](https://www.python.org/downloads/)
- pip (comes with Python)
- [Ollama](https://ollama.com/download) installed
- A [Jira account](https://www.atlassian.com/software/jira) (free tier works)
- A Gmail account with 2-Step Verification enabled

---

## Step 1 — Install Ollama & Pull Model

### 1.1 Install Ollama

Download and install from: **https://ollama.com/download**

### 1.2 Pull the AI model

Open a terminal and run:

```bash
ollama pull qwen2:1.5b
```

> Other supported models you can use:
>
> ```bash
> ollama pull gemma3
> ollama pull gemma4:e2b
> ollama pull llama3:8b
> ```

### 1.3 Start Ollama (keep this running)

```bash
ollama serve
```

> On Windows, Ollama usually starts automatically. Check if it's running at: http://localhost:11434

---

## Step 2 — Clone & Install Dependencies

```bash
# Navigate to the project folder
cd vendor-risk-analyzer

# Install all Python packages
pip install -r requirements.txt
```

---

## Step 3 — Set Up the .env File

Create a file named `.env` in the project root folder (`vendor-risk-analyzer/`).

Copy and paste this template:

```env
# ─── Ollama ────────────────────────────────────────────────
OLLAMA_URL=http://127.0.0.1:11434/api/generate
OLLAMA_MODEL=qwen2:1.5b

# ─── Jira Integration ──────────────────────────────────────
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@gmail.com
JIRA_API_TOKEN=your-jira-api-token-here
JIRA_PROJECT_KEY=KAN

# ─── Email (Gmail SMTP) ────────────────────────────────────
EMAIL_SENDER=your-email@gmail.com
EMAIL_RECEIVER=receiver-email@gmail.com
EMAIL_APP_PASSWORD=your-gmail-app-password
```

> ⚠️ **Never commit `.env` to GitHub.** Add it to `.gitignore`:
>
> ```
> .env
> ```

---

## Step 4 — Jira Integration Setup

When an alert is **approved**, the app automatically creates a Jira task with full details.

### 4.1 Create a Jira Account

Go to: **https://www.atlassian.com/software/jira** → Sign up for free

### 4.2 Create a Jira Project

1. Log in to your Jira account
2. Click **"Create project"**
3. Choose **"Scrum"** or **"Kanban"** (either works)
4. Give it a name — note the **Project Key** (e.g., `KAN`)
5. This key goes in your `.env` as `JIRA_PROJECT_KEY`

### 4.3 Generate a Jira API Token

1. Go to: **https://id.atlassian.com/manage-profile/security/api-tokens**
2. Click **"Create API token"**
3. Give it a label (e.g., `vendor-risk-analyzer`)
4. Click **"Create"** → Copy the token immediately (shown only once)
5. Paste it in `.env` as `JIRA_API_TOKEN`

### 4.4 Fill in your .env

```env
JIRA_BASE_URL=https://yourname.atlassian.net    # your Jira site URL
JIRA_EMAIL=your-email@gmail.com                 # email used to log in to Jira
JIRA_API_TOKEN=ATATT3xFfGF0...                  # token from step 4.3
JIRA_PROJECT_KEY=KAN                            # project key from step 4.2
```

> 📖 Official Jira API docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

---

## Step 5 — Gmail Email Integration Setup

The app sends emails automatically:

- ✅ **Approval email** — rich HTML email with all AI analysis details + Jira link
- ❌ **Rejection email** — plain text notification

### 5.1 Enable 2-Step Verification on Gmail

1. Go to: **https://myaccount.google.com/security**
2. Under **"How you sign in to Google"**, enable **2-Step Verification**

### 5.2 Generate a Gmail App Password

> ⚠️ You MUST have 2-Step Verification enabled first.

1. Go to: **https://myaccount.google.com/apppasswords**
2. Select app: **"Mail"**
3. Select device: **"Other (custom name)"** → type `vendor-risk-analyzer`
4. Click **"Generate"** → Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
5. Remove spaces: `abcdefghijklmnop`
6. Paste in `.env` as `EMAIL_APP_PASSWORD`

### 5.3 Fill in your .env

```env
EMAIL_SENDER=your-gmail@gmail.com       # the Gmail account sending emails
EMAIL_RECEIVER=receiver@gmail.com       # who receives the notifications
EMAIL_APP_PASSWORD=abcdefghijklmnop     # 16-char app password (no spaces)
```

> 📖 Google App Passwords guide: https://support.google.com/accounts/answer/185833

---

## Step 6 — Add Your Alert Data

Place your alerts in `alerts.xlsx`. The file must have these columns:

| Column               | Description        | Example                                  |
| -------------------- | ------------------ | ---------------------------------------- |
| `alert_id`         | Unique alert ID    | `123456`                               |
| `vendor`           | Vendor name        | `Vendor 1`                             |
| `vendor_id`        | Vendor ID          | `V-1001`                               |
| `vendor_domain`    | Vendor domain      | `vendor1.com`                          |
| `alertTitle`       | Alert title        | `API Key Exposed`                      |
| `alertDescription` | Full description   | `A third-party API key...`             |
| `action_item`      | Recommended action | `Rotate credentials`                   |
| `risk_level`       | Risk level         | `high`, `medium`, `low`            |
| `resource_type`    | Alert type         | `Security Advisory`, `Policy Update` |
| `business_unit`    | Affected dept      | `IT Security`, `Finance`             |
| `submittedAt`      | Date submitted     | `2026-04-20 10:00:00`                  |

> The included `alerts.xlsx` has synthetic demo data — ready to use immediately.

To convert/reformat existing alert data, run:

```bash
python data.py
```

---

## Step 7 — Run the App

```bash
python backend.py
```

You should see:

```
==================================================
  Vendor Risk Analyzer — Backend
  Model : qwen2:1.5b
  Data  : alerts.xlsx
  URL   : http://localhost:5000
==================================================
```

Open your browser and go to: **http://localhost:5000**

---

## 🖥️ How the App Works

### Main Dashboard (`/`)

- Lists all vendor alerts from `alerts.xlsx`
- Shows risk level, status (Pending / Accepted / Rejected), and Jira link
- Auto-refreshes every 5 seconds
- Filter by risk level, business unit, resource type
- Click **"+ Generate Alert"** to generate a synthetic alert using AI

### Alert Detail View (`/old` or click a row)

- Full alert details panel
- Click **"Analyze"** → AI generates a complete remediation plan:
  - Remedy type (CONTRACT_REVIEW, VENDOR_AMENDMENT, etc.)
  - Confidence score (60–95%)
  - Risk summary (7–8 lines)
  - Tags, Rationale, Step-by-step plan, Success criteria, SLA
- **Approve** → Creates Jira ticket + sends approval email
- **Reject** → Sends rejection email notification

### Decision Storage

All decisions are saved to `output.xlsx` with full AI analysis data.

---

## 🔌 API Endpoints

| Method   | Endpoint                | Description                       |
| -------- | ----------------------- | --------------------------------- |
| `GET`  | `/`                   | Main dashboard                    |
| `GET`  | `/old`                | Alert detail view                 |
| `GET`  | `/api/alerts`         | Get all raw alerts                |
| `GET`  | `/api/dashboard`      | Get alerts with decision status   |
| `POST` | `/api/analyze`        | Run AI analysis on an alert       |
| `POST` | `/api/decision`       | Save approve/reject decision      |
| `POST` | `/api/generate-alert` | Generate a synthetic alert via AI |
| `GET`  | `/api/status`         | Check Ollama connection status    |

---

## 🔄 Switching Models

Edit your `.env` file:

```env
OLLAMA_MODEL=qwen2:1.5b    # fast, lightweight (default)
# OLLAMA_MODEL=gemma3      # better quality
# OLLAMA_MODEL=llama3:8b   # most capable, slower
```

Make sure the model is pulled first:

```bash
ollama pull gemma3
```

Then restart `backend.py` — no code changes needed.

---

## 🔧 Troubleshooting

| Problem                                  | Fix                                                                      |
| ---------------------------------------- | ------------------------------------------------------------------------ |
| `python backend.py` gives syntax error | Run `python --version` — must be 3.9+                                 |
| "Cannot reach backend" in browser        | Make sure `python backend.py` is running                               |
| "AI analysis failed"                     | Run `ollama serve` in a separate terminal                              |
| Model not found error                    | Run `ollama pull qwen2:1.5b`                                           |
| Port 5000 already in use                 | Add `PORT=5001` to `.env` or change `port=5000` in `backend.py`  |
| Jira ticket not created                  | Check `JIRA_API_TOKEN` and `JIRA_BASE_URL` in `.env`               |
| Email not sending                        | Ensure 2FA is on Gmail and `EMAIL_APP_PASSWORD` is correct (no spaces) |
| `.env` not loading                     | Make sure `.env` is in the same folder as `backend.py`               |
| Excel file error                         | Check `alerts.xlsx` has all required columns (see Step 6)              |

---

## 🔐 Security Notes

- Never commit `.env` to version control
- Rotate your Jira API token regularly at: https://id.atlassian.com/manage-profile/security/api-tokens
- Gmail App Passwords can be revoked at: https://myaccount.google.com/apppasswords
- This app is designed for **local/internal use** — Flask debug mode is ON by default

---

## 📦 Dependencies

```
flask==3.1.0
flask-cors==5.0.1
pandas==2.2.3
openpyxl==3.1.5
requests==2.32.3
python-dotenv==1.2.1
```

Install all at once:

```bash
pip install -r requirements.txt
```
