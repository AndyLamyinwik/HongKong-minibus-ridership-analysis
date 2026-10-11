"""Meaningful chart contracts: units, estimation labels and denominator boundaries."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hk_minibus.dashboard.charts import (
    MODE_NAMES, baseline_comparison_chart, composition_chart, fleet_chart,
    recovery_bar, recovery_trend_chart, series_chart, share_chart, trend_chart,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return pd.read_csv(PROJECT_ROOT / "analysis" / "outputs" / f"{name}.csv")


def trace(figure, mode):
    return next(item for item in figure.data if item.name == MODE_NAMES[mode])


def test_annual_trend_preserves_values_units_and_estimated_labels():
    frame = source("annual_ridership")
    frame["value"] = frame.passenger_journeys_thousands / 1000
    frame = frame.loc[frame["mode"].isin(["GMB", "RMB", "PLB"])]
    original = frame.copy(deep=True)
    figure = trend_chart(frame)
    assert len(figure.data) == 3
    for mode in ("GMB", "RMB", "PLB"):
        expected = frame.loc[frame["mode"].eq(mode)].sort_values("year").value.tolist()
        assert list(trace(figure, mode).y) == expected
    assert "Million journeys / year" == figure.layout.yaxis.title.text
    assert figure.layout.yaxis.rangemode == "tozero"
    assert "estimated" in trace(figure, "RMB").hovertemplate
    assert "includes estimates" in trace(figure, "PLB").name
    assert trace(figure, "GMB").line.dash != trace(figure, "RMB").line.dash
    pd.testing.assert_frame_equal(frame, original)


def test_indexed_chart_preserves_fixed_baseline_after_year_filter():
    frame = source("annual_ridership")
    baseline = frame.loc[frame.year.eq(2015)].set_index("mode").passenger_journeys_thousands
    frame["value"] = frame.passenger_journeys_thousands / frame["mode"].map(baseline) * 100
    filtered = frame.loc[frame.year.between(2023, 2025) & frame["mode"].eq("RMB")]
    figure = trend_chart(filtered, indexed=True)
    assert list(figure.data[0].y) == filtered.value.tolist()
    assert figure.data[0].y[0] != 100
    assert figure.data[0].y[-1] == pytest.approx(41.99626645546184)
    assert "2015 = 100" in figure.layout.yaxis.title.text
    assert any(shape.y0 == 100 and shape.y1 == 100 for shape in figure.layout.shapes)


def test_monthly_index_labels_same_calendar_month_baseline():
    frame = source("monthly_ridership")
    frame = frame.loc[frame["mode"].eq("RMB")]
    baseline = frame.loc[frame.year.eq(2015)].set_index("calendar_month").average_daily_journeys_thousands
    frame = frame.copy()
    frame["value"] = frame.average_daily_journeys_thousands / frame.calendar_month.map(baseline) * 100
    figure = trend_chart(frame, frequency="Monthly", indexed=True)
    assert "Daily-rate index" in figure.layout.yaxis.title.text
    assert "same month in 2015" in figure.layout.yaxis.title.text
    assert list(figure.data[0].y[:12]) == pytest.approx([100] * 12)
    assert figure.layout.xaxis.hoverformat == "%b %Y"


def test_recovery_baseline_and_mtr_above_100_are_visible():
    frame = source("recovery_2019")
    figure = recovery_bar(frame)
    bars = figure.data[0]
    position = list(bars.y).index(MODE_NAMES["MTR"])
    assert bars.x[position] == pytest.approx(101.986736364914)
    assert figure.layout.xaxis.range[1] > bars.x[position]
    assert figure.layout.xaxis.range[0] == 0
    assert any(shape.x0 == 100 and shape.x1 == 100 for shape in figure.layout.shapes)
    assert "RMB (estimated)" in bars.y


def test_paired_baseline_totals_convert_thousands_to_millions():
    frame = source("recovery_2019")
    original = frame.copy(deep=True)
    figure = baseline_comparison_chart(frame)
    assert [item.name for item in figure.data] == ["2019", "2025"]
    mtr = list(figure.data[1].y).index(MODE_NAMES["MTR"])
    assert figure.data[1].x[mtr] == pytest.approx(1899.839725)
    assert "Million journeys / year" == figure.layout.xaxis.title.text
    assert figure.layout.xaxis.rangemode == "tozero"
    pd.testing.assert_frame_equal(frame, original)


def test_annual_recovery_uses_preserved_baselines_for_each_mode():
    frame = source("annual_recovery")
    figure = recovery_trend_chart(frame)
    for mode in ("GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"):
        item = trace(figure, mode)
        position = list(item.x).index(2019)
        assert item.y[position] == pytest.approx(100)
        expected = frame.loc[frame["mode"].eq(mode)].sort_values("year").recovery_pct.tolist()
        assert list(item.y) == expected


def test_share_subset_preserves_original_denominator_and_no_renormalization():
    frame = source("annual_market_share")
    selected = frame.loc[frame["mode"].isin(["GMB", "RMB"])]
    original = selected.copy(deep=True)
    figure = share_chart(selected)
    assert len(figure.data) == 2
    assert "Share within selected public transport modes" == figure.layout.title.text.replace("<br>", " ")
    assert sum(item.y[-1] for item in figure.data) == pytest.approx(14.324027685876346, abs=0.00001)
    assert all(item.groupnorm is None for item in figure.data)
    assert figure.layout.yaxis.range == (0, 100)
    pd.testing.assert_frame_equal(selected, original)


def test_complete_share_stack_sums_to_100_and_line_view_keeps_values():
    frame = source("annual_market_share")
    stacked = share_chart(frame)
    lines = share_chart(frame, style="Lines")
    assert len(stacked.data) == 4
    totals = np.array([item.y for item in stacked.data]).sum(axis=0)
    assert totals == pytest.approx([100] * 11, abs=1e-8)
    for left, right in zip(stacked.data, lines.data):
        assert left.name == right.name
        assert left.y == right.y
        assert right.stackgroup is None


def test_share_chart_rejects_double_counted_plb_and_unknown_styles():
    frame = source("annual_market_share")
    extra = frame.iloc[[0]].copy()
    extra["mode"] = "PLB"
    with pytest.raises(ValueError, match="PLB"):
        share_chart(pd.concat([frame, extra]))
    with pytest.raises(ValueError, match="Area or Lines"):
        share_chart(frame, style="Pie")


@pytest.mark.parametrize("frequency,name", [("Annual", "annual_minibus_composition"), ("Monthly", "minibus_composition")])
def test_composition_keeps_gmb_rmb_shares_and_estimation_label(frequency, name):
    frame = source(name)
    figure = composition_chart(frame, frequency)
    assert len(figure.data) == 2
    assert np.array([item.y for item in figure.data]).sum(axis=0) == pytest.approx([100] * len(figure.data[0].x))
    assert trace(figure, "RMB").name == "RMB (estimated)"
    assert all(item.groupnorm is None for item in figure.data)


def test_fleet_annual_stock_is_december_and_proxy_is_not_recomputed():
    frame = source("annual_fleet")
    original = frame.copy(deep=True)
    stock = fleet_chart(frame, frequency="Annual")
    proxy = fleet_chart(frame, frequency="Annual", metric="Journeys per licensed vehicle-day proxy")
    assert trace(stock, "GMB").y[0] == 3203
    assert trace(stock, "GMB").y[-1] == 3360
    assert trace(proxy, "GMB").y[-1] == pytest.approx(404.86489912161126)
    for mode in ("GMB", "RMB"):
        expected = frame.loc[frame["mode"].eq(mode)].sort_values("year").average_daily_journeys_per_licensed_vehicle.tolist()
        assert list(trace(proxy, mode).y) == expected
    assert "Licensed vehicles" == stock.layout.yaxis.title.text
    assert "vehicle-day proxy" in proxy.layout.yaxis.title.text
    pd.testing.assert_frame_equal(frame, original)


def test_fleet_monthly_and_indexed_prepared_values_keep_distinct_units():
    monthly = source("fleet_normalized")
    stock = fleet_chart(monthly)
    proxy = fleet_chart(monthly, metric="Journeys per licensed vehicle-day proxy")
    assert trace(stock, "RMB").y[0] == 1199
    assert trace(proxy, "RMB").y[0] == pytest.approx(291.438591299201)
    annual = source("annual_fleet")
    baselines = annual.loc[annual.year.eq(2015)].set_index("mode").december_licensed_vehicles
    annual["value"] = annual.december_licensed_vehicles / annual["mode"].map(baselines) * 100
    indexed = fleet_chart(annual.loc[annual.year.ge(2020)], frequency="Annual", indexed=True)
    assert trace(indexed, "RMB").y[-1] == pytest.approx(693 / 1141 * 100)
    assert "2015 = 100" in indexed.layout.yaxis.title.text
    with pytest.raises(ValueError, match="annual series"):
        fleet_chart(monthly, indexed=True)


@pytest.mark.parametrize("builder,name", [
    (recovery_bar, "recovery_2019"), (baseline_comparison_chart, "recovery_2019"),
    (recovery_trend_chart, "annual_recovery"), (share_chart, "annual_market_share"),
    (composition_chart, "annual_minibus_composition"),
])
def test_empty_chart_selection_returns_readable_message(builder, name):
    figure = builder(source(name).iloc[:0])
    assert len(figure.data) == 0
    assert any("No observations" in item.text for item in figure.layout.annotations)


def test_empty_generic_selection_and_missing_fields():
    frame = pd.DataFrame(columns=["year", "mode", "value"])
    assert "No observations" in series_chart(frame).layout.annotations[0].text
    with pytest.raises(ValueError, match="missing columns"):
        trend_chart(pd.DataFrame(columns=["mode"]))


@pytest.mark.parametrize("damage,message", [
    ("missing", "missing values"), ("infinite", "finite nonnegative"),
    ("negative", "finite nonnegative"), ("duplicate", "duplicate"),
    ("unsupported_mode", "Unsupported modes"), ("fractional_year", "integers"),
])
def test_bad_chart_inputs_are_rejected_instead_of_drawn(damage, message):
    frame = pd.DataFrame({"year": [2015, 2025], "mode": ["GMB", "GMB"], "value": [100.0, 90.0]})
    if damage == "missing":
        frame.loc[0, "value"] = np.nan
    elif damage == "infinite":
        frame.loc[0, "value"] = np.inf
    elif damage == "negative":
        frame.loc[0, "value"] = -1
    elif damage == "duplicate":
        frame = pd.concat([frame, frame.iloc[[0]]])
    elif damage == "unsupported_mode":
        frame.loc[0, "mode"] = "UNKNOWN"
    elif damage == "fractional_year":
        frame["year"] = [2015.5, 2025]
    with pytest.raises(ValueError, match=message):
        trend_chart(frame)


def test_disruption_shading_does_not_expand_filtered_year_range():
    frame = pd.DataFrame({"year": [2021, 2022, 2023], "mode": ["GMB"] * 3, "value": [80, 78, 85]})
    figure = trend_chart(frame)
    rectangle = next(shape for shape in figure.layout.shapes if shape.type == "rect")
    assert rectangle.x0 == 2021
    assert rectangle.x1 == 2022
    later = trend_chart(frame.loc[frame.year.ge(2023)])
    assert not later.layout.shapes


def test_percentage_range_is_specific_to_shares_not_recovery():
    frame = source("annual_market_share")
    frame.loc[0, "share_pct"] = 101
    with pytest.raises(ValueError, match="100% share"):
        share_chart(frame)
    recovery = source("recovery_2019")
    recovery.loc[recovery["mode"].eq("MTR"), "recovery_pct"] = 130
    figure = recovery_bar(recovery)
    assert figure.layout.xaxis.range[1] > 130


@pytest.mark.parametrize("builder,name,value_column", [
    (share_chart, "annual_market_share", "share_pct"),
    (composition_chart, "annual_minibus_composition", "share_of_plb_pct"),
])
def test_single_year_area_selection_renders_visible_bars_with_preserved_shares(builder, name, value_column):
    frame = source(name).query("year == 2025")
    figure = builder(frame)
    assert figure.layout.barmode == "stack"
    assert all(item.type == "bar" and item.width > 0 for item in figure.data)
    for mode in frame["mode"]:
        assert list(trace(figure, mode).y) == frame.loc[frame["mode"].eq(mode), value_column].tolist()
    assert sum(item.y[0] for item in figure.data) == pytest.approx(100)
    if builder is share_chart:
        subset = builder(frame.loc[frame["mode"].isin(("GMB", "RMB"))])
        assert sum(item.y[0] for item in subset.data) < 20


def test_titles_and_legends_reserve_space_for_narrow_containers():
    frame = pd.DataFrame({"year": [2015, 2025], "mode": ["GMB", "GMB"], "value": [100.0, 90.0]})
    title = "Green and Red Minibuses: the decade in perspective"
    figure = trend_chart(frame, title=title)
    assert figure.layout.title.text.replace("<br>", " ") == title
    assert all(len(line) <= 32 for line in figure.layout.title.text.split("<br>"))
    assert figure.layout.margin.t >= 80
    assert figure.layout.margin.b >= 200
    assert figure.layout.legend.y == -0.40
    assert figure.layout.legend.maxheight == 80
    plot_height = figure.layout.height - figure.layout.margin.t - figure.layout.margin.b
    legend_offset = plot_height * abs(figure.layout.legend.y)
    assert legend_offset >= 80  # Keep the legend below rotated years + axis title.
    assert legend_offset + figure.layout.legend.maxheight <= figure.layout.margin.b
