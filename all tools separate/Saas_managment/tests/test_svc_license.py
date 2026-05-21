from services import license_service


RAW_LICENSE_KEYS = {
    "license_id",
    "vendor",
    "sku",
    "seat_type",
    "assigned_email",
    "employee_id",
    "department",
    "job_level",
    "provisioned_date",
    "last_active_date",
    "license_status",
    "usage_tier",
    "seat_tier_match",
    "monthly_cost",
    "cost_at_risk",
    "annual_cost",
    "active_usage_rate",
    "login_events_30d",
    "days_since_last_active",
    "days_since_provisioned",
    "contract_days_remaining",
    "days_until_notice",
    "renewal_urgency",
    "notice_deadline",
    "auto_renewal",
    "true_down_rights",
    "measurement_method",
    "current_of_id",
    "of_id",
    "reclamation_candidate",
    "churn_risk_score",
}


def test_get_raw_licenses_returns_list(default_version):
    assert isinstance(license_service.get_raw_licenses(version=default_version), list)


def test_get_raw_licenses_active_vendors_only(default_version, active_vendors):
    rows = license_service.get_raw_licenses(version=default_version)
    assert {row["vendor"] for row in rows} == set(active_vendors)


def test_get_raw_licenses_no_filter_all_statuses_present(default_version):
    rows = license_service.get_raw_licenses(version=default_version)
    statuses = {row["license_status"] for row in rows}
    assert {"active", "ghost", "deprovisioned", "over_tier"}.issubset(statuses)


def test_get_raw_licenses_columns_exact_count(default_version):
    rows = license_service.get_raw_licenses(version=default_version)
    assert rows and len(rows[0].keys()) == 31


def test_get_raw_licenses_required_columns_present(default_version):
    rows = license_service.get_raw_licenses(version=default_version)
    assert rows and set(rows[0].keys()) == RAW_LICENSE_KEYS


def test_get_raw_licenses_status_filter_active_overtier(default_version):
    rows = license_service.get_raw_licenses(
        status_filter=["active", "over_tier"],
        version=default_version,
    )
    assert rows and all(row["license_status"] in {"active", "over_tier"} for row in rows)


def test_get_raw_licenses_status_filter_ghost_only(default_version):
    rows = license_service.get_raw_licenses(status_filter=["ghost"], version=default_version)
    assert rows and all(row["license_status"] == "ghost" for row in rows)


def test_get_raw_licenses_vendor_filter(default_version, active_vendors):
    vendor = active_vendors[0]
    rows = license_service.get_raw_licenses(vendor=vendor, version=default_version)
    assert rows and all(row["vendor"] == vendor for row in rows)


def test_get_raw_licenses_ghost_count_for_first_vendor(default_version, active_vendors):
    vendor = active_vendors[0]
    rows = license_service.get_raw_licenses(
        vendor=vendor,
        status_filter=["ghost"],
        version=default_version,
    )
    assert len(rows) == 1817


def test_get_raw_licenses_monthly_cost_positive(default_version):
    rows = license_service.get_raw_licenses(version=default_version)
    assert all(row["monthly_cost"] > 0 for row in rows)


def test_get_raw_licenses_cost_at_risk_zero_for_active(default_version):
    rows = license_service.get_raw_licenses(status_filter=["active"], version=default_version)
    assert rows and all(row["cost_at_risk"] >= 0 for row in rows)


def test_get_raw_licenses_null_churn_for_ghost(default_version):
    rows = license_service.get_raw_licenses(status_filter=["ghost"], version=default_version)
    assert rows and all(row["churn_risk_score"] is None for row in rows)


def test_get_raw_licenses_null_churn_for_deprovisioned(default_version):
    rows = license_service.get_raw_licenses(status_filter=["deprovisioned"], version=default_version)
    assert rows and all(row["churn_risk_score"] is None for row in rows)


def test_get_raw_licenses_null_last_active_for_deprovisioned(default_version):
    rows = license_service.get_raw_licenses(status_filter=["deprovisioned"], version=default_version)
    assert rows and all(row["last_active_date"] is None for row in rows)


def test_get_raw_licenses_expired_urgency_by_vendor(default_version, active_vendors):
    nexaflow = license_service.get_raw_licenses(vendor=active_vendors[1], version=default_version)
    cloudora = license_service.get_raw_licenses(vendor=active_vendors[2], version=default_version)

    assert sum(1 for row in nexaflow if row["renewal_urgency"] == "expired") == 261
    assert sum(1 for row in cloudora if row["renewal_urgency"] == "expired") == 218
