from fastapi.testclient import TestClient

from api.main import app
from processing.context_builder import build_context
from tests.test_mail_service import DummySMTP


def _vendor():
    return build_context().active_vendors[0]


def test_churn_mail_preview(monkeypatch):
    monkeypatch.setenv("CHURN_NOTIFICATION_RECIPIENT", "ops@example.com")
    client = TestClient(app)

    response = client.post("/mail/churn-notification", json={"vendor": _vendor(), "confirmed": False})

    assert response.status_code == 200
    body = response.json()
    assert body["preview"] is True
    assert body["recipient"] == "ops@example.com"
    assert body["candidate_count"] > 0


def test_churn_mail_confirmed(monkeypatch):
    DummySMTP.calls = []
    monkeypatch.setenv("CHURN_NOTIFICATION_RECIPIENT", "ops@example.com")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setattr("smtplib.SMTP", DummySMTP)
    monkeypatch.setattr("api.routers.mail.insert_recommendation", lambda payload: "rec-mail")
    client = TestClient(app)

    response = client.post("/mail/churn-notification", json={"vendor": _vendor(), "confirmed": True})

    assert response.status_code == 200
    body = response.json()
    assert body["sent"] is True
    assert body["recommendation_id"] == "rec-mail"
