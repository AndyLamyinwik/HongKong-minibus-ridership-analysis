"""Analytical contracts and failure cases; synthetic changes stay in tests."""

from decimal import Decimal
import json
from pathlib import Path
import re
import shutil

import numpy as np
import pandas as pd
import pytest

from hk_minibus.analysis import compute_tables, safe_ratio
from hk_minibus.analysis_pipeline import compare_frames, load_inputs, protected_input_hashes, run_analysis, validate_calculations
from hk_minibus.config import PROJECT_ROOT
from hk_minibus.validation import PreparationError, ValidationReport


@pytest.fixture(scope="module")
def inputs():
    frames, _ = load_inputs(PROJECT_ROOT, ValidationReport())
    return frames


@pytest.fixture(scope="module")
def analytical_tables(inputs):
    return compute_tables(*inputs)


def test_annual_values_equal_decimal_monthly_sums(inputs, analytical_tables):
    source = inputs[0].copy()
    source["year"] = source.month.str[:4].astype(int)
    for row in analytical_tables["annual_ridership"].itertuples():
        values = source.loc[source.year.eq(row.year) & source["mode"].eq(row.mode), "passenger_journeys_thousands"]
        expected = sum((Decimal(str(value)) for value in values), Decimal(0))
        assert len(values) == 12
        assert Decimal(str(row.passenger_journeys_thousands)) == pytest.approx(expected, abs=Decimal("0.0000001"))


def test_undefined_ratios_are_missing():
    result = safe_ratio(pd.Series([2.0, 2.0, np.nan]), pd.Series([0.0, 4.0, 4.0]))
    assert result.isna().tolist() == [True, False, True]
    assert result.iloc[1] == 50


def test_signed_change_contributions_can_offset(analytical_tables):
    values = analytical_tables["minibus_change_contributions"].query("segment == '2023_to_2025'").set_index("mode")
    assert values.loc["GMB", "contribution_to_plb_change_pct"] > 100
    assert values.loc["RMB", "contribution_to_plb_change_pct"] < 0
    assert values.absolute_change_thousands.sum() == pytest.approx(values.plb_absolute_change_thousands.iloc[0], abs=1e-7)
    assert values.contribution_to_plb_change_pct.sum() == pytest.approx(100, abs=1e-9)


def test_daily_calendar_and_vehicle_days_with_synthetic_constant_demand(inputs):
    # In-memory software fixture, never exported as analytical observations.
    monthly, daily, fleet = [frame.copy(deep=True) for frame in inputs]
    target_monthly = monthly.month.str.startswith("2020") & monthly["mode"].eq("GMB")
    target_daily = daily.month.str.startswith("2020") & daily["mode"].eq("GMB")
    target_fleet = fleet.month.str.startswith("2020") & fleet["mode"].eq("GMB")
    monthly.loc[target_monthly, "passenger_journeys_thousands"] = pd.to_datetime(monthly.loc[target_monthly, "month"]).dt.days_in_month
    daily.loc[target_daily, "average_daily_journeys_thousands"] = 1.0
    fleet.loc[target_fleet, "licensed_vehicles"] = 100
    fleet.loc[fleet.month.eq("2020-02-01") & fleet["mode"].eq("GMB"), "licensed_vehicles"] = 200
    tables = compute_tables(monthly, daily, fleet)
    context = tables["monthly_ridership"].query("year == 2020 and mode == 'GMB'")
    assert context.calendar_days.sum() == 366
    assert context.within_year_daily_index.eq(100).all()
    annual = tables["annual_fleet"].query("year == 2020 and mode == 'GMB'").iloc[0]
    assert annual.licensed_vehicle_days_proxy == 100 * 366 + 100 * 29
    assert annual.average_daily_journeys_per_licensed_vehicle == pytest.approx(366000 / 39500)
    assert annual.average_daily_journeys_per_licensed_vehicle != pytest.approx(1000 / annual.mean_month_end_licensed_vehicles)


def test_period_daily_rates_use_days_and_mean_annual_comparisons(analytical_tables):
    periods = analytical_tables["period_summary"].set_index(["period", "mode"])
    monthly = analytical_tables["monthly_ridership"]
    for (period, mode), row in periods.iterrows():
        selected = monthly.loc[monthly.period.eq(period) & monthly["mode"].eq(mode)]
        assert row.mean_annual_passenger_journeys_thousands == pytest.approx(selected.passenger_journeys_thousands.sum() / selected.year.nunique())
        expected = np.average(selected.average_daily_journeys_thousands, weights=selected.calendar_days)
        assert row.weighted_average_daily_journeys_thousands == pytest.approx(expected, abs=1e-7)


