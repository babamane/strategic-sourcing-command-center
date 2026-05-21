from fastapi.testclient import TestClient

from api.main import app
from processing.breakdown_enricher import get_trueup_breakdown
from processing.context_builder import build_context
from processing.trueup_processor import get_trueup_exposure


def test_trueup_exposure_rowcount_and_vendor_scope():
    client = TestClient(app)
    ctx = build_context()
    proc_rows = get_trueup_exposure(ctx)
    r = client.get("/trueup/exposure")
    assert r.status_code == 200
    assert len(r.json()) == len(proc_rows)

    vendor = ctx.active_vendors[0]
    scoped = client.get("/trueup/exposure", params={"vendor": vendor})
    assert scoped.status_code == 200
    assert {row["vendor"] for row in scoped.json()} == {vendor}


def test_trueup_breakdown_matches_processor():
    client = TestClient(app)
    ctx = build_context()
    proc_exp = get_trueup_exposure(ctx)
    assert proc_exp
    top = proc_exp[0]
    proc = get_trueup_breakdown(ctx, vendor=top.vendor, sku=top.sku, seat_type=top.seat_type)
    api = client.get(
        "/trueup/breakdown",
        params={"vendor": top.vendor, "sku": top.sku, "seat_type": top.seat_type},
    )
    assert api.status_code == 200
    assert len(api.json()) == len(proc)
