"""Reproduce the reviewed snapshot and exercise failure-safe publication.

All outputs and intentionally damaged snapshot copies remain in pytest's
temporary directories. These tests never replace the project's raw files.
"""

from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

import pandas as pd
import pytest

from hk_minibus.config import PROJECT_ROOT
from hk_minibus import pipeline


RAW = PROJECT_ROOT / "data/raw"
MANIFEST = PROJECT_ROOT / "config/sources.json"
REFERENCES = PROJECT_ROOT / "config/reference_values.csv"
DATA_ARTIFACTS = [
    "monthly_passenger_journeys.csv",
    "monthly_average_daily_journeys.csv",
    "monthly_minibus_fleet.csv",
    "transport.sqlite",
    "source_inspection.json",
]


def raw_hashes(directory=RAW):
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.iterdir() if path.is_file()}


@pytest.fixture(scope="module")
def successful_run(tmp_path_factory):
    directory = tmp_path_factory.mktemp("reviewed_snapshot_run")
    output = directory / "processed"
    report = directory / "validation.md"
    before = raw_hashes()
    summary = pipeline.run_pipeline(RAW, output, MANIFEST, REFERENCES, report)
    assert raw_hashes() == before
    assert summary["outputs_published"], summary["error"]
    assert summary["check_counts"]["fail"] == 0
    return output, report, summary


def copy_successful_outputs(successful_run, tmp_path):
    source, source_report, _ = successful_run
    output = tmp_path / "processed"
    shutil.copytree(source, output)
    report = tmp_path / "validation.md"
    shutil.copyfile(source_report, report)
    return output, report


def test_full_run_has_complete_facts_provenance_and_database_constraints(successful_run, tmp_path):
    output, report, summary = successful_run
    expected = {
        "monthly_passenger_journeys": 660,
        "monthly_average_daily_journeys": 660,
        "monthly_minibus_fleet": 264,
        "passenger_source_records": 1422,
        "daily_source_records": 1290,
        "passenger_lineage": 1686,
        "daily_lineage": 1554,
    }
    assert summary["record_counts"] == expected
    assert summary["status"] == "passed_with_warnings"
    assert len(summary["source_files"]) == 5
    assert len({item["sha256"] for item in summary["source_files"]}) == 5
    for table, count in [("monthly_passenger_journeys", 660), ("monthly_average_daily_journeys", 660), ("monthly_minibus_fleet", 264)]:
        frame = pd.read_csv(output / f"{table}.csv", keep_default_na=False)
        assert len(frame) == count
        assert frame.month.nunique() == 132
        assert (frame.month.min(), frame.month.max()) == ("2015-01-01", "2025-12-01")
        assert not frame.duplicated(["month", "mode"]).any()
    assert json.loads((output / "validation_summary.json").read_text(encoding="utf-8")) == summary
    assert "passed_with_warnings" in report.read_text(encoding="utf-8")
    database = tmp_path / "constraint_test.sqlite"
    shutil.copyfile(output / "transport.sqlite", database)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        for table, count in expected.items():
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == count
        assert connection.execute("SELECT COUNT(*) FROM source_files").fetchone()[0] == 5
        assert connection.execute("SELECT COUNT(*) FROM v_monthly_comparison_group").fetchone()[0] == 396
        assert connection.execute("SELECT COUNT(*) FROM v_passenger_source_lineage").fetchone()[0] == 1686
        assert connection.execute("SELECT COUNT(*) FROM monthly_minibus_fleet WHERE mode='RMB' AND vehicle_km_thousands IS NULL").fetchone()[0] == 132
        assert connection.execute("SELECT DISTINCT calendar_days FROM v_daily_reconciliation_inputs WHERE month='2020-02-01'").fetchall() == [(29,)]
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO monthly_passenger_journeys SELECT * FROM monthly_passenger_journeys WHERE month='2020-02-01' AND mode='GMB'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE monthly_minibus_fleet SET licensed_vehicles=1.5 WHERE month='2020-02-01' AND mode='GMB'")


def test_repeated_run_produces_identical_csv_and_json(successful_run, tmp_path):
    output, report = copy_successful_outputs(successful_run, tmp_path)
    paths = list(output.glob("*.csv")) + list(output.glob("*.json"))
    before = {path.name: path.read_bytes() for path in paths}
    raw_before = raw_hashes()
    summary = pipeline.run_pipeline(RAW, output, MANIFEST, REFERENCES, report)
    assert summary["outputs_published"]
    assert summary["check_counts"]["fail"] == 0
    assert {path.name: path.read_bytes() for path in paths} == before
    assert raw_hashes() == raw_before