@pytest.mark.parametrize("damage", ["annual_value", "extra_plb_share", "share_value"])
def test_analytical_checks_detect_wrong_aggregation_and_denominators(analytical_tables, damage):
    tables = {name: frame.copy(deep=True) for name, frame in analytical_tables.items()}
    if damage == "annual_value":
        tables["annual_ridership"].loc[0, "passenger_journeys_thousands"] += 1
        expected = "annual_totals_twelve_months"
    elif damage == "extra_plb_share":
        extra = tables["annual_market_share"].iloc[[0]].copy()
        extra["mode"] = "PLB"
        tables["annual_market_share"] = pd.concat([tables["annual_market_share"], extra], ignore_index=True)
        expected = "annual_market_share_denominator"
    else:
        tables["monthly_market_share"].loc[0, "share_pct"] += 1
        expected = "monthly_market_share_100_percent"
    report = ValidationReport()
    with pytest.raises(PreparationError, match=expected):
        validate_calculations(tables, report)
    assert next(check for check in report.checks if check["check_id"] == expected)["status"] == "fail"


def test_comparison_rejects_missingness_metadata_and_numeric_disagreement():
    expected = pd.DataFrame({"value_thousands": [1.0, np.nan], "share_pct": [50.0, np.nan], "mode": ["GMB", "RMB"]})
    assert compare_frames(expected, expected.copy())["equal"]
    for column, value in [("value_thousands", 2.0), ("share_pct", 50.00001), ("mode", "PLB")]:
        wrong = expected.copy()
        wrong.loc[0, column] = value
        assert not compare_frames(expected, wrong)["equal"]
    wrong = expected.copy()
    wrong.loc[1, "value_thousands"] = 0
    assert "value_thousands:nullness" in compare_frames(expected, wrong)["problems"]


def test_changed_processed_copy_is_rejected_without_touching_real_sources(tmp_path):
    before = protected_input_hashes(PROJECT_ROOT)
    for name in ["data/raw", "data/processed", "config"]:
        shutil.copytree(PROJECT_ROOT / name, tmp_path / name)
    path = tmp_path / "data/processed/monthly_passenger_journeys.csv"
    frame = pd.read_csv(path, keep_default_na=False, float_precision="round_trip")
    frame.loc[0, "passenger_journeys_thousands"] += 1
    frame.to_csv(path, index=False)
    with pytest.raises(PreparationError, match="input_csv_sql_monthly_passenger_journeys"):
        load_inputs(tmp_path, ValidationReport())
    assert protected_input_hashes(PROJECT_ROOT) == before


@pytest.fixture(scope="module")
def completed_analysis(tmp_path_factory):
    directory = tmp_path_factory.mktemp("phase3_real_snapshot")
    analysis_dir, report_path = directory / "analysis", directory / "reports/eda_findings.md"
    before = protected_input_hashes(PROJECT_ROOT)
    summary = run_analysis(analysis_dir=analysis_dir, report_path=report_path)
    assert protected_input_hashes(PROJECT_ROOT) == before
    return analysis_dir, report_path, summary


def test_full_analysis_exports_and_report_links(completed_analysis):
    analysis_dir, report_path, summary = completed_analysis
    assert summary["check_counts"]["fail"] == 0
    assert summary["record_counts"]["annual_ridership"] == 55
    assert summary["record_counts"]["monthly_market_share"] == 528
    assert len(summary["figures"]) == 7
    assert json.loads((analysis_dir / "outputs/analysis_summary.json").read_text(encoding="utf-8")) == summary
    text = report_path.read_text(encoding="utf-8")
    for match in re.finditer(r"\]\((?:<([^>]+)>|([^)]*))\)", text):
        target = match.group(1) or match.group(2)
        if not target.startswith(("https://", "http://")):
            assert (report_path.parent / target).exists(), target
    assert not list(analysis_dir.glob(".analysis-build-*"))


def test_analysis_is_reproducible_without_replacing_prepared_inputs(completed_analysis):
    analysis_dir, report_path, _ = completed_analysis
    artifacts = [*sorted((analysis_dir / "outputs").rglob("*.csv")), analysis_dir / "outputs/analysis_summary.json", report_path]
    before = {path: path.read_bytes() for path in artifacts}
    summary = run_analysis(analysis_dir=analysis_dir, report_path=report_path)
    assert summary["check_counts"]["fail"] == 0
    assert {path: path.read_bytes() for path in artifacts} == before


@pytest.mark.parametrize("protected", ["data/raw", "data/processed", "src", "sql", "config", "tests"])
def test_analysis_output_cannot_replace_existing_project_layers(protected):
    with pytest.raises(ValueError, match="separate"):
        run_analysis(analysis_dir=PROJECT_ROOT / protected)
