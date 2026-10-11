"""Preparation contracts tested with copied sources and software-only mutations.

The preserved government files are read-only. Modified records are synthetic
test cases in temporary directories or independent in-memory copies.
"""

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

from hk_minibus.config import PROJECT_ROOT
from hk_minibus.ingest import load_sources, parse_numeric
from hk_minibus.transform import (
    aggregate_passengers,
    build_frames,
    prepare_source_passengers,
    select_scope,
)
from hk_minibus.validation import PreparationError, ValidationReport, reconcile_daily, validate_outputs


@pytest.fixture(scope="module")
def reviewed_sources():
    frames, _, _ = load_sources(
        PROJECT_ROOT / "data/raw", PROJECT_ROOT / "config/sources.json", ValidationReport()
    )
    return frames


def copied_sources(reviewed_sources):
    return {name: frame.copy(deep=True) for name, frame in reviewed_sources.items()}


@pytest.fixture
def snapshot_copy(tmp_path):
    raw = tmp_path / "synthetic_snapshot"
    shutil.copytree(PROJECT_ROOT / "data/raw", raw)
    manifest = tmp_path / "synthetic_sources.json"
    shutil.copyfile(PROJECT_ROOT / "config/sources.json", manifest)
    return raw, manifest


def rewrite_test_csv(raw, manifest, mutation):
    """Alter a test copy and update only its synthetic manifest for parsing tests."""
    path = raw / "table21_eng.csv"
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    mutation(frame).to_csv(path, index=False, lineterminator="\n")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    entry = next(item for item in payload["files"] if item["filename"] == path.name)
    entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    entry["size_bytes"] = path.stat().st_size
    manifest.write_text(json.dumps(payload), encoding="utf-8")


@pytest.mark.parametrize("failure", ["changed_raw_bytes", "wrong_revision_manifest"])
def test_snapshot_integrity_errors_are_actionable(snapshot_copy, failure):
    raw, manifest = snapshot_copy
    if failure == "changed_raw_bytes":
        path = raw / "table21_eng.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        expected_check = "hash_td_table21"
    else:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["expected_revision_date"] = "2000-01-01"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        expected_check = "source_revision_date"
    report = ValidationReport()
    with pytest.raises(PreparationError, match=expected_check):
        load_sources(raw, manifest, report)
    diagnostic = next(check for check in report.checks if check["check_id"] == expected_check)
    assert diagnostic["status"] == "fail"
    assert diagnostic["details"]


def test_numeric_parser_distinguishes_unavailable_from_invalid_text():
    report = ValidationReport()
    values = parse_numeric(pd.Series(["", "N.A.", "-", "0", "1.125"]), "PAX", report, "valid")
    assert values.iloc[:3].isna().all()
    assert values.iloc[3:].tolist() == [0.0, 1.125]
    assert not report.failed
    invalid_report = ValidationReport()
    parse_numeric(pd.Series(["nan", "NULL", "unexpected", "inf", "-inf"]), "PAX", invalid_report, "invalid")
    assert invalid_report.failed
    assert invalid_report.checks[0]["details"]["invalid_count"] == 5
    assert len(invalid_report.checks[0]["details"]["examples"]) == 5


@pytest.mark.parametrize(
    ("column", "token", "expected_check"),
    [
        ("YR_MTH", "201513", "dates_td_table21"),
        ("YR_MTH", "20151", "dates_td_table21"),
        ("PAX", "not_a_number", "numeric_td_table21_PAX"),
        ("PAX", "-1", "nonnegative_td_table21_PAX"),
        ("PAX_INDI", "unrecognized", "indicators_td_table21_PAX_INDI"),
        ("duplicate", "", "duplicates_td_table21"),
    ],
)
def test_invalid_source_records_are_rejected(snapshot_copy, column, token, expected_check):
    raw, manifest = snapshot_copy

    def mutation(frame):
        if column == "duplicate":
            return pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        frame.loc[0, column] = token
        return frame

    rewrite_test_csv(raw, manifest, mutation)
    report = ValidationReport()
    with pytest.raises(PreparationError, match=expected_check):
        load_sources(raw, manifest, report)
    assert next(check for check in report.checks if check["check_id"] == expected_check)["status"] == "fail"


