from processing.context_builder import build_context
from processing.utilization_aggregator import USAGE_TIERS, get_utilization_summary


def test_utilization_summary_rates_and_tiers():
    ctx = build_context()
    rows = get_utilization_summary(ctx)

    assert rows
    assert all(row.computed_at for row in rows)
    assert all(set(row.by_usage_tier) == set(USAGE_TIERS) for row in rows)
    assert all(0 <= row.active_rate <= 1 for row in rows)
    assert {row.vendor for row in get_utilization_summary(ctx, vendor="Nexaflow")} == {"Nexaflow"}
    assert get_utilization_summary(ctx, vendor="NotAVendor") == []

