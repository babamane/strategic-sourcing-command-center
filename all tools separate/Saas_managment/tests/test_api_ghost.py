from fastapi.testclient import TestClient

from api.main import app
from processing.context_builder import build_context
from processing.ghost_detector import get_ghost_detail, get_ghost_summary


def test_ghost_summary_totals_match_processor():
    client = TestClient(app)
    ctx = build_context()
    proc_total = sum(row.ghost_license_count for row in get_ghost_summary(ctx))
    r = client.get("/ghost/summary")
    assert r.status_code == 200
    api_total = sum(row["ghost_license_count"] for row in r.json())
    assert api_total == proc_total


def test_ghost_detail_matches_processor_optional_department():
    client = TestClient(app)
    ctx = build_context()
    vendor = ctx.active_vendors[0]
    proc_rows = get_ghost_detail(ctx, vendor=vendor)
    r = client.get("/ghost/detail", params={"vendor": vendor})
    assert r.status_code == 200
    assert len(r.json()) == len(proc_rows)
