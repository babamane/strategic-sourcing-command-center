from fastapi.testclient import TestClient

from api.main import app
from processing.context_builder import build_context
from processing.utilization_aggregator import get_utilization_summary


def test_utilization_rowcount_and_portfolio_active_rate():
    client = TestClient(app)
    ctx = build_context()
    proc_rows = get_utilization_summary(ctx)
    r = client.get("/utilization")
    assert r.status_code == 200
    api_rows = r.json()
    assert len(api_rows) == len(proc_rows)
    total_lic = sum(row.total_licenses for row in proc_rows)
    weighted = sum(row.active_rate * row.total_licenses for row in proc_rows) / total_lic if total_lic else 0.0
    api_weighted = sum(row["active_rate"] * row["total_licenses"] for row in api_rows) / total_lic
    assert abs(weighted - api_weighted) < 1e-6
