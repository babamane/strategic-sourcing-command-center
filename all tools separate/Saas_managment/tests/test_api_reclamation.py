from fastapi.testclient import TestClient

from api.main import app
from processing.context_builder import build_context
from processing.reclamation_detector import get_reclamation_candidates


def test_reclamation_min_score_and_ordering():
    client = TestClient(app)
    ctx = build_context()
    min_score = 0.45
    proc = get_reclamation_candidates(ctx, min_score=min_score)
    r = client.get("/reclamation", params={"min_score": min_score})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == len(proc)
    scores = [row["reclamation_score"] for row in rows]
    assert scores == sorted(scores, reverse=True)
    assert all(row["reclamation_score"] >= min_score - 1e-9 for row in rows)
    assert all(row["license_status"] != "ghost" for row in rows)
