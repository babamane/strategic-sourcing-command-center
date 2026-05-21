"""Integration dispatchers for write tools (Jira, Slack, CSV export)."""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _export_base_dir() -> Path:
    raw = os.getenv("RECOMMENDATION_EXPORT_PATH", "./exports")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def dispatch_jira(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a Jira ticket from a structured payload, or return a mock result."""

    from dotenv import load_dotenv
    load_dotenv(override=True)

    base    = os.getenv("JIRA_BASE_URL", "").strip()
    email   = os.getenv("JIRA_EMAIL", "").strip()
    token   = os.getenv("JIRA_API_TOKEN", "").strip()
    project = os.getenv("JIRA_PROJECT_KEY", "").strip()

    if not (base and email and token and project):
        logger.warning("Jira credentials missing — returning mock dispatch result")
        return {"status": "ok", "integration": "jira", "ticket_id": "MOCK-001", "mock": True}

    try:
        import base64
        import urllib.error
        import urllib.request

        summary = f"{payload.get('action_type')} — {payload.get('vendor')}"
                # ADD THIS BLOCK HERE
        trimmed_payload = {**payload, "affected_records": payload.get("affected_records", [])[:5]}
        description_text = json.dumps(trimmed_payload, indent=2)
        if len(description_text.encode("utf-8")) > 10000:
            description_text = description_text[:10000] + "\n... (truncated)"

        body = {
            "fields": {
                "project": {"key": project},
                "summary": summary[:254],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "codeBlock",
                            "attrs": {"language": "json"},
                            "content": [{"type": "text", "text": description_text}],  # ← use description_text here
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
            }
        }
        

        credentials = base64.b64encode(f"{email}:{token}".encode()).decode()

        req = urllib.request.Request(
            f"{base.rstrip('/')}/rest/api/3/issue",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        ticket_id  = data.get("key", "unknown")
        ticket_url = f"{base.rstrip('/')}/browse/{ticket_id}"
        logger.info("Jira ticket created: %s", ticket_url)
        return {
            "status": "ok",
            "integration": "jira",
            "ticket_id": ticket_id,
            "ticket_url": ticket_url,
            "mock": False,
        }

    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        logger.error("Jira HTTP %s: %s", exc.code, body_text)
        return {"status": "failed", "reason": f"HTTP {exc.code}: {body_text}"}

    except Exception as exc:
        logger.exception("Jira dispatch failed")
        return {"status": "failed", "reason": str(exc)}


def dispatch_slack(payload: dict[str, Any]) -> dict[str, Any]:
    """Post a Slack message from a webhook, or return a mock result."""

    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        logger.warning("SLACK_WEBHOOK_URL missing — returning mock dispatch result")
        return {"status": "ok", "integration": "slack", "message_ts": "MOCK-SLACK", "mock": True}

    try:
        import urllib.request

        text = (
            f"*{payload.get('action_type')}* for *{payload.get('vendor')}*\n"
            f"Annual impact: ${payload.get('dollar_impact', 0):,.0f}\n"
            f"```\n{json.dumps(payload, indent=2)[:3500]}\n```"
        )
        req = urllib.request.Request(
            webhook,
            data=json.dumps({"text": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        return {"status": "ok", "integration": "slack", "mock": False}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Slack dispatch failed")
        return {"status": "failed", "reason": str(exc)}


def dispatch_csv(payload: dict[str, Any]) -> dict[str, Any]:
    """Write affected records to a CSV file under the exports directory."""

    try:
        vendor = str(payload.get("vendor", "unknown")).replace("/", "_")
        action = str(payload.get("action_type", "action")).replace("/", "_")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = _export_base_dir() / f"{action}_{vendor}_{ts}.csv"
        records = payload.get("affected_records") or []
        if not records:
            with path.open("w", encoding="utf-8", newline="") as handle:
                handle.write("empty\n")
        else:
            fieldnames = sorted({key for row in records for key in row.keys()})
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in records:
                    writer.writerow({k: row.get(k) for k in fieldnames})
        return {"status": "ok", "integration": "csv", "path": str(path.resolve()), "mock": False}
    except Exception as exc:  # noqa: BLE001
        logger.exception("CSV dispatch failed")
        return {"status": "failed", "reason": str(exc)}
