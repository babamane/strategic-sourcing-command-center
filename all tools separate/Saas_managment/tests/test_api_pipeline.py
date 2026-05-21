"""Tests for pipeline API endpoints."""

from __future__ import annotations

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_pipeline_state():
    from api.pipeline_state import _runs
    _runs.clear()

class TestUploadValidFile:
    """POST /pipeline/upload with valid license_utilization CSV → HTTP 200."""

    def test_upload_valid_file(self):
        csv_content = b"license_id,vendor,sku\n1,Atlassify,Pro\n"
        response = client.post(
            "/v1/pipeline/upload",
            files={"file": ("license_utilization_v5.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "license_utilization"
        assert data["filename"] == "license_utilization_v5.csv"
        assert data["size_bytes"] > 0


class TestUploadUnknownFilename:
    """POST /pipeline/upload with random_data.csv → HTTP 400."""

    def test_upload_unknown_filename(self):
        csv_content = b"col1,col2\na,b\n"
        response = client.post(
            "/v1/pipeline/upload",
            files={"file": ("random_data.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert response.status_code == 400


class TestVersionsReturnsDict:
    """GET /pipeline/versions → HTTP 200, dict with known keys."""

    def test_versions_returns_dict(self):
        response = client.get("/v1/pipeline/versions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Live DB has promoted versions
        if data:
            for table_name, info in data.items():
                assert "version" in info
                assert "promoted_at" in info


class TestRunReturnsRunId:
    """POST /pipeline/run → HTTP 200, run_id is a valid UUID string."""

    def test_run_returns_run_id(self):
        with patch("api.routers.pipeline._execute_pipeline"):
            response = client.post("/v1/pipeline/run")
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert len(data["run_id"]) == 36  # UUID format


class TestStatusReturnsRun:
    """GET /pipeline/status/{run_id} → HTTP 200, status field present."""

    def test_status_returns_run(self):
        # Create a run first
        with patch("api.routers.pipeline._execute_pipeline"):
            run_resp = client.post("/v1/pipeline/run")

        run_id = run_resp.json()["run_id"]
        response = client.get(f"/v1/pipeline/status/{run_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "steps" in data


class TestStatus404UnknownRun:
    """GET /pipeline/status/nonexistent → HTTP 404."""

    def test_status_404_unknown_run(self):
        response = client.get("/v1/pipeline/status/nonexistent-run-id")
        assert response.status_code == 404


class TestDoubleRunRejected:
    """Second POST /pipeline/run while first is running → HTTP 409."""

    def test_double_run_rejected(self):
        with patch("api.routers.pipeline._execute_pipeline"):
            first = client.post("/v1/pipeline/run")
        assert first.status_code == 200

        # Second run while first is still "running"
        second = client.post("/v1/pipeline/run")
        assert second.status_code == 409
