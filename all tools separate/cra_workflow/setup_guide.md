# 🚀 Anti Gravity Orchestrator Setup Guide

This guide covers how to set up the **Agentic Relays** via Gmail Push Notifications (Pub/Sub) and expose your FastAPI locally using ngrok.

## 1. Local Network Exposure (Ngrok)

To receive webhooks from Google Cloud on your machine, you must expose port 8000.

1. Install [ngrok](https://ngrok.com/download).
2. Start the tunnel:
   ```bash
   ngrok http 8000
   ```
3. Copy the `Forwarding URL` (e.g., `https://1234-abcd.ngrok-free.app`). Your webhook endpoint will be `https://1234-abcd.ngrok-free.app/webhook`.

## 2. Setting up Google Cloud Pub/Sub & Gmail

To let Gmail inform our agent of new 180-day alerts:

1. **Create a Pub/Sub Topic**:
   - Go to GCP Console -> Pub/Sub.
   - Create a topic (e.g., `projects/my-project/topics/cra-webhook-topic`).
2. **Grant Gmail Publish Rights**:
   - Add `gmail-api-push@system.gserviceaccount.com` as a **Pub/Sub Publisher** on your topic.
3. **Configure the Push Subscription**:
   - Create a subscription for the topic.
   - Set Delivery Type to **Push**.
   - Input your Ngrok Webhook URL (`https://.../webhook`).

## 3. Register the `watch()` Request

Use the Gmail API to instruct Google to publish to your topic. You can do this via Google's OAuth Playground or a simple Python script using your authorized credentials.

**Sample `watch` body:**
```json
{
  "labelIds": ["INBOX"],
  "labelFilterAction": "include",
  "topicName": "projects/my-project/topics/cra-webhook-topic"
}
```

## 4. Run the Anti Gravity Orchestrator & Dashboard

Make sure you've installed required packages (`fastapi`, `uvicorn`, `streamlit`, `plotly`, `pandas`).

1. **Start the Agent (FastAPI):**
   ```bash
   uvicorn main:app --reload
   ```

2. **Start the Dashboard (Streamlit):**
   ```bash
   streamlit run app_v8.py
   ```

When changes occur in the Agent (`agent_state.json`), simply refreshing the Streamlit dashboard will reflect the newly assigned `Current_Stage` and `Pending_With` values.
