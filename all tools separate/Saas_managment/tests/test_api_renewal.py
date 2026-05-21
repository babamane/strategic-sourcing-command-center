from fastapi.testclient import TestClient

from api.main import app
from processing.context_builder import build_context
from processing.license_demand_forecaster import get_license_demand_forecast
from processing.renewal_pressure_forecaster import get_renewal_pressure


def test_renewal_pressure_expired_nexaflow_cloudora():
    client = TestClient(app)
    ctx = build_context()
    proc_expired = [
        row
        for row in get_renewal_pressure(ctx)
        if row.vendor in {"Nexaflow", "Cloudora"} and row.renewal_urgency == "expired"
    ]
    assert proc_expired
    r = client.get("/renewal-pressure")
    assert r.status_code == 200
    payload = r.json()
    for row in proc_expired:
        matches = [
            item
            for item in payload
            if item["vendor"] == row.vendor and item["sku"] == row.sku and item["seat_type"] == row.seat_type
        ]
        assert matches
        assert matches[0]["renewal_urgency"] == "expired"


def test_renewal_hires_before_deadline_matches_projected_active():
    client = TestClient(app)
    ctx = build_context()
    demand_rows = get_license_demand_forecast(ctx, forecast_months=8)
    renewal_rows = get_renewal_pressure(ctx)

    target = None
    matching = []
    for row in renewal_rows:
        if not row.notice_deadline:
            continue
        candidate_rows = [
            demand_row for demand_row in demand_rows
            if (demand_row.vendor, demand_row.sku, demand_row.seat_type) == (row.vendor, row.sku, row.seat_type)
            and demand_row.forecast_month <= row.notice_deadline[:7]
        ]
        if candidate_rows:
            target = row
            matching = candidate_rows
            break

    assert target is not None
    expected = max(matching, key=lambda row: row.forecast_month).projected_active

    response = client.get("/renewal-pressure")
    assert response.status_code == 200
    payload = next(
        item for item in response.json()
        if item["vendor"] == target.vendor and item["sku"] == target.sku and item["seat_type"] == target.seat_type
    )
    assert payload["hires_before_deadline"] == expected
