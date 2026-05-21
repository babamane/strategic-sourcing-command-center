import pytest

from services import forecast_service


def test_get_renewal_pressure_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        forecast_service.get_renewal_pressure()


def test_get_pressure_summary_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        forecast_service.get_pressure_summary()


def test_get_headcount_driven_demand_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        forecast_service.get_headcount_driven_demand("Nexaflow", "Flow Automation", "Contributor")

