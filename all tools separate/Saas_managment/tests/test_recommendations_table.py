import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from db import recommendations_table as rt


@pytest.fixture
def isolated_recommendations_db(monkeypatch):
    path = Path(f"rec_test_{uuid4().hex}.db")
    path.unlink(missing_ok=True)
    connections = []

    def _open():
        conn = sqlite3.connect(path)
        connections.append(conn)
        return conn

    monkeypatch.setattr(rt, "open_database_connection", _open)
    rt.ensure_recommendations_table()
    yield path
    for conn in connections:
        conn.close()
    path.unlink(missing_ok=True)


def test_insert_and_get_pending_roundtrip(isolated_recommendations_db):
    payload = {
        "vendor": "Veloxa",
        "action_type": "reclamation",
        "seat_delta": -3,
        "dollar_impact": 1200.5,
        "affected_records": [{"id": "a"}],
        "recommended_action": "reclaim",
    }
    rec_id = rt.insert_recommendation(payload)
    assert rec_id.startswith("rec-")
    pending = rt.get_pending_recommendations()
    assert len(pending) == 1
    assert pending[0]["status"] == "pending"
    assert pending[0]["affected_records"] == [{"id": "a"}]
    one = rt.get_recommendation_by_id(rec_id)
    assert one is not None
    assert one["vendor"] == "Veloxa"


def test_get_pending_vendor_filter(isolated_recommendations_db):
    rt.insert_recommendation(
        {
            "vendor": "A",
            "action_type": "ghost_review",
            "seat_delta": -1,
            "dollar_impact": 1.0,
            "affected_records": [],
            "recommended_action": "deprovision_review",
        }
    )
    rt.insert_recommendation(
        {
            "vendor": "B",
            "action_type": "ghost_review",
            "seat_delta": -1,
            "dollar_impact": 1.0,
            "affected_records": [],
            "recommended_action": "deprovision_review",
        }
    )
    rows = rt.get_pending_recommendations(vendor="B")
    assert len(rows) == 1
    assert rows[0]["vendor"] == "B"
