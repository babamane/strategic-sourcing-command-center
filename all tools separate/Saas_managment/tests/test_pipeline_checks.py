"""Tests for pipeline checks and trial runner — all monkeypatched, no live DB required."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, call
from dataclasses import asdict

from pipeline.checks import CheckResult


# ---------------------------------------------------------------------------
# Ingestion checks
# ---------------------------------------------------------------------------

class TestRowCountWithinThreshold:
    """check_ingestion() passes when new count is within 5% of previous."""

    def test_row_count_within_threshold(self):
        mock_conn = MagicMock()

        # We need to carefully track which execute call returns what
        pending_result = MagicMock()
        pending_result.fetchone.return_value = (16649, "abc123")

        prev_result = MagicMock()
        prev_result.fetchone.return_value = (16000, "abc123")

        table_exists_result = MagicMock()
        table_exists_result.fetchone.return_value = ("license_utilization_v4",)

        count_result = MagicMock()
        count_result.fetchone.return_value = (16649,)

        pragma_result = MagicMock()
        pragma_result.fetchall.return_value = [
            (0, "days_since_last_active", "TEXT", 0, None, 0),
        ]

        mock_conn.execute.side_effect = [
            pending_result,       # data_versions for pending
            prev_result,          # data_versions for previous
            table_exists_result,  # sqlite_master check
            count_result,         # COUNT(*)
            pragma_result,        # PRAGMA table_info
        ]

        with patch("db.connection.open_database_connection", return_value=mock_conn):
            from pipeline.checks import check_ingestion
            results = check_ingestion("license_utilization", 4)

        row_check = [r for r in results if r.check_name == "row_count_deviation"]
        assert len(row_check) >= 1
        assert row_check[0].passed is True


class TestRowCountExceedsThreshold:
    """check_ingestion() fails when deviation > 5%."""

    def test_row_count_exceeds_threshold(self):
        mock_conn = MagicMock()

        pending_result = MagicMock()
        pending_result.fetchone.return_value = (20000, "abc123")

        prev_result = MagicMock()
        prev_result.fetchone.return_value = (16000, "abc123")

        table_exists_result = MagicMock()
        table_exists_result.fetchone.return_value = ("license_utilization_v4",)

        count_result = MagicMock()
        count_result.fetchone.return_value = (20000,)

        pragma_result = MagicMock()
        pragma_result.fetchall.return_value = [
            (0, "days_since_last_active", "TEXT", 0, None, 0),
        ]

        mock_conn.execute.side_effect = [
            pending_result,
            prev_result,
            table_exists_result,
            count_result,
            pragma_result,
        ]

        with patch("db.connection.open_database_connection", return_value=mock_conn):
            from pipeline.checks import check_ingestion
            results = check_ingestion("license_utilization", 4, deviation_threshold=0.05)

        row_check = [r for r in results if r.check_name == "row_count_deviation"]
        assert len(row_check) >= 1
        assert row_check[0].passed is False
        assert "EXCEEDED" in row_check[0].message


class TestSchemaFingerprintChangeIsWarning:
    """Fingerprint change → passed=True, message contains 'SCHEMA CHANGE'."""

    def test_schema_fingerprint_change_is_warning_not_failure(self):
        mock_conn = MagicMock()

        pending_result = MagicMock()
        pending_result.fetchone.return_value = (16649, "new_fingerprint")

        prev_result = MagicMock()
        prev_result.fetchone.return_value = (16000, "old_fingerprint")

        table_exists_result = MagicMock()
        table_exists_result.fetchone.return_value = ("vendor_overview_v2",)

        count_result = MagicMock()
        count_result.fetchone.return_value = (16649,)

        mock_conn.execute.side_effect = [
            pending_result,
            prev_result,
            table_exists_result,
            count_result,
        ]

        with patch("db.connection.open_database_connection", return_value=mock_conn):
            from pipeline.checks import check_ingestion
            results = check_ingestion("vendor_overview", 2)

        schema_check = [r for r in results if r.check_name == "schema_fingerprint_change"]
        assert len(schema_check) >= 1
        assert schema_check[0].passed is True
        assert "SCHEMA CHANGE" in schema_check[0].message


# ---------------------------------------------------------------------------
# Service checks
# ---------------------------------------------------------------------------

class TestServiceCheckPassesWhenRowsReturned:
    """check_service_layer() passes when mocked service returns rows."""

    def test_service_check_passes_when_rows_returned(self):
        with patch.dict("os.environ", {"ACTIVE_VENDORS": "Atlassify,Nexaflow,Cloudora"}):
            with patch(
                "services.license_service.get_raw_licenses",
                return_value=[
                    {"vendor": "Atlassify", "license_id": 1},
                    {"vendor": "Nexaflow", "license_id": 2},
                    {"vendor": "Cloudora", "license_id": 3},
                ],
            ):
                from pipeline.checks import check_service_layer
                results = check_service_layer("license_utilization", 4)

        service_checks = [r for r in results if r.check_name == "service_returns_rows"]
        assert any(r.passed for r in service_checks)


class TestServiceCheckFailsOnEmptyResults:
    """check_service_layer() fails when mocked service returns []."""

    def test_service_check_fails_on_empty_results(self):
        with patch.dict("os.environ", {"ACTIVE_VENDORS": "Atlassify,Nexaflow,Cloudora"}):
            with patch(
                "services.license_service.get_raw_licenses",
                return_value=[],
            ):
                from pipeline.checks import check_service_layer
                results = check_service_layer("license_utilization", 4)

        service_checks = [r for r in results if r.check_name == "service_returns_rows"]
        assert any(not r.passed for r in service_checks)


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

class TestRollbackMarksDataVersionsRow:
    """rollback() sets status='trial_failed' on the correct row."""

    def test_rollback_marks_data_versions_row(self):
        mock_conn = MagicMock()

        with patch("db.connection.open_database_connection", return_value=mock_conn):
            from pipeline.runner import rollback
            rollback("license_utilization", 4)

        # Check DROP TABLE was called
        calls = [str(c) for c in mock_conn.execute.call_args_list]
        assert any("DROP TABLE" in c for c in calls)

        # Check status update to trial_failed
        assert any("trial_failed" in str(c) for c in calls)
        mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Full trial run
# ---------------------------------------------------------------------------

class TestFullTrialRunPromotesOnAllPass:
    """run_trial() with all mocked checks passing → report.promoted=True."""

    def test_full_trial_run_promotes_on_all_pass(self):
        passing_checks = [
            CheckResult(layer="ingestion", check_name="row_count_deviation", passed=True, message="OK"),
        ]

        mock_conn = MagicMock()

        with patch("services.ingestion_service.ingest", return_value={
            "version_id": 4,
            "row_count": 16649,
            "schema_fingerprint": "abc",
            "promoted": False,
        }):
            with patch("pipeline.runner.check_ingestion", return_value=passing_checks):
                with patch("pipeline.runner.check_service_layer", return_value=passing_checks):
                    with patch("pipeline.runner.check_processing_layer", return_value=passing_checks):
                        with patch("pipeline.runner.check_api_layer", return_value=passing_checks):
                            with patch("db.connection.open_database_connection", return_value=mock_conn):
                                with patch("db.connection.promote_current_version"):
                                    from pipeline.runner import run_trial
                                    report = run_trial(
                                        file_path="test.csv",
                                        table_name="license_utilization",
                                    )

        assert report.all_passed is True
        assert report.promoted is True
        assert report.rolled_back is False


class TestFullTrialRunRollsBackOnFailure:
    """run_trial() with one check failing → report.rolled_back=True, promoted=False."""

    def test_full_trial_run_rolls_back_on_failure(self):
        failing_checks = [
            CheckResult(layer="ingestion", check_name="row_count_deviation", passed=False, message="EXCEEDED"),
        ]

        mock_conn = MagicMock()

        with patch("services.ingestion_service.ingest", return_value={
            "version_id": 4,
            "row_count": 16649,
            "schema_fingerprint": "abc",
            "promoted": False,
        }):
            with patch("pipeline.runner.check_ingestion", return_value=failing_checks):
                with patch("db.connection.open_database_connection", return_value=mock_conn):
                    from pipeline.runner import run_trial
                    report = run_trial(
                        file_path="test.csv",
                        table_name="license_utilization",
                    )

        assert report.all_passed is False
        assert report.promoted is False
        assert report.rolled_back is True
