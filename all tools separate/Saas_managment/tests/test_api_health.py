from fastapi.testclient import TestClient

from api.main import app
from processing.context_builder import build_context


def test_health_matches_context():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    ctx = build_context()
    data = response.json()
    assert data["audit_date"] == ctx.audit_date
    assert data["active_vendors"] == ctx.active_vendors
    assert data["fetched_at"] == ctx.fetched_at
