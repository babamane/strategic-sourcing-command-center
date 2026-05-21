from fastapi.testclient import TestClient

from api.main import app
from processing.context_builder import build_context


def _vendor():
    return build_context().active_vendors[0]


def test_ghost_ticket_preview():
    client = TestClient(app)

    response = client.post("/triggers/ghost-ticket", json={"vendor": _vendor(), "confirmed": False})

    assert response.status_code == 200
    body = response.json()
    assert body["preview"] is True
    assert body["count"] > 0


def test_ghost_ticket_confirmed(monkeypatch):
    monkeypatch.setattr("api.routers.triggers.insert_recommendation", lambda payload: "rec-test")
    client = TestClient(app)

    response = client.post("/triggers/ghost-ticket", json={"vendor": _vendor(), "confirmed": True})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert body["recommendation_id"] == "rec-test"


def test_reclamation_preview():
    client = TestClient(app)

    response = client.post("/triggers/reclamation", json={"vendor": _vendor(), "confirmed": False})

    assert response.status_code == 200
    body = response.json()
    assert body["preview"] is True
    assert body["count"] > 0


def test_reclamation_confirmed(monkeypatch):
    monkeypatch.setattr("api.routers.triggers.insert_recommendation", lambda payload: "rec-test")
    monkeypatch.setattr(
        "api.routers.triggers.dispatch_csv",
        lambda payload: {"status": "ok", "integration": "csv", "path": "mock.csv"},
    )
    client = TestClient(app)

    response = client.post("/triggers/reclamation", json={"vendor": _vendor(), "confirmed": True})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert body["integration"] == "csv"
    assert body["recommendation_id"] == "rec-test"


def test_rightsizing_preview():
    client = TestClient(app)

    response = client.post("/triggers/rightsizing", json={"vendor": _vendor(), "confirmed": False})

    assert response.status_code == 200
    body = response.json()
    assert body["preview"] is True
    assert body["count"] > 0


def test_rightsizing_confirmed(monkeypatch):
    monkeypatch.setattr("api.routers.triggers.insert_recommendation", lambda payload: "rec-test")
    client = TestClient(app)

    response = client.post("/triggers/rightsizing", json={"vendor": _vendor(), "confirmed": True})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert body["integration"] == "slack"
    assert body["recommendation_id"] == "rec-test"


def test_renewal_alert_preview():
    client = TestClient(app)

    response = client.post("/triggers/renewal-alert", json={"vendor": _vendor(), "confirmed": False})

    assert response.status_code == 200
    body = response.json()
    assert body["preview"] is True
    assert body["count"] >= 0


def test_renewal_alert_confirmed(monkeypatch):
    monkeypatch.setattr("api.routers.triggers.insert_recommendation", lambda payload: "rec-test")
    client = TestClient(app)

    response = client.post("/triggers/renewal-alert", json={"vendor": _vendor(), "confirmed": True})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert body["recommendation_id"] == "rec-test"


def test_reclamation_review_preview():
    client = TestClient(app)

    response = client.post("/triggers/reclamation-review", json={"vendor": _vendor(), "confirmed": False})

    assert response.status_code == 200
    body = response.json()
    assert body["preview"] is True
    assert body["count"] > 0


def test_reclamation_review_confirmed(monkeypatch):
    monkeypatch.setattr("api.routers.triggers.insert_recommendation", lambda payload: "rec-test")
    client = TestClient(app)

    response = client.post(
        "/triggers/reclamation-review",
        json={"vendor": _vendor(), "confirmed": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert body["recommendation_id"] == "rec-test"
