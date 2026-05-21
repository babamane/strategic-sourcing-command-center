from datetime import date

from services import contract_service, employee_service, license_service


def test_vendors_are_consistent(default_version, active_vendors):
    entitlement_vendors = {row["vendor"] for row in contract_service.get_entitlement(version=default_version)}
    raw_license_vendors = {
        row["vendor"] for row in license_service.get_raw_licenses(version=default_version)
    }

    assert entitlement_vendors == set(active_vendors)
    assert raw_license_vendors == set(active_vendors)


def test_employee_and_license_join_keys_align(default_version):
    active_employees = employee_service.get_active_employees(version=default_version)
    exited_employees = employee_service.get_exited_employees(version=default_version)
    future_hires = employee_service.get_future_hires(version=default_version)

    known_emails = {row["email"] for row in active_employees}
    known_emails.update(row["email"] for row in exited_employees)
    known_emails.update(row["email"] for row in future_hires)

    raw_licenses = license_service.get_raw_licenses(version=default_version)
    assert all(row["assigned_email"] in known_emails for row in raw_licenses)


def test_sub_team_resolves_for_active_employees(default_version):
    active_employees = employee_service.get_active_employees(version=default_version)

    assert any(row.get("sub_team") for row in active_employees)


def test_sub_team_resolves_for_future_hires(default_version):
    future_hires = employee_service.get_future_hires(version=default_version)

    assert future_hires and all("sub_team" in row for row in future_hires)


def test_future_hires_respect_audit_window(default_version):
    future_hires = employee_service.get_future_hires(version=default_version)
    may_window = employee_service.get_future_hires(before_date=date(2026, 5, 31), version=default_version)

    assert len(may_window) == 80
    assert all(row["hire_date"] > date(2026, 5, 1) for row in future_hires)


def test_ghost_emails_resolve_to_exited_employees(default_version):
    ghost_licenses = license_service.get_raw_licenses(status_filter=["ghost"], version=default_version)
    exited_emails = {row["email"] for row in employee_service.get_exited_employees(version=default_version)}

    assert all(row["assigned_email"] in exited_emails for row in ghost_licenses)


def test_active_provisioned_rows_use_expected_statuses(default_version, active_vendors):
    active_licenses = license_service.get_raw_licenses(
        status_filter=["active", "over_tier"],
        version=default_version,
    )
    assert active_licenses
    assert {row["vendor"] for row in active_licenses} == set(active_vendors)
    assert {row["license_status"] for row in active_licenses}.issubset({"active", "over_tier"})


def test_future_hires_not_in_any_license_status(default_version):
    future_hires = employee_service.get_future_hires(version=default_version)
    raw_licenses = license_service.get_raw_licenses(version=default_version)
    all_license_emails = {row["assigned_email"] for row in raw_licenses}

    assert all(row["email"] not in all_license_emails for row in future_hires)


def test_entitlement_vendors_match_license_vendors(default_version):
    entitlement_vendors = {row["vendor"] for row in contract_service.get_entitlement(version=default_version)}
    active_license_vendors = {
        row["vendor"]
        for row in license_service.get_raw_licenses(
            status_filter=["active", "over_tier"],
            version=default_version,
        )
    }

    assert entitlement_vendors == active_license_vendors


def test_no_email_in_multiple_status_groups(default_version):
    active_emails = {row["email"] for row in employee_service.get_active_employees(version=default_version)}
    exited_emails = {row["email"] for row in employee_service.get_exited_employees(version=default_version)}
    future_hires = {row["email"] for row in employee_service.get_future_hires(version=default_version)}

    assert active_emails.isdisjoint(exited_emails)
    assert active_emails.isdisjoint(future_hires)
    assert exited_emails.isdisjoint(future_hires)


def test_license_vendor_sku_in_contracts(default_version):
    contract_pairs = {
        (row["vendor"], row["sku"])
        for row in contract_service.get_active_contracts(version=default_version)
    }
    raw_pairs = {
        (row["vendor"], row["sku"])
        for row in license_service.get_raw_licenses(
            status_filter=["active", "over_tier"],
            version=default_version,
        )
    }

    assert raw_pairs.issubset(contract_pairs)


def test_ghost_count_for_first_vendor(default_version, active_vendors):
    rows = license_service.get_raw_licenses(
        vendor=active_vendors[0],
        status_filter=["ghost"],
        version=default_version,
    )
    assert len(rows) == 1817


def test_expired_renewal_urgency_by_vendor(default_version, active_vendors):
    nexaflow = license_service.get_raw_licenses(vendor=active_vendors[1], version=default_version)
    cloudora = license_service.get_raw_licenses(vendor=active_vendors[2], version=default_version)

    assert sum(1 for row in nexaflow if row["renewal_urgency"] == "expired") == 261
    assert sum(1 for row in cloudora if row["renewal_urgency"] == "expired") == 218
