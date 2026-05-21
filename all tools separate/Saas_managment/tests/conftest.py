import pytest
import os
from datetime import date


@pytest.fixture(scope="session")
def audit_date():
    return date(2026, 5, 1)


@pytest.fixture(scope="session")
def default_version():
    return None


@pytest.fixture(scope="session")
def active_vendors():
    raw = os.getenv("ACTIVE_VENDORS", "")
    vendors = [value.strip() for value in raw.split(",") if value.strip()]
    assert vendors, "ACTIVE_VENDORS env var is not set or empty"
    return vendors


@pytest.fixture(scope="session")
def row_count_threshold():
    return float(os.getenv("ROW_COUNT_DEVIATION_THRESHOLD", "0.05"))
