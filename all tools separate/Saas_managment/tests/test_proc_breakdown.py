from processing.breakdown_enricher import get_trueup_breakdown
from processing.context_builder import build_context


def test_breakdown_returns_department_and_job_level_rollups():
    ctx = build_context()
    rows = get_trueup_breakdown(ctx)

    assert rows
    assert all(row.computed_at for row in rows)
    assert all(row.by_department for row in rows)
    assert all(row.by_job_level for row in rows)
    assert {row.vendor for row in get_trueup_breakdown(ctx, vendor="Nexaflow")} == {"Nexaflow"}
    assert get_trueup_breakdown(ctx, vendor="NotAVendor") == []

