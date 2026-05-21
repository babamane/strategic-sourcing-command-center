from processing.context_builder import build_context
from processing.trueup_processor import get_trueup_exposure


def test_trueup_happy_path_and_filter():
    ctx = build_context()
    rows = get_trueup_exposure(ctx)

    assert rows
    assert all(row.computed_at for row in rows)
    assert {row.vendor for row in get_trueup_exposure(ctx, vendor="Nexaflow")} == {"Nexaflow"}
    assert get_trueup_exposure(ctx, vendor="NotAVendor") == []


def test_trueup_arithmetic_spot_check():
    ctx = build_context()
    row = get_trueup_exposure(ctx)[0]

    assert row.exposure_seats == max(0, row.active_provisioned_seats - row.effective_total_seats)
    assert row.shelfware_seats == max(0, row.effective_total_seats - row.active_provisioned_seats)
    assert row.exposure_amount_annual == round(row.exposure_seats * row.unit_price * 12, 2)

