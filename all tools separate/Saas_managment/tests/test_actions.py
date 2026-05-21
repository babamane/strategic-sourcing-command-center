import pytest
from pathlib import Path

from mcp_server.actions import dispatch_csv, dispatch_jira, dispatch_slack


def test_dispatch_jira_mock_without_credentials(monkeypatch):
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    monkeypatch.delenv("JIRA_PROJECT_KEY", raising=False)
    payload = {"vendor": "Veloxa", "action_type": "reclamation", "seat_delta": -1, "dollar_impact": 100.0}
    result = dispatch_jira(payload)
    assert result.get("status") == "ok"
    assert result.get("mock") is True


def test_dispatch_slack_mock_without_webhook(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    result = dispatch_slack({"vendor": "Veloxa", "action_type": "renewal_alert"})
    assert result.get("status") == "ok"
    assert result.get("mock") is True


def test_dispatch_csv_writes_file(monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_EXPORT_PATH", ".")
    payload = {
        "vendor": "TestCo",
        "action_type": "ghost_review",
        "seat_delta": -2,
        "dollar_impact": 50.0,
        "affected_records": [{"license_id": "L1"}, {"license_id": "L2"}],
    }
    result = dispatch_csv(payload)
    assert result.get("status") == "ok"
    path = Path(result["path"])
    assert path.exists()
    path.unlink(missing_ok=True)