@pytest.mark.parametrize("failure", ["missing_record", "unavailable_value"])
def test_missing_components_abort_aggregation_instead_of_becoming_zero(reviewed_sources, failure):
    scoped = select_scope(copied_sources(reviewed_sources), ValidationReport())
    source = prepare_source_passengers(scoped["td_table21"], daily=False)
    target = source["month"].eq("2020-02-01") & source["operator_code"].eq("RMB")
    if failure == "missing_record":
        source = source.loc[~target].copy()
    else:
        source.loc[target, "passenger_journeys_thousands"] = pd.NA
    with pytest.raises(ValueError, match="Incomplete RMB components for 2020-02-01"):
        aggregate_passengers(source, daily=False)


def test_estimate_metadata_and_status_flags_propagate_separately(reviewed_sources):
    sources = copied_sources(reviewed_sources)
    for source_id, indicator in [("td_table21", "PAX_INDI"), ("td_table21s", "AVG_DAILY_PAX_INDI")]:
        frame = sources[source_id]
        month = frame["month"].eq("2020-02-01")
        frame.loc[month & frame["TTD_PTO_CODE"].eq("GMB"), indicator] = "#"
        frame.loc[month & frame["TTD_PTO_CODE"].eq("RMB"), indicator] = "*"
    frames = build_frames(sources, ValidationReport())
    for table in ["monthly_passenger_journeys", "monthly_average_daily_journeys"]:
        facts = frames[table].set_index(["month", "mode"])
        gmb = facts.loc[("2020-02-01", "GMB")]
        rmb = facts.loc[("2020-02-01", "RMB")]
        plb = facts.loc[("2020-02-01", "PLB")]
        assert (gmb.measurement_basis, gmb.includes_estimates, gmb.is_provisional) == ("reported", 0, 1)
        assert (rmb.measurement_basis, rmb.includes_estimates, rmb.is_revised) == ("estimated", 1, 1)
        assert (plb.measurement_basis, plb.includes_estimates, plb.component_count) == ("mixed", 1, 2)
        assert (plb.source_indicator, plb.is_provisional, plb.is_revised) == ("#|*", 1, 1)
        amount = "passenger_journeys_thousands" if table == "monthly_passenger_journeys" else "average_daily_journeys_thousands"
        assert plb[amount] == pytest.approx(gmb[amount] + rmb[amount], abs=1e-9)


def test_merger_components_and_mtr_boundary_are_explicit(reviewed_sources):
    frames = build_frames(copied_sources(reviewed_sources), ValidationReport())
    source = frames["passenger_source_records"]
    for month, expected_ctb, has_nwfb, component_count in [
        ("2023-06-01", {"1", "2"}, True, 6),
        ("2023-07-01", {"2", "3"}, False, 5),
    ]:
        buses = source.loc[source["month"].eq(month) & source["source_mode"].eq("Fran_Bus")]
        assert set(buses.loc[buses["operator_code"].eq("CTB"), "franchise_type"]) == expected_ctb
        assert buses["operator_code"].eq("NWFB").any() == has_nwfb
        fact = frames["monthly_passenger_journeys"].set_index(["month", "mode"]).loc[(month, "FRANCHISED_BUS")]
        assert fact.component_count == component_count
        assert fact.passenger_journeys_thousands == float(sum(Decimal(value) for value in buses["source_numeric_text"]))
    assert not source["operator_code"].isin(["HKT", "LRB"]).any()
    links = frames["passenger_lineage"].query("mode == 'MTR'").merge(source, on="source_record_id")
    assert len(links) == 396
    assert set(links["operator_code"]) == {"MTRC"}
    assert set(links["rail_category"]) == {"Local", "Airport", "LRT"}
    assert links.groupby("month_x").size().eq(3).all()


