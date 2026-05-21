from processing.context_builder import build_context
from processing.reclamation_detector import get_reclamation_candidates


def test_reclamation_candidates_ranked_and_filterable():
    ctx = build_context()
    rows = get_reclamation_candidates(ctx)

    assert rows
    assert all(row.computed_at for row in rows)
    assert all(row.license_status in {"active", "over_tier"} for row in rows)
    assert all(row.license_status != "ghost" for row in rows)
    assert all(row.reclamation_score >= 0.45 for row in rows)
    assert min(row.reclamation_score for row in rows) < 0.7
    assert rows == sorted(rows, key=lambda row: (row.reclamation_score, row.monthly_cost), reverse=True)
    assert {row.vendor for row in get_reclamation_candidates(ctx, vendor="Atlassify")} == {"Atlassify"}
    assert get_reclamation_candidates(ctx, vendor="NotAVendor") == []

