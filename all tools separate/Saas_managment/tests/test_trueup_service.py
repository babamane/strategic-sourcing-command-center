import pytest

from services import trueup_service


def test_compute_snapshot_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        trueup_service.compute_snapshot()


def test_get_latest_snapshot_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        trueup_service.get_latest_snapshot()


def test_get_snapshot_history_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        trueup_service.get_snapshot_history()


def test_compute_snapshot_with_vendor_raises():
    with pytest.raises(NotImplementedError):
        trueup_service.compute_snapshot(vendor="Atlassify")

