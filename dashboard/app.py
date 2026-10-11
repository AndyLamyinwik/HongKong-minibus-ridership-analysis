"""Streamlit entry point; reads the preserved Phase 3 analytical outputs."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st

from hk_minibus.dashboard import charts
from hk_minibus.dashboard.components import (
    apply_style, export_table, finding, methodology, mode_picker, page_header, plot, source_note,
)
from hk_minibus.dashboard.data import DataLoadError, load_dashboard_data, source_fingerprint
from hk_minibus.dashboard.metrics import (
    MINIBUS_MODES, MODES, MODE_LABELS, fleet_endpoints, headline_metrics,
    ridership_endpoints, select_rows, share_endpoints, trend_data,
)


SECTIONS = (
    "Executive Overview",
    "Ridership Trends",
    "COVID-19 Recovery",
    "Market Share & Industry Structure",
    "Fleet & Ridership Relationships",
)


@st.cache_data(show_spinner=False)
def cached_data(root: str, fingerprint: tuple):
    """The file signature invalidates cached frames when local inputs change."""
    return load_dashboard_data(Path(root))


def row(frame: pd.DataFrame, mode: str, **filters) -> pd.Series:
    selected = frame.loc[frame["mode"].eq(mode)]
    for column, value in filters.items():
        selected = selected.loc[selected[column].eq(value)]
    if len(selected) != 1:
        raise DataLoadError(f"Expected one {mode} row for {filters}; found {len(selected)}.")
    return selected.iloc[0]


def overview(data) -> None:
    page_header("01", "One industry. Two different futures.",
                "How have Green and Red Minibuses followed different paths over a decade?")
    st.caption(
        "Decade change: 2015 → 2025 annual journeys. Recovery: 2025 as % of 2019. "
        "RMB volumes are estimated; PLB combines GMB and estimated RMB journeys."
    )
    kpi = headline_metrics(data)
    cards = (
        ("PLB decade change", kpi["plb_change"], "2015 → 2025 annual journeys"),
        ("GMB decade change", kpi["gmb_change"], "2015 → 2025 annual journeys"),
        ("RMB decade change · estimated", kpi["rmb_change"], "2015 → 2025 annual journeys"),
        ("RMB recovery · 2019 baseline", kpi["rmb_recovery"], "2025 annual journeys as % of 2019"),
    )
    for column, (label, value, detail) in zip(st.columns(4), cards):
        with column:
            st.metric(label, f"{value:+.2f}%" if "change" in label else f"{value:.2f}%",
                      help=detail, border=True)
    measure = st.radio("Overview measure", ["Indexed (2015 = 100)", "Annual journeys (millions)"],
                       horizontal=True, key="overview_measure")
    indexed = measure.startswith("Indexed")
    frame = trend_data(data, frequency="Annual", indexed=indexed,
                       modes=("GMB", "RMB"), year_range=(2015, 2025))
    plot(charts.trend_chart(frame, frequency="Annual", indexed=indexed,
                           title="Green and Red Minibuses: the decade in perspective"), "overview_trend")
    source_note("annual_ridership.csv", "Annual index = each mode's annual journeys / its 2015 annual journeys × 100. The shaded interval marks 2020–2022.")
    segments = data.tables["trend_segments"]
    gmb_recent = row(segments, "GMB", segment="2023_to_2025")["change_pct"]
    rmb_recent = row(segments, "RMB", segment="2023_to_2025")["change_pct"]
    recent_column, composition_column = st.columns(2)
    with recent_column:
        finding("A recovery concentrated in Green Minibuses",
                f"From 2023 to 2025, GMB journeys changed **{gmb_recent:+.2f}%**, "
                f"while estimated RMB journeys changed **{rmb_recent:+.2f}%**.",
                "The combined PLB headline conceals different recent directions.")
    with composition_column:
        finding("An increasingly GMB-dominated industry",
                f"GMB accounted for **{kpi['gmb_share_2025']:.2f}%** of PLB journeys in 2025, "
                f"a change of **{kpi['gmb_share_change_pp']:+.2f} percentage points** since 2015.",
                "Composition describes aggregate journeys; it does not identify passenger switching.")
    st.markdown(
        "The study matters because the two minibus categories need separate treatment in transport "
        "planning and industry discussion. Explore their long-term paths, compare recovery with rail "
        "and franchised buses, and place demand alongside licensed fleet stock. The evidence "
        "describes historical change; its underlying causes remain open."
    )


def trends(data) -> None:
    page_header("02", "Ridership trends", "How do the long-term direction and monthly detail differ by mode?")
    modes = mode_picker("trends_modes", MODES, MINIBUS_MODES)
    first, second, third = st.columns([1.5, 1, 1.4])
    years = first.slider("Year range", 2015, 2025, (2015, 2025), key="trends_years")
    frequency = second.radio("Aggregation", ["Monthly", "Annual"], key="trends_frequency")
    measure = third.radio("Measure", ["Journeys (millions)", "Indexed trend"], key="trends_measure")
    indexed = measure == "Indexed trend"
    frame = trend_data(data, frequency=frequency, indexed=indexed, modes=modes, year_range=years)
    if frame.empty:
        st.info("Select at least one transport mode to explore ridership trends.")
        return
    plot(charts.trend_chart(frame, frequency=frequency, indexed=indexed,
                           title=f"{frequency} passenger journeys · {years[0]}–{years[1]}"), "ridership_trends")
    if indexed:
        definition = ("Each mode's annual journeys / its 2015 annual journeys × 100." if frequency == "Annual"
                      else "Each month's average daily journeys / the same mode's same-calendar-month daily rate in 2015 × 100. Every 2015 month equals 100.")
        st.caption(f"Index definition: {definition} The 2015 baseline stays fixed when filters change.")
    else:
        st.caption(f"Millions of journeys per {'calendar year' if frequency == 'Annual' else 'calendar month'}. Monthly totals reflect different month lengths; the monthly index uses daily rates.")
    result = ridership_endpoints(data, modes, years)
    st.markdown(f"**Annual endpoints for the selected period · {years[0]} → {years[1]}**")
    st.dataframe(result, hide_index=True, width="stretch", column_config={
        column: st.column_config.NumberColumn(format="%.2f") for column in result.columns[1:]})
    first_result = result.iloc[0]
    finding("What the selected years show",
            f"For **{first_result['Transport mode']}**, annual journeys changed "
            f"**{first_result['Annual endpoint change (%)']:+.2f}%** from {years[0]} to {years[1]}.",
            "Absolute levels describe volume; fixed-baseline indices help compare trajectories across different scales. A one-year selection compares the same annual total with itself.")
    source_name = "monthly_ridership" if frequency == "Monthly" else "annual_ridership"
    source_note(f"{source_name}.csv", "RMB is estimated; PLB overlaps its GMB/RMB components. MTR service coverage changed over time. The shaded interval is a timing label, not a causal estimate.")
    export_table(select_rows(data.tables[source_name], modes, years), "Download selected journey records",
                 f"{source_name}_{years[0]}_{years[1]}.csv", "download_trends")


def recovery(data) -> None:
    page_header("03", "COVID-19 recovery", "How far did each mode return to its own 2019 annual journey benchmark?")
    modes = mode_picker("recovery_modes", MODES, MODES)
    frame = data.tables["recovery_2019"].loc[lambda df: df["mode"].isin(modes)].copy()
    if frame.empty:
        st.info("Select at least one transport mode to compare recovery.")
        return
    st.caption("Recovery = 2025 annual journeys / 2019 annual journeys × 100. 100% is the benchmark; values above 100% exceed it.")
    benchmark, volumes, path = st.tabs(["Recovery benchmark", "2019 vs 2025 volumes", "Recovery path"])
    with benchmark:
        plot(charts.recovery_bar(frame), "recovery_bars")
    with volumes:
        plot(charts.baseline_comparison_chart(frame), "recovery_volumes")
    with path:
        plot(charts.recovery_trend_chart(select_rows(data.tables["annual_recovery"], modes, (2015, 2025))), "recovery_path")
    gmb, rmb, plb = (row(data.tables["recovery_2019"], mode)["recovery_pct"] for mode in MINIBUS_MODES)
    finding("Study finding · full 2015–2025 scope",
            f"In 2025, GMB reached **{gmb:.2f}%** of its 2019 journeys, estimated RMB **{rmb:.2f}%**, "
            f"and combined PLB **{plb:.2f}%**.",
            "The difference is persistent in the published aggregates. These ratios do not explain why demand changed; the study also documents an earlier 2015–2018 benchmark sensitivity.")
    table = frame.assign(**{"Transport mode": frame["mode"].map(MODE_LABELS),
                            "2019 journeys (million)": frame["baseline_2019_journeys_thousands"] / 1000,
                            "2025 journeys (million)": frame["journeys_2025_thousands"] / 1000,
                            "Recovery (%)": frame["recovery_pct"]})
    st.dataframe(table[["Transport mode", "2019 journeys (million)", "2025 journeys (million)", "Recovery (%)"]],
                 hide_index=True, width="stretch", column_config={
                     c: st.column_config.NumberColumn(format="%.2f") for c in table.columns if c.endswith("(million)") or c == "Recovery (%)"})
    source_note("recovery_2019.csv; annual_recovery.csv", "RMB is estimated; PLB includes estimates. MTR includes cross-boundary services and changing railway coverage. PLB and its components are overlapping comparison series.")
    export_table(frame, "Download selected recovery records", "recovery_2019_selected.csv", "download_recovery")


def shares(data) -> None:
    page_header("04", "Market share & industry structure", "How did the selected transport shares and minibus composition change?")
    first, second, third = st.columns([1.5, 1, 1.3])
    years = first.slider("Year range", 2015, 2025, (2015, 2025), key="share_years")
    frequency = second.radio("Aggregation", ["Annual", "Monthly"], key="share_frequency")
    style = third.radio("Share view", ["Stacked area", "Share lines"], key="share_view")
    name = "annual_market_share" if frequency == "Annual" else "monthly_market_share"
    frame = select_rows(data.tables[name], ("GMB", "RMB", "MTR", "FRANCHISED_BUS"), years)
    st.caption("Share within selected public transport modes · denominator: GMB + RMB + MTR railway services + franchised buses. PLB is the GMB/RMB subtotal.")
    plot(charts.share_chart(frame, frequency=frequency, style="Area" if style == "Stacked area" else "Lines"), "transport_shares")
    endpoints = share_endpoints(data, years)
    finding("PLB's position within the comparison group",
            f"Combined PLB share was **{endpoints['plb_start']:.2f}%** in {years[0]} and **{endpoints['plb_end']:.2f}%** in {years[1]}, "
            f"a change of **{endpoints['plb_change_pp']:+.2f} percentage points**.",
            "Shares depend on changes in both minibus journeys and the comparison-group total. They do not measure all Hong Kong travel or identify individual mode switching.")
    source_note(f"{name}.csv", "All four share denominators contain estimated RMB. Annual shares use annual flow totals.")
    st.subheader("Within the minibus industry")
    composition_name = "annual_minibus_composition" if frequency == "Annual" else "minibus_composition"
    composition = select_rows(data.tables[composition_name], ("GMB", "RMB"), years)
    plot(charts.composition_chart(composition, frequency=frequency), "minibus_composition")
    st.markdown(f"GMB's annual share of PLB journeys moved from **{endpoints['gmb_start']:.2f}%** to **{endpoints['gmb_end']:.2f}%** "
                f"across these years (**{endpoints['gmb_change_pp']:+.2f} pp**). RMB volumes remain estimates.")
    source_note(f"{composition_name}.csv", "Composition = category journeys / (GMB + RMB journeys) × 100; its denominator differs from the transport-share chart above.")
    export_table(frame, "Download selected transport shares", f"{name}_selected.csv", "download_shares")


def fleet(data) -> None:
    page_header("05", "Fleet & ridership relationships", "How do licensed stocks and journeys relative to those stocks move together?")
    modes = mode_picker("fleet_modes", ("GMB", "RMB"), ("GMB", "RMB"))
    first, second = st.columns([2, 1])
    years = first.slider("Year range", 2015, 2025, (2015, 2025), key="fleet_years")
    frequency = second.radio("Aggregation", ["Monthly", "Annual"], key="fleet_frequency")
    if not modes:
        st.info("Select at least one minibus category to explore licensed fleet context.")
        return
    name = "fleet_normalized" if frequency == "Monthly" else "annual_fleet"
    frame = select_rows(data.tables[name], modes, years)
    st.caption("Licensed vehicles are administrative stocks. They do not reveal daily deployed vehicles or passenger occupancy.")
    stock, relative = st.tabs(["Licensed fleet", "Journeys relative to licensed stock"])
    with stock:
        plot(charts.fleet_chart(frame, frequency=frequency, metric="Licensed fleet"), "licensed_fleet")
        st.caption("Month-end licensed vehicles." if frequency == "Monthly" else "December licensed vehicles in each year; this is an endpoint stock, not a monthly average.")
    with relative:
        plot(charts.fleet_chart(frame, frequency=frequency, metric="Journeys per licensed vehicle-day proxy"), "fleet_relative")
        st.caption("Monthly: average daily journeys × 1,000 / month-end licensed vehicles." if frequency == "Monthly"
                   else "Annual: journeys × 1,000 / Σ(month-end licensed vehicles × calendar days). This preserves the Phase 3 annual vehicle-day proxy.")
    table = fleet_endpoints(data, modes, years)
    st.markdown(f"**Annual context · {years[0]} → {years[1]}**")
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        "December stock change (%)": st.column_config.NumberColumn(format="%.2f"),
        "Annual proxy change (%)": st.column_config.NumberColumn(format="%.2f"),
        f"Dec {years[0]} vehicles": st.column_config.NumberColumn(format="%d"),
        f"Dec {years[1]} vehicles": st.column_config.NumberColumn(format="%d"),
    })
    selected = table.iloc[0]
    finding("Fleet context for the selected years",
            f"For **{selected['Transport mode']}**, December licensed stock changed "
            f"**{selected['December stock change (%)']:+.2f}%** and the annual journey/vehicle-day proxy "
            f"changed **{selected['Annual proxy change (%)']:+.2f}%**.",
            "A licensed-stock ratio describes historical demand relative to administrative stock. It does not measure actual occupancy, utilization or operational productivity; RMB demand estimation already uses fleet information.")
    source_note(f"{name}.csv", "Fleet counts are reported; RMB passenger values are estimated. Comparable RMB mileage is unavailable.")
    export_table(frame, "Download selected fleet context", f"{name}_selected.csv", "download_fleet")


def main() -> None:
    st.set_page_config(page_title="Hong Kong Minibus Ridership · 2015–2025", page_icon="◉", layout="wide")
    apply_style()
    with st.sidebar:
        st.markdown("### Hong Kong\nMinibus Ridership")
        st.caption("A DECADE IN TRANSITION  /  2015–2025")
        st.divider()
        section = st.radio("Explore the study", SECTIONS, key="section")
        st.divider()
        st.markdown("**Reading the evidence**")
        st.caption("RMB journeys are estimated. PLB includes those estimates. Comparisons describe historical change.")
        st.markdown(f"[Official data catalogue](https://data.gov.hk/en-data/dataset/hk-td-tis_17-monthly-traffic-and-transport-digest-csv)")
        st.caption("Open ‘Sources & methodology’ below each section for definitions, formulas and revision notes.")
    try:
        data = cached_data(str(ROOT), source_fingerprint(ROOT))
        {SECTIONS[0]: overview, SECTIONS[1]: trends, SECTIONS[2]: recovery,
         SECTIONS[3]: shares, SECTIONS[4]: fleet}[section](data)
        methodology(data, ROOT)
    except DataLoadError as error:
        st.error(f"The historical data could not be loaded: {error}")
        st.info("Restore the included analysis/outputs files and source metadata from the same project snapshot, then reload the page. See docs/dashboard.md for the required files.")
        st.stop()


if __name__ == "__main__":
    main()