@pytest.mark.parametrize("damage", ["header_only", "duplicate_key", "invalid_number", "wrong_url"])
def test_invalid_annual_reference_contract_is_rejected(successful_run, tmp_path, damage):
    output, _, _ = successful_run
    passengers = pd.read_csv(output / "monthly_passenger_journeys.csv", keep_default_na=False)
    references = pd.read_csv(REFERENCES, dtype=str, keep_default_na=False)
    if damage == "header_only":
        references = references.iloc[:0]
    elif damage == "duplicate_key":
        references = pd.concat([references.iloc[:-1], references.iloc[[0]]], ignore_index=True)
    elif damage == "invalid_number":
        references.loc[0, "passenger_journeys_thousands"] = "inf"
    else:
        references.loc[0, "source_url"] = "https://example.invalid/test-fixture"
    synthetic_reference = tmp_path / "synthetic_reference.csv"
    references.to_csv(synthetic_reference, index=False)
    report = pipeline.ValidationReport()
    with pytest.raises(pipeline.PreparationError, match="annual_reference_contract"):
        pipeline.check_annual_references(passengers, synthetic_reference, report)
    assert report.checks[0]["status"] == "fail"
    assert report.checks[0]["check_id"] == "annual_reference_contract"


def test_failed_source_check_keeps_last_successful_datasets_and_writes_diagnostics(successful_run, tmp_path):
    output, report = copy_successful_outputs(successful_run, tmp_path)
    preserved = {name: (output / name).read_bytes() for name in DATA_ARTIFACTS}
    raw = tmp_path / "synthetic_bad_snapshot"
    shutil.copytree(RAW, raw)
    damaged = raw / "table21_eng.csv"
    damaged.write_bytes(damaged.read_bytes() + b"\n")
    copied_raw_before = raw_hashes(raw)
    real_raw_before = raw_hashes()
    summary = pipeline.run_pipeline(raw, output, MANIFEST, REFERENCES, report)
    assert summary["status"] == "failed"
    assert summary["outputs_published"] is False
    assert "hash_td_table21" in summary["error"]
    assert next(check for check in summary["checks"] if check["check_id"] == "hash_td_table21")["status"] == "fail"
    assert {name: (output / name).read_bytes() for name in DATA_ARTIFACTS} == preserved
    assert json.loads((output / "validation_summary.json").read_text(encoding="utf-8")) == summary
    assert "Outputs published by this run:** no" in report.read_text(encoding="utf-8")
    assert raw_hashes(raw) == copied_raw_before
    assert raw_hashes() == real_raw_before


@pytest.mark.parametrize(
    "conflict",
    ["output_equals_raw", "output_inside_raw", "output_contains_raw", "report_inside_raw", "report_is_database", "report_is_manifest"],
)
def test_output_path_conflicts_are_rejected_before_any_file_changes(tmp_path, conflict):
    raw = tmp_path / "inputs/raw"
    shutil.copytree(RAW, raw)
    # A JSON manifest may have any filename. The .md case checks the explicit
    # input-path guard rather than relying only on a Markdown suffix check.
    manifest = tmp_path / ("synthetic_sources.md" if conflict == "report_is_manifest" else "synthetic_sources.json")
    shutil.copyfile(MANIFEST, manifest)
    output = tmp_path / "processed"
    report = tmp_path / "validation.md"
    if conflict == "output_equals_raw":
        output = raw
    elif conflict == "output_inside_raw":
        output = raw / "processed"
    elif conflict == "output_contains_raw":
        output = raw.parent
    elif conflict == "report_inside_raw":
        report = raw / "validation.md"
    elif conflict == "report_is_database":
        report = output / "transport.sqlite"
    elif conflict == "report_is_manifest":
        report = manifest
    before = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(ValueError):
        pipeline.run_pipeline(raw, output, manifest, REFERENCES, report)
    after = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before


def test_publication_failure_rolls_back_existing_csv_and_database(successful_run, tmp_path, monkeypatch):
    output, report = copy_successful_outputs(successful_run, tmp_path)
    preserved = {name: (output / name).read_bytes() for name in DATA_ARTIFACTS}
    replace = pipeline.os.replace
    injected_failure = False

    def simulate_locked_database(source, destination):
        nonlocal injected_failure
        destination = Path(destination)
        if destination == output / "transport.sqlite" and not injected_failure:
            injected_failure = True
            raise PermissionError("Synthetic test: database destination is locked")
        return replace(source, destination)

    monkeypatch.setattr(pipeline.os, "replace", simulate_locked_database)
    summary = pipeline.run_pipeline(RAW, output, MANIFEST, REFERENCES, report)
    assert injected_failure
    assert summary["status"] == "failed"
    assert summary["outputs_published"] is False
    assert "locked" in summary["error"]
    assert {name: (output / name).read_bytes() for name in DATA_ARTIFACTS} == preserved
    assert json.loads((output / "validation_summary.json").read_text(encoding="utf-8")) == summary
    assert "Outputs published by this run:** no" in report.read_text(encoding="utf-8")
