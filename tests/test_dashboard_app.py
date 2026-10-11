"""Exercise the real Streamlit entry point against the preserved analysis tables."""

import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "dashboard" / "app.py"
SECTIONS = (
    "Executive Overview",
    "Ridership Trends",
    "COVID-19 Recovery",
    "Market Share & Industry Structure",
    "Fleet & Ridership Relationships",
)


@pytest.fixture
def app():
    return AppTest.from_file(APP, default_timeout=30).run()


def _visit(app, section):
    app.sidebar.radio(key="section").set_value(section).run()
    assert not app.exception
    assert not app.error
    return app


def _percentage(value):
    return float(value.replace("%", "").replace("−", "-").replace(",", "").strip())


def _chart(app, index=0):
    return json.loads(app.get("plotly_chart")[index].proto.spec)


def test_overview_four_kpis_agree_with_existing_phase3_tables(app):
    endpoints = pd.read_csv(ROOT / "analysis" / "outputs" / "endpoint_comparison.csv").set_index("mode")
    recovery = pd.read_csv(ROOT / "analysis" / "outputs" / "recovery_2019.csv").set_index("mode")
    expected = {
        "PLB decade change": endpoints.loc["PLB", "change_2015_2025_pct"],
        "GMB decade change": endpoints.loc["GMB", "change_2015_2025_pct"],
        "RMB decade change · estimated": endpoints.loc["RMB", "change_2015_2025_pct"],
        "RMB recovery · 2019 baseline": recovery.loc["RMB", "recovery_pct"],
    }
    assert not app.exception
    assert not app.error
    actual = {metric.label: _percentage(metric.value) for metric in app.metric}
    assert actual.keys() == expected.keys()
    for label, value in expected.items():
        assert actual[label] == pytest.approx(value, abs=0.0051)


@pytest.mark.parametrize("section", SECTIONS)
def test_every_main_section_renders_charts_and_accessible_methodology(app, section):
    _visit(app, section)
    assert len(app.get("plotly_chart")) >= 1
    assert any(expander.label == "Sources & methodology" for expander in app.expander)
    text = "\n".join(element.value for element in app.markdown) + "\n" + "\n".join(element.value for element in app.caption)
    assert "2015" in text
    assert "2025" in text
    assert "estimated" in text.lower()


def test_overview_measure_can_switch_to_absolute_annual_journeys(app):
    app.radio(key="overview_measure").set_value("Annual journeys (millions)").run()
    assert not app.exception
    assert len(app.get("plotly_chart")) >= 1
    assert len(app.metric) == 4


@pytest.mark.parametrize("frequency", ["Monthly", "Annual"])
@pytest.mark.parametrize("measure", ["Journeys (millions)", "Indexed trend"])
def test_trend_frequency_measure_mode_and_year_controls_run(app, frequency, measure):
    _visit(app, "Ridership Trends")
    app.multiselect(key="trends_modes").set_value(["RMB"]).run()
    app.slider(key="trends_years").set_value((2023, 2025)).run()
    app.radio(key="trends_frequency").set_value(frequency).run()
    app.radio(key="trends_measure").set_value(measure).run()
    assert not app.exception
    assert not app.error
    assert app.multiselect(key="trends_modes").value == ["RMB"]
    assert app.slider(key="trends_years").value == (2023, 2025)
    assert app.radio(key="trends_frequency").value == frequency
    assert app.radio(key="trends_measure").value == measure
    assert len(app.get("plotly_chart")) >= 1
    rendered = _chart(app)["data"]
    assert len(rendered) == 1
    assert "RMB" in rendered[0]["name"]
    assert len(rendered[0]["x"]) == (36 if frequency == "Monthly" else 3)
    displayed_years = {int(str(value)[:4]) for value in rendered[0]["x"]}
    assert displayed_years == {2023, 2024, 2025}
    comparison = app.dataframe[0].value
    assert len(comparison) == 1
    assert comparison["Transport mode"].iloc[0] == "Red Minibuses (estimated)"
    annual = pd.read_csv(ROOT / "analysis" / "outputs" / "annual_ridership.csv")
    annual = annual.loc[annual["mode"].eq("RMB")].set_index("year")
    assert comparison["2023 annual journeys (million)"].iloc[0] == pytest.approx(
        annual.loc[2023, "passenger_journeys_thousands"] / 1000
    )
    assert comparison["2025 annual journeys (million)"].iloc[0] == pytest.approx(
        annual.loc[2025, "passenger_journeys_thousands"] / 1000
    )


@pytest.mark.parametrize(
    ("section", "key"),
    [
        ("Ridership Trends", "trends_modes"),
        ("COVID-19 Recovery", "recovery_modes"),
        ("Fleet & Ridership Relationships", "fleet_modes"),
    ],
)
def test_empty_mode_selections_have_readable_guidance_without_runtime_errors(app, section, key):
    _visit(app, section)
    app.multiselect(key=key).set_value([]).run()
    assert not app.exception
    assert not app.error
    assert len(app.info) >= 1
    assert not app.get("plotly_chart")


