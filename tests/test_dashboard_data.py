"""Dashboard inputs must remain a complete, consistent historical snapshot."""

import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest

from hk_minibus.dashboard.data import (
    DataLoadError,
    TABLE_NAMES,
    load_dashboard_data,
    source_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def copied_inputs(tmp_path):
    (tmp_path / "analysis" / "outputs").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    for name in TABLE_NAMES:
        shutil.copyfile(ROOT / "analysis" / "outputs" / f"{name}.csv",
                        tmp_path / "analysis" / "outputs" / f"{name}.csv")
    shutil.copyfile(ROOT / "analysis" / "outputs" / "analysis_summary.json",
                    tmp_path / "analysis" / "outputs" / "analysis_summary.json")
    shutil.copyfile(ROOT / "config" / "sources.json", tmp_path / "config" / "sources.json")
    return tmp_path


def rewrite(root, name, mutation):
    path = root / "analysis" / "outputs" / f"{name}.csv"
    frame = pd.read_csv(path)
    mutation(frame).to_csv(path, index=False)


def test_actual_outputs_load_with_preserved_qualifications_and_provenance():
    data = load_dashboard_data(ROOT)
    assert set(data.tables) == set(TABLE_NAMES)
    assert len(data.table("monthly_ridership")) == 660
    assert data.metadata["scope"]["months"] == 132
    assert data.metadata["snapshot_retrieved_on"] == "2026-10-11"
    assert data.metadata["expected_revision_date"] == "2026-09-21"
    assert "Transport Department" in data.metadata["publisher"]
    monthly = data.table("monthly_ridership")
    assert pd.api.types.is_datetime64_any_dtype(monthly["month"])
    assert monthly.loc[monthly["mode"].eq("RMB"), "measurement_basis"].eq("estimated").all()
    assert monthly.loc[monthly["mode"].eq("PLB"), "includes_estimates"].eq(1).all()


def test_table_access_returns_independent_copies():
    data = load_dashboard_data(ROOT)
    frame = data.table("endpoint_comparison")
    original = data.table("endpoint_comparison")["change_2015_2025_pct"].copy()
    frame["change_2015_2025_pct"] = 0
    pd.testing.assert_series_equal(data.table("endpoint_comparison")["change_2015_2025_pct"], original)


def test_missing_file_has_actionable_error(copied_inputs):
    (copied_inputs / "analysis" / "outputs" / "annual_ridership.csv").unlink()
    with pytest.raises(DataLoadError, match="annual_ridership.csv"):
        load_dashboard_data(copied_inputs)


def test_fingerprint_changes_for_a_changed_input(copied_inputs):
    before = source_fingerprint(copied_inputs)
    path = copied_inputs / "analysis" / "outputs" / "annual_ridership.csv"
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    assert source_fingerprint(copied_inputs) != before


@pytest.mark.parametrize("mutation, message", [
    (lambda f: f.iloc[1:], "complete 2015"),
    (lambda f: pd.concat([f, f.iloc[[0]]]), "duplicate"),
    (lambda f: f.drop(columns="passenger_journeys_thousands"), "required columns"),
    (lambda f: f.assign(passenger_journeys_thousands=np.nan), "missing or nonfinite"),
    (lambda f: f.assign(passenger_journeys_thousands=np.inf), "missing or nonfinite"),
    (lambda f: f.assign(passenger_journeys_thousands="invalid"), "invalid numbers"),
    (lambda f: f.assign(month="2015-01-02"), "duplicate|complete"),
    (lambda f: f.assign(month="invalid"), "invalid reference months"),
    (lambda f: f.assign(includes_estimates=0), "estimation qualifications"),
    (lambda f: f.assign(measurement_basis="reported"), "estimation qualifications"),
    (lambda f: f.assign(is_provisional=2), "status flags"),
    (lambda f: f.assign(unit="million_journeys"), "thousand_journeys units"),
])
def test_malformed_monthly_inputs_are_rejected(copied_inputs, mutation, message):
    rewrite(copied_inputs, "monthly_ridership", mutation)
    with pytest.raises(DataLoadError, match=message):
        load_dashboard_data(copied_inputs)


@pytest.mark.parametrize("table, column, message", [
    ("annual_ridership", "passenger_journeys_thousands", "annual/monthly totals"),
    ("endpoint_comparison", "change_2015_2025_pct", "endpoint percentage change"),
    ("recovery_2019", "recovery_pct", "recovery ratio"),
    ("annual_recovery", "recovery_pct", "annual recovery ratio"),
    ("annual_market_share", "share_pct", "annual_market_share ratio"),
    ("monthly_market_share", "comparison_group_journeys_thousands", "monthly_market_share denominator"),
    ("annual_minibus_composition", "share_of_plb_pct", "annual_minibus_composition ratio"),
    ("minibus_composition", "plb_journeys_thousands", "minibus_composition denominator"),
    ("annual_fleet", "licensed_vehicle_days_proxy", "licensed vehicle-day denominator"),
    ("annual_fleet", "average_daily_journeys_per_licensed_vehicle", "annual fleet indicator"),
    ("fleet_normalized", "average_daily_journeys_per_licensed_vehicle", "monthly fleet indicator"),
    ("trend_segments", "change_pct", "segment percentage change"),
    ("trend_segments", "annual_decreases", "transition counts"),
])
def test_numerical_disagreement_cannot_silently_reach_the_ui(copied_inputs, table, column, message):
    rewrite(copied_inputs, table, lambda frame: frame.assign(**{column: frame[column] + 1}))
    with pytest.raises(DataLoadError, match=message):
        load_dashboard_data(copied_inputs)


def test_market_share_rejects_overlapping_plb_component(copied_inputs):
    rewrite(copied_inputs, "annual_market_share", lambda f: f.assign(mode=f["mode"].replace({"GMB": "PLB"})))
    with pytest.raises(DataLoadError, match="complete 2015"):
        load_dashboard_data(copied_inputs)


def test_failed_analysis_summary_is_rejected(copied_inputs):
    path = copied_inputs / "analysis" / "outputs" / "analysis_summary.json"
    summary = json.loads(path.read_text())
    summary["check_counts"]["fail"] = 1
    path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(DataLoadError, match="successful validated"):
        load_dashboard_data(copied_inputs)


def test_wrong_summary_scope_is_rejected(copied_inputs):
    path = copied_inputs / "analysis" / "outputs" / "analysis_summary.json"
    summary = json.loads(path.read_text())
    summary["scope"]["months"] = 131
    path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(DataLoadError, match="132 months"):
        load_dashboard_data(copied_inputs)


@pytest.mark.parametrize("content", ["invalid JSON", "[]", '{"check_counts": null}'])
def test_malformed_metadata_has_controlled_error(copied_inputs, content):
    path = copied_inputs / "analysis" / "outputs" / "analysis_summary.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataLoadError):
        load_dashboard_data(copied_inputs)


def test_annual_yoy_preserves_undefined_first_year(copied_inputs):
    rewrite(copied_inputs, "annual_ridership", lambda f: f.assign(yoy_change_pct=f["yoy_change_pct"].fillna(0)))
    with pytest.raises(DataLoadError, match="first in-window year"):
        load_dashboard_data(copied_inputs)
