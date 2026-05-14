# 🦋 Contract Renewal Agent (CRA) Platform

The **CRA Platform** is an automated system designed to monitor SaaS contract renewals, track license utilization, and orchestrate approval workflows via Gmail push notifications.

## 📁 Project Structure

- `main.py`: FastAPI server that handles webhooks and orchestrates the agent loop.
- `agent_logic.py`: Core logic for the Contract Agent, including workflow transitions and email relay.
- `app_v8.py`: Main Streamlit dashboard for visualizing contract data and renewal status.
- `appp.py`: Shared dashboard components and data loading logic.
- `setup_gmail_watch.py`: Utility script to bind your Gmail inbox to a GCP Pub/Sub topic.
- `data/`: Folder containing CSV datasets, state files, and credentials.
- `.env`: Secret configuration file (ignored by git).
- `requirements.txt`: Python dependencies.

## 🚀 Setup Instructions

### 1. Environment Configuration
Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
```
Key variables to update:
- `SMTP_EMAIL` & `SMTP_PASSWORD`: Your Gmail sender credentials (use an App Password).
- `BASE_URL`: Your ngrok URL or local IP (e.g., `https://xxxx-xxxx.ngrok-free.app`).
- `GCP_PROJECT_ID` & `GCP_TOPIC_NAME`: Your Google Cloud project and Pub/Sub topic.

### 2. Install Dependencies
Ensure you have Python 3.9+ installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Google Cloud & Gmail Setup
Follow these steps to enable the automated relay:

#### A. Local Network Exposure (Ngrok)
Expose port 8000 to receive webhooks:
```bash
ngrok http 8000
```
Update `BASE_URL` in your `.env` with the generated URL.

#### B. GCP Pub/Sub
1. Create a **Pub/Sub Topic** in GCP Console.
2. Grant `gmail-api-push@system.gserviceaccount.com` the **Pub/Sub Publisher** role on the topic.
3. Create a **Push Subscription** for the topic, pointing to `BASE_URL/webhook`.

#### C. Gmail API Credentials
1. Create an OAuth Client ID (Desktop App) in GCP -> APIs & Services -> Credentials.
2. Download the JSON file and save it as `data/credentials.json`.
3. Run the registration script:
   ```bash
   python setup_gmail_watch.py
   ```

## 🏃 Running the Application

### 1. Start the Agent (Orchestrator)
The agent listens for webhooks and manages the workflow state.
```bash
uvicorn main:app --reload
```

### 2. Start the Dashboard
Visualize the portfolio and renewal triggers.
```bash
streamlit run app_v8.py
```

## 🛠 Butterfly Triggers
The platform uses "Butterfly Rules" to flag risks:
- **Red Alert**: <=30 days to renewal, <70% utilization, or budget exceeded.
- **Amber Warning**: 31-180 days to renewal, or overpriced vs market.
- **Green**: Healthy contracts with high utilization and good performance.


