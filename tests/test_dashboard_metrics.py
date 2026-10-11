"""Check display units, fixed baselines and study headline consistency."""

from pathlib import Path

import pandas as pd
import pytest

from hk_minibus.dashboard.data import load_dashboard_data
from hk_minibus.dashboard.metrics import (
    fleet_endpoints, headline_metrics, period_change, ridership_endpoints,
    select_rows, share_endpoints, trend_data,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data():
    return load_dashboard_data(ROOT)


def test_headlines_match_published_phase3_findings(data):
    headlines = headline_metrics(data)
    assert headlines["plb_change"] == pytest.approx(-19.5075142058)
    assert headlines["gmb_change"] == pytest.approx(-11.1743300682)
    assert headlines["rmb_change"] == pytest.approx(-58.0037335445)
    assert headlines["rmb_recovery"] == pytest.approx(49.1837562180)
    assert headlines["gmb_share_2025"] == pytest.approx(90.7157314137)
    assert headlines["gmb_share_change_pp"] == pytest.approx(8.5105003388)
    assert headlines["plb_selected_share_2025"] == pytest.approx(14.3240285025)
    assert headlines["plb_selected_share_change_pp"] == pytest.approx(-2.6688929586)


@pytest.mark.parametrize("table, expected_rows", [("monthly_ridership", 36), ("annual_ridership", 3)])
def test_date_and_mode_selection_is_inclusive(data, table, expected_rows):
    result = select_rows(data.table(table), ("RMB",), (2023, 2025))
    assert len(result) == expected_rows
    assert set(result["mode"]) == {"RMB"}
    assert set(result["year"]) == {2023, 2024, 2025}


def test_selection_supports_month_only_tables(data):
    frame = data.table("fleet_normalized")
    selected = select_rows(frame, ("GMB",), (2019, 2019))
    assert len(selected) == 12
    assert selected["month"].dt.year.eq(2019).all()


@pytest.mark.parametrize("frequency, rows", [("Monthly", 12), ("Annual", 1)])
def test_absolute_views_convert_thousand_journeys_to_millions(data, frequency, rows):
    displayed = trend_data(data, frequency=frequency, modes=("GMB",), year_range=(2025, 2025))
    assert len(displayed) == rows
    pd.testing.assert_series_equal(displayed["value"], displayed["passenger_journeys_thousands"] / 1000, check_names=False)
    if frequency == "Annual":
        assert displayed.iloc[0]["value"] == pytest.approx(495.802414)
    else:
        assert displayed.iloc[-1]["value"] == pytest.approx(42.416688)


@pytest.mark.parametrize("frequency, expected_rows", [("Monthly", 60), ("Annual", 5)])
def test_2015_index_points_are_100(data, frequency, expected_rows):
    displayed = trend_data(data, frequency=frequency, indexed=True, modes=("GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"), year_range=(2015, 2015))
    assert len(displayed) == expected_rows
    assert displayed["value"].tolist() == pytest.approx([100] * expected_rows, abs=1e-10)


@pytest.mark.parametrize("frequency", ["Monthly", "Annual"])
def test_filtered_index_never_resets_its_2015_baseline(data, frequency):
    full = trend_data(data, frequency=frequency, indexed=True, modes=("RMB",))
    filtered = trend_data(data, frequency=frequency, indexed=True, modes=("RMB",), year_range=(2023, 2025))
    full_selected = select_rows(full, ("RMB",), (2023, 2025)).reset_index(drop=True)
    pd.testing.assert_frame_equal(filtered, full_selected)
    assert not filtered.iloc[0]["value"] == pytest.approx(100)


def test_monthly_index_uses_daily_rates_and_same_calendar_month(data):
    displayed = trend_data(data, frequency="Monthly", indexed=True, modes=("GMB",), year_range=(2016, 2016))
    february = displayed[displayed["month"].dt.month.eq(2)].iloc[0]
    baseline = data.table("monthly_ridership")
    baseline = baseline[baseline["mode"].eq("GMB") & baseline["month"].eq(pd.Timestamp("2015-02-01"))].iloc[0]
    expected = 100 * february["average_daily_journeys_thousands"] / baseline["average_daily_journeys_thousands"]
    incorrect_total_index = 100 * february["passenger_journeys_thousands"] / baseline["passenger_journeys_thousands"]
    assert february["value"] == pytest.approx(expected)
    assert february["value"] != pytest.approx(incorrect_total_index)
    assert february["calendar_days"] == 29


def test_empty_mode_and_outside_window_selections_are_safe(data):
    assert trend_data(data, modes=()).empty
    assert trend_data(data, modes=("GMB",), year_range=(2030, 2031)).empty
    assert select_rows(data.table("annual_fleet"), (), (2015, 2025)).empty


def test_display_filters_do_not_mutate_cached_tables(data):
    original = data.table("monthly_ridership")
    trend_data(data, frequency="Monthly", indexed=True, modes=("GMB",), year_range=(2025, 2025))
    pd.testing.assert_frame_equal(data.table("monthly_ridership"), original)


def test_invalid_controls_have_clear_errors(data):
    with pytest.raises(ValueError, match="Frequency"):
        trend_data(data, frequency="Weekly")
    with pytest.raises(ValueError, match="start year"):
        trend_data(data, year_range=(2025, 2015))


def test_fleet_endpoint_change_uses_existing_annual_stock_values(data):
    result = period_change(data.table("annual_fleet"), "december_licensed_vehicles", 2015, 2025).set_index("mode")
    assert result.loc["GMB", "start_value"] == 3203
    assert result.loc["GMB", "end_value"] == 3360
    assert result.loc["RMB", "start_value"] == 1141
    assert result.loc["RMB", "end_value"] == 693
    assert result.loc["RMB", "change_pct"] == pytest.approx(-39.2638036810)


def test_missing_period_endpoints_do_not_create_values(data):
    result = period_change(data.table("annual_fleet"), "december_licensed_vehicles", 2014, 2025)
    assert result.empty


def test_recovery_does_not_cap_values_at_100(data):
    recovery = data.table("recovery_2019").set_index("mode")
    assert recovery.loc["MTR", "recovery_pct"] == pytest.approx(101.9867370273)
    assert recovery.loc["MTR", "recovery_pct"] > 100


def test_ridership_endpoint_table_matches_findings_and_requested_order(data):
    table = ridership_endpoints(data, ("RMB", "GMB"), (2015, 2025))
    assert table["Transport mode"].tolist() == ["Red Minibuses (estimated)", "Green Minibuses"]
    assert table.iloc[0]["2015 annual journeys (million)"] == pytest.approx(120.826736)
    assert table.iloc[0]["2025 annual journeys (million)"] == pytest.approx(50.742718)
    assert table.iloc[0]["Annual endpoint change (%)"] == pytest.approx(-58.0037335445)
    assert table.iloc[1]["Annual endpoint change (%)"] == pytest.approx(-11.1743300682)


def test_ridership_selected_recent_endpoint_matches_existing_segment(data):
    table = ridership_endpoints(data, ("GMB", "RMB"), (2023, 2025))
    segments = data.table("trend_segments").loc[lambda f: f["segment"].eq("2023_to_2025")].set_index("mode")
    assert table["Annual endpoint change (%)"].tolist() == pytest.approx([
        segments.loc["GMB", "change_pct"], segments.loc["RMB", "change_pct"],
    ])


def test_fleet_endpoint_table_matches_december_stocks_and_annual_proxy(data):
    table = fleet_endpoints(data, ("GMB", "RMB"), (2015, 2025))
    assert table.iloc[0]["Dec 2015 vehicles"] == 3203
    assert table.iloc[0]["Dec 2025 vehicles"] == 3360
    assert table.iloc[1]["Dec 2015 vehicles"] == 1141
    assert table.iloc[1]["Dec 2025 vehicles"] == 693
    assert table.iloc[1]["December stock change (%)"] == pytest.approx(-39.2638036810)
    annual = data.table("annual_fleet").set_index(["year", "mode"])
    for index, mode in enumerate(("GMB", "RMB")):
        expected = 100 * (annual.loc[(2025, mode), "average_daily_journeys_per_licensed_vehicle"] /
                          annual.loc[(2015, mode), "average_daily_journeys_per_licensed_vehicle"] - 1)
        assert table.iloc[index]["Annual proxy change (%)"] == pytest.approx(expected)


def test_share_endpoints_match_approved_denominator_and_percentage_points(data):
    result = share_endpoints(data, (2015, 2025))
    assert result["plb_start"] == pytest.approx(16.9929214611)
    assert result["plb_end"] == pytest.approx(14.3240285025)
    assert result["plb_change_pp"] == pytest.approx(-2.6688929586)
    assert result["gmb_start"] == pytest.approx(82.2052310750)
    assert result["gmb_end"] == pytest.approx(90.7157314137)
    assert result["gmb_change_pp"] == pytest.approx(8.5105003388)


def test_selected_recent_share_endpoint_reads_annual_ratios(data):
    result = share_endpoints(data, (2023, 2025))
    annual = data.table("annual_market_share")
    expected = annual.loc[annual["year"].eq(2023) & annual["mode"].isin(("GMB", "RMB")), "share_pct"].sum()
    assert result["plb_start"] == pytest.approx(expected)


def test_single_year_endpoint_helpers_return_zero_changes(data):
    ridership = ridership_endpoints(data, ("GMB", "RMB"), (2023, 2023))
    fleet = fleet_endpoints(data, ("GMB", "RMB"), (2023, 2023))
    shares = share_endpoints(data, (2023, 2023))
    assert ridership["Annual endpoint change (%)"].eq(0).all()
    assert fleet["December stock change (%)"].eq(0).all()
    assert fleet["Annual proxy change (%)"].eq(0).all()
    assert shares["plb_change_pp"] == 0
    assert shares["gmb_change_pp"] == 0
    assert ridership.columns.is_unique and fleet.columns.is_unique


def test_empty_endpoint_mode_selections_preserve_table_schema(data):
    assert ridership_endpoints(data, (), (2015, 2025)).empty
    assert "Annual endpoint change (%)" in ridership_endpoints(data, (), (2015, 2025)).columns
    assert fleet_endpoints(data, (), (2015, 2025)).empty


def test_unavailable_share_endpoint_cannot_be_reported_as_zero(data):
    with pytest.raises(ValueError, match="validated study window"):
        share_endpoints(data, (2014, 2025))
