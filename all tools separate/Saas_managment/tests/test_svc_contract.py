import pytest

from exceptions import DataNotReadyError
from services import contract_service


ENTITLEMENT_KEYS = {
    "vendor",
    "sku",
    "seat_type",
    "effective_total_seats",
    "unit_price",
    "notice_deadline",
    "auto_renewal",
    "true_down_rights",
    "measurement_method",
    "contract_status",
}

ACTIVE_CONTRACT_KEYS = {
    "of_id",
    "vendor",
    "sku",
    "seat_type",
    "contracted_seats",
    "effective_total_seats",
    "unit_price",
    "contract_start",
    "contract_expiry",
    "notice_deadline",
    "auto_renewal",
    "true_down_rights",
    "measurement_method",
    "contract_event_type",
    "contract_group_id",
}

HISTORY_KEYS = {
    "of_id",
    "vendor",
    "sku",
    "seat_type",
    "contracted_seats",
    "effective_total_seats",
    "unit_price",
    "contract_start",
    "contract_expiry",
    "contract_status",
    "contract_event_type",
    "predecessor_of_id",
    "seat_delta",
    "contract_group_id",
}


def test_get_entitlement_returns_list(default_version):
    assert isinstance(contract_service.get_entitlement(version=default_version), list)


def test_get_entitlement_no_duplicates(default_version):
    rows = contract_service.get_entitlement(version=default_version)
    combos = {(row["vendor"], row["sku"], row["seat_type"]) for row in rows}
    assert len(combos) == len(rows)


def test_get_entitlement_only_active_status(default_version):
    rows = contract_service.get_entitlement(version=default_version)
    assert all(row["contract_status"] == "active" for row in rows)


def test_get_entitlement_effective_seats_positive(default_version):
    rows = contract_service.get_entitlement(version=default_version)
    assert all(row["effective_total_seats"] > 0 for row in rows)


def test_get_entitlement_active_vendors_only(default_version, active_vendors):
    rows = contract_service.get_entitlement(version=default_version)
    assert {row["vendor"] for row in rows} == set(active_vendors)


def test_get_entitlement_vendor_filter_first_vendor(default_version, active_vendors):
    vendor = active_vendors[0]
    rows = contract_service.get_entitlement(vendor=vendor, version=default_version)
    assert rows and all(row["vendor"] == vendor for row in rows)


def test_get_entitlement_vendor_filter_second_vendor(default_version, active_vendors):
    vendor = active_vendors[1]
    rows = contract_service.get_entitlement(vendor=vendor, version=default_version)
    assert rows and all(row["vendor"] == vendor for row in rows)


def test_get_entitlement_columns_exact(default_version):
    rows = contract_service.get_entitlement(version=default_version)
    assert rows and set(rows[0].keys()) == ENTITLEMENT_KEYS


def test_get_entitlement_unit_price_positive(default_version):
    rows = contract_service.get_entitlement(version=default_version)
    assert all(row["unit_price"] > 0 for row in rows)


def test_get_active_contracts_returns_list(default_version):
    assert isinstance(contract_service.get_active_contracts(version=default_version), list)


def test_get_active_contracts_of_id_unique(default_version):
    rows = contract_service.get_active_contracts(version=default_version)
    assert len({row["of_id"] for row in rows}) == len(rows)


def test_get_active_contracts_no_superseded(default_version):
    rows = contract_service.get_active_contracts(version=default_version)
    assert rows and all("contract_status" not in row for row in rows)


def test_get_active_contracts_vendor_filter(default_version, active_vendors):
    vendor = active_vendors[2]
    rows = contract_service.get_active_contracts(vendor=vendor, version=default_version)
    assert rows and all(row["vendor"] == vendor for row in rows)


def test_get_active_contracts_columns_exact(default_version):
    rows = contract_service.get_active_contracts(version=default_version)
    assert rows and set(rows[0].keys()) == ACTIVE_CONTRACT_KEYS


def test_get_contract_history_ordered_by_start(default_version, active_vendors):
    rows = contract_service.get_contract_history(
        vendor=active_vendors[0],
        sku="Project Suite",
        seat_type="Full",
        version=default_version,
    )
    starts = [row["contract_start"] for row in rows]
    assert starts == sorted(starts)


def test_get_contract_history_includes_superseded(default_version, active_vendors):
    rows = contract_service.get_contract_history(
        vendor=active_vendors[0],
        sku="Project Suite",
        seat_type="Full",
        version=default_version,
    )
    assert any(row["contract_status"] == "superseded" for row in rows)


def test_get_contract_history_returns_superseded_rows(default_version):
    rows = contract_service.get_contract_history(version=default_version)

    assert rows
    assert any(row["contract_status"] == "superseded" for row in rows)


def test_get_contract_history_vendor_filter(default_version):
    rows = contract_service.get_contract_history(vendor="Atlassify", version=default_version)

    assert rows
    assert {row["vendor"] for row in rows} == {"Atlassify"}


def test_get_contract_history_count_exceeds_active_contracts(default_version):
    history = contract_service.get_contract_history(version=default_version)
    active = contract_service.get_active_contracts(version=default_version)

    assert len(history) > len(active)


def test_get_contract_history_unknown_combo_raises(default_version, active_vendors):
    with pytest.raises(DataNotReadyError):
        contract_service.get_contract_history(
            vendor=active_vendors[0],
            version=default_version,
            sku="NonExistentSKU",
            seat_type="Full",
        )


def test_get_contract_history_columns_exact(default_version, active_vendors):
    rows = contract_service.get_contract_history(
        vendor=active_vendors[0],
        version=default_version,
        sku="Project Suite",
        seat_type="Full",
    )
    assert rows and set(rows[0].keys()) == HISTORY_KEYS
