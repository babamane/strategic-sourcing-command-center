from services.mail_service import send_churn_notification


class DummySMTP:
    calls: list[tuple] = []

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ehlo(self):
        self.calls.append(("ehlo",))

    def starttls(self):
        self.calls.append(("starttls",))

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def sendmail(self, user, recipient, body):
        self.calls.append(("sendmail", user, recipient, body))


def test_churn_notification_preview_does_not_send(monkeypatch):
    DummySMTP.calls = []
    monkeypatch.setenv("CHURN_NOTIFICATION_RECIPIENT", "ops@example.com")
    monkeypatch.setattr("smtplib.SMTP", DummySMTP)

    result = send_churn_notification(
        vendor="Atlassify",
        department=None,
        candidates=[{"license_id": "L1", "annual_cost": 100}],
        dollar_impact=100,
        preview_only=True,
    )

    assert result["preview"] is True
    assert result["recipient"] == "ops@example.com"
    assert DummySMTP.calls == []


def test_churn_notification_send_uses_smtp(monkeypatch):
    DummySMTP.calls = []
    monkeypatch.setenv("CHURN_NOTIFICATION_RECIPIENT", "ops@example.com")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setattr("smtplib.SMTP", DummySMTP)

    result = send_churn_notification(
        vendor="Atlassify",
        department="Engineering",
        candidates=[{"license_id": "L1", "annual_cost": 100}],
        dollar_impact=100,
        preview_only=False,
    )

    assert result["sent"] is True
    assert sum(1 for call in DummySMTP.calls if call[0] == "sendmail") == 1
