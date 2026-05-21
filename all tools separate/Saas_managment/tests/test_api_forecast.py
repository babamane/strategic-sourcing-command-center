from fastapi.testclient import TestClient

from api.main import app
from processing.active_demand_processor import get_active_demand_history, get_active_demand_series
from processing.context_builder import build_context
from processing.license_demand_forecaster import get_license_demand_forecast


def test_forecast_demand_rowcount():
    client = TestClient(app)
    ctx = build_context()
    months = 8
    proc = get_license_demand_forecast(ctx, forecast_months=months)
    r = client.get("/forecast/demand", params={"months": months})
    assert r.status_code == 200
    assert len(r.json()) == len(proc)


def test_forecast_demand_response_includes_new_fields():
    client = TestClient(app)
    response = client.get("/forecast/demand", params={"months": 8})

    assert response.status_code == 200
    payload = response.json()
    assert payload
    row = payload[0]
    for field in (
        "baseline_active",
        "projected_active",
        "contracted_capacity",
        "projected_over_capacity",
        "exit_licenses_applied",
    ):
        assert field in row


def test_active_demand_route_returns_200():
    client = TestClient(app)
    response = client.get("/forecast/active-demand")

    assert response.status_code == 200
    assert response.json()


def test_active_demand_response_shape():
    client = TestClient(app)
    ctx = build_context()
    proc = get_active_demand_history(ctx)
    response = client.get("/forecast/active-demand")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == len(proc)
    row = payload[0]
    for field in (
        "vendor",
        "sku",
        "seat_type",
        "month",
        "productive_active",
        "vendor_billed",
        "ghost_count",
        "contracted_capacity",
        "over_capacity",
    ):
        assert field in row


def test_active_demand_series_route_returns_200():
    client = TestClient(app)
    response = client.get("/forecast/active-demand-series")

    assert response.status_code == 200
    assert response.json()


def test_active_demand_series_response_shape():
    client = TestClient(app)
    ctx = build_context()
    proc = get_active_demand_series(ctx)
    response = client.get("/forecast/active-demand-series")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == len(proc)
    row = payload[0]
    for field in (
        "vendor",
        "sku",
        "seat_type",
        "month",
        "is_forecast",
        "productive_active",
        "vendor_billed",
        "ghost_count",
        "projected_active",
        "contracted_capacity",
        "projected_over_capacity",
        "pipeline_data_available",
    ):
        assert field in row