def test_recovery_all_modes_and_mtr_above_baseline_are_supported(app):
    _visit(app, "COVID-19 Recovery")
    modes = ["GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"]
    app.multiselect(key="recovery_modes").set_value(modes).run()
    assert not app.exception
    assert not app.error
    assert app.multiselect(key="recovery_modes").value == modes
    assert len(app.get("plotly_chart")) >= 1
    chart = _chart(app)
    bars = chart["data"][0]
    assert len(bars["x"]) == 5
    mtr_index = bars["y"].index("MTR railway")
    assert bars["x"][mtr_index] > 100
    assert chart["layout"]["xaxis"]["range"][1] > bars["x"][mtr_index]
    assert any(shape.get("x0") == shape.get("x1") == 100 for shape in chart["layout"]["shapes"])


@pytest.mark.parametrize("frequency", ["Monthly", "Annual"])
@pytest.mark.parametrize("view", ["Stacked area", "Share lines"])
def test_market_share_view_frequency_and_year_controls_run(app, frequency, view):
    _visit(app, "Market Share & Industry Structure")
    app.radio(key="share_frequency").set_value(frequency).run()
    app.radio(key="share_view").set_value(view).run()
    app.slider(key="share_years").set_value((2019, 2025)).run()
    assert not app.exception
    assert not app.error
    assert len(app.get("plotly_chart")) >= 1
    traces = _chart(app)["data"]
    assert len(traces) == 4
    assert {trace["name"] for trace in traces} == {
        "GMB", "RMB (estimated)", "MTR railway", "Franchised buses"
    }
    assert all(len(trace["x"]) == (84 if frequency == "Monthly" else 7) for trace in traces)
    for values in zip(*(trace["y"] for trace in traces), strict=True):
        assert sum(values) == pytest.approx(100, abs=1e-9)


@pytest.mark.parametrize("frequency", ["Monthly", "Annual"])
def test_fleet_frequency_mode_and_year_controls_run(app, frequency):
    _visit(app, "Fleet & Ridership Relationships")
    app.multiselect(key="fleet_modes").set_value(["GMB"]).run()
    app.radio(key="fleet_frequency").set_value(frequency).run()
    app.slider(key="fleet_years").set_value((2018, 2025)).run()
    assert not app.exception
    assert not app.error
    assert app.multiselect(key="fleet_modes").value == ["GMB"]
    assert len(app.get("plotly_chart")) >= 1
    traces = _chart(app)["data"]
    assert len(traces) == 1
    assert traces[0]["name"] == "GMB"
    source_name = "fleet_normalized" if frequency == "Monthly" else "annual_fleet"
    source = pd.read_csv(ROOT / "analysis" / "outputs" / f"{source_name}.csv")
    years = pd.to_datetime(source["month"]).dt.year if frequency == "Monthly" else source["year"]
    selected = source.loc[source["mode"].eq("GMB") & years.between(2018, 2025)]
    column = "licensed_vehicles" if frequency == "Monthly" else "december_licensed_vehicles"
    assert traces[0]["y"] == pytest.approx(selected[column].tolist())


def test_missing_required_input_is_reported_by_app_without_a_traceback(monkeypatch):
    from hk_minibus.dashboard import data

    def missing_source(_root):
        raise data.DataLoadError(
            "Required historical input is unavailable: analysis/outputs/annual_ridership.csv"
        )

    # Inject an unavailable input; never rename, remove or change actual datasets.
    monkeypatch.setattr(data, "source_fingerprint", missing_source)
    result = AppTest.from_file(APP, default_timeout=30).run()
    assert not result.exception
    assert len(result.error) == 1
    assert "annual_ridership.csv" in result.error[0].value
    assert not result.metric
    assert not result.get("plotly_chart")


def test_entrypoint_resolves_data_relative_to_repository_instead_of_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    result = AppTest.from_file(APP, default_timeout=30).run()
    assert not result.exception
    assert not result.error
    assert len(result.metric) == 4


@pytest.mark.parametrize(
    ("section", "year_key", "frequency_key"),
    [
        ("Ridership Trends", "trends_years", "trends_frequency"),
        ("Market Share & Industry Structure", "share_years", "share_frequency"),
        ("Fleet & Ridership Relationships", "fleet_years", "fleet_frequency"),
    ],
)
def test_same_year_annual_selection_is_defined_and_renders_without_errors(app, section, year_key, frequency_key):
    _visit(app, section)
    app.radio(key=frequency_key).set_value("Annual").run()
    app.slider(key=year_key).set_value((2025, 2025)).run()
    assert not app.exception
    assert not app.error
    assert len(app.get("plotly_chart")) >= 1
    if section == "Ridership Trends":
        comparison = app.dataframe[0].value
        assert comparison["Annual endpoint change (%)"].eq(0).all()
    if section == "Fleet & Ridership Relationships":
        comparison = app.dataframe[0].value
        assert comparison["December stock change (%)"].eq(0).all()
        assert comparison["Annual proxy change (%)"].eq(0).all()