@pytest.mark.parametrize(
    ("field", "value", "expected_check"),
    [
        ("NO_FLEET", pd.NA, "required_td_table22_NO_FLEET"),
        ("PAX_CAP", pd.NA, "required_td_table22_PAX_CAP"),
        ("NO_FLEET", 1.5, "integer_td_table22_NO_FLEET"),
        ("PAX_CAP", 0, "integer_td_table22_PAX_CAP"),
    ],
)
def test_required_fleet_counts_are_present_positive_integers(reviewed_sources, field, value, expected_check):
    sources = copied_sources(reviewed_sources)
    fleet = sources["td_table22"]
    target = fleet["month"].eq("2020-02-01") & fleet["TTD_PTO_CODE"].eq("GMB")
    fleet.loc[target, field] = value
    report = ValidationReport()
    with pytest.raises(PreparationError, match=expected_check):
        select_scope(sources, report)


def test_unsupported_fleet_mileage_stays_null(reviewed_sources):
    fleet = build_frames(copied_sources(reviewed_sources), ValidationReport())["monthly_minibus_fleet"]
    assert len(fleet) == 264
    assert fleet.loc[fleet["mode"].eq("RMB"), "vehicle_km_thousands"].isna().all()
    assert fleet["cross_harbour_vehicle_km_thousands"].isna().all()
    assert fleet.loc[fleet["mode"].eq("GMB"), "vehicle_km_thousands"].notna().all()
    assert str(fleet["licensed_vehicles"].dtype) == "Int64"
    assert str(fleet["passenger_capacity"].dtype) == "Int64"
    assert fleet["measurement_basis"].eq("reported").all()


@pytest.mark.parametrize("damage", ["incompatible_component", "lost_source_flag"])
def test_source_lineage_and_status_cannot_silently_change(reviewed_sources, damage):
    frames = build_frames(copied_sources(reviewed_sources), ValidationReport())
    source = frames["passenger_source_records"]
    month = "2020-02-01"
    if damage == "incompatible_component":
        rmb_id = source.loc[source["month"].eq(month) & source["operator_code"].eq("RMB"), "source_record_id"].iloc[0]
        lineage = frames["passenger_lineage"]
        target = lineage["month"].eq(month) & lineage["mode"].eq("GMB")
        lineage.loc[target, "source_record_id"] = rmb_id
        check_id = "monthly_passenger_journeys_lineage"
        expected_row = [month, "GMB", "incompatible_component_set"]
    else:
        target = source["month"].eq(month) & source["operator_code"].eq("GMB")
        source.loc[target, "source_indicator"] = "#"
        check_id = "monthly_passenger_journeys_status_propagation"
        expected_row = [month, "GMB"]
    report = ValidationReport()
    validate_outputs(frames, report)
    diagnostic = next(check for check in report.checks if check["check_id"] == check_id)
    assert diagnostic["status"] == "fail"
    assert expected_row in diagnostic["details"]["bad_rows"]


def test_daily_reconciliation_uses_leap_calendar_and_reports_real_mismatches(reviewed_sources):
    frames = build_frames(copied_sources(reviewed_sources), ValidationReport())
    report = ValidationReport()
    reconciled = reconcile_daily(frames, report)
    assert not report.failed
    assert len(reconciled) == 1290
    assert reconciled.loc[reconciled["month"].eq("2020-02-01"), "days_in_month"].eq(29).all()
    assert reconciled.loc[reconciled["month"].eq("2019-02-01"), "days_in_month"].eq(28).all()
    assert report.checks[1]["details"]["comparisons"] == 660
    source = frames["daily_source_records"]
    target = source["month"].eq("2020-02-01") & source["operator_code"].eq("GMB")
    source.loc[target, "average_daily_journeys_thousands"] += 1
    facts = frames["monthly_average_daily_journeys"]
    target_fact = facts["month"].eq("2020-02-01") & facts["mode"].eq("GMB")
    facts.loc[target_fact, "average_daily_journeys_thousands"] += 1
    bad_report = ValidationReport()
    reconcile_daily(frames, bad_report)
    assert [check["status"] for check in bad_report.checks] == ["fail", "fail"]
    diagnostic = bad_report.checks[0]["details"]["mismatches"]
    assert len(diagnostic) == 1
    assert (diagnostic[0]["month"], diagnostic[0]["operator_code"]) == ("2020-02-01", "GMB")
    assert diagnostic[0]["difference_thousands"] == pytest.approx(-29)
