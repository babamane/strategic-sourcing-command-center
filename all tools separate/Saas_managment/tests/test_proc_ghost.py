from processing.context_builder import build_context
from processing.ghost_detector import get_ghost_details, get_ghost_summary


def test_ghost_summary_and_details():
    ctx = build_context()
    summary = get_ghost_summary(ctx)
    details = get_ghost_details(ctx)

    assert summary
    assert details
    assert all(row.computed_at for row in summary)
    assert all(row.computed_at for row in details)
    assert sum(row.ghost_license_count for row in summary) == len(details)
    assert {row.vendor for row in get_ghost_summary(ctx, vendor="Cloudora")} == {"Cloudora"}
    assert get_ghost_summary(ctx, vendor="NotAVendor") == []


def test_ghost_details_exclude_future_hires():
    ctx = build_context()
    future_ids = {row["employee_id"] for row in ctx.future_hires}

    assert not ({row.employee_id for row in get_ghost_details(ctx)} & future_ids)

