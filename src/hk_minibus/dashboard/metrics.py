"""Display selectors and transparent indices over the preserved analytical tables."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from .data import DashboardData, MODES, SHARE_MODES


MINIBUS_MODES = ("GMB", "RMB", "PLB")
MODE_LABELS = {
    "GMB": "Green Minibuses",
    "RMB": "Red Minibuses (estimated)",
    "PLB": "Total Public Light Bus (includes estimates)",
    "MTR": "MTR railway services",
    "FRANCHISED_BUS": "Franchised buses",
}
COLORS = {"GMB": "#00796B", "RMB": "#BD4551", "PLB": "#263746", "MTR": "#087EA4", "FRANCHISED_BUS": "#B56A19"}
ANNUAL_INDEX_LABEL = "Index: own 2015 annual journeys = 100"
MONTHLY_INDEX_LABEL = "Index: same calendar month’s 2015 average daily journeys = 100"


def select_rows(frame: pd.DataFrame, modes: Iterable[str], year_range: tuple[int, int]) -> pd.DataFrame:
    """Select mode and inclusive year bounds without altering the source frame."""
    chosen = tuple(modes)
    start, end = year_range
    if start > end:
        raise ValueError("The start year cannot follow the end year.")
    if "year" in frame:
        years = pd.to_numeric(frame["year"], errors="raise")
    elif "month" in frame:
        years = pd.to_datetime(frame["month"], errors="raise").dt.year
    else:
        raise ValueError("Date filtering requires a year or month field.")
    return frame.loc[frame["mode"].isin(chosen) & years.between(start, end)].copy(deep=True)


def trend_data(data: DashboardData, *, frequency: str = "Annual", indexed: bool = False,
               modes: Iterable[str] = MINIBUS_MODES, year_range: tuple[int, int] = (2015, 2025)) -> pd.DataFrame:
    """Prepare x/mode/value for display, retaining the full-window 2015 baseline.

    Absolute views are million journeys per month or per year. The annual index
    divides annual totals by each mode's 2015 total. The monthly index divides
    average daily rates by the same calendar month's 2015 daily rate, avoiding
    month-length effects. A filtered view never resets its reference period.
    """
    if frequency not in ("Annual", "Monthly"):
        raise ValueError("Frequency must be Annual or Monthly.")
    name = "annual_ridership" if frequency == "Annual" else "monthly_ridership"
    source = data.table(name)
    source["x"] = source["year"] if frequency == "Annual" else pd.to_datetime(source["month"])
    if indexed and frequency == "Annual":
        baseline = source[source["year"].eq(2015)].set_index("mode")["passenger_journeys_thousands"]
        source["value"] = 100 * source["passenger_journeys_thousands"] / source["mode"].map(baseline)
    elif indexed:
        source["calendar_month"] = source["x"].dt.month
        baseline = source[source["x"].dt.year.eq(2015)].set_index(["mode", "calendar_month"])["average_daily_journeys_thousands"]
        keys = pd.MultiIndex.from_frame(source[["mode", "calendar_month"]])
        source["value"] = 100 * source["average_daily_journeys_thousands"].to_numpy() / baseline.reindex(keys).to_numpy()
    else:
        source["value"] = source["passenger_journeys_thousands"] / 1000
    selected = select_rows(source, modes, year_range)
    return selected.sort_values(["mode", "x"]).reset_index(drop=True)


def headline_metrics(data: DashboardData) -> dict[str, float]:
    """Read the approved full-window headline metrics from existing outputs."""
    endpoint = data.table("endpoint_comparison").set_index("mode")
    composition = data.table("annual_minibus_composition")
    gmb_composition = composition[composition["mode"].eq("GMB")].set_index("year")["share_of_plb_pct"]
    shares = data.table("annual_market_share")
    plb_shares = shares[shares["mode"].isin(("GMB", "RMB"))].groupby("year")["share_pct"].sum()
    return {
        "plb_change": float(endpoint.loc["PLB", "change_2015_2025_pct"]),
        "gmb_change": float(endpoint.loc["GMB", "change_2015_2025_pct"]),
        "rmb_change": float(endpoint.loc["RMB", "change_2015_2025_pct"]),
        "rmb_recovery": float(endpoint.loc["RMB", "recovery_2025_vs_2019_pct"]),
        "gmb_share_2015": float(gmb_composition.loc[2015]),
        "gmb_share_2025": float(gmb_composition.loc[2025]),
        "gmb_composition_change_pp": float(gmb_composition.loc[2025] - gmb_composition.loc[2015]),
        "gmb_share_change_pp": float(gmb_composition.loc[2025] - gmb_composition.loc[2015]),
        "plb_selected_share_2015": float(plb_shares.loc[2015]),
        "plb_selected_share_2025": float(plb_shares.loc[2025]),
        "plb_selected_share_change_pp": float(plb_shares.loc[2025] - plb_shares.loc[2015]),
    }


def period_change(frame: pd.DataFrame, value_column: str, start: int, end: int) -> pd.DataFrame:
    """Compare two existing annual records per mode; do not rebuild annual flows."""
    if start > end:
        raise ValueError("The start year cannot follow the end year.")
    if frame.duplicated(["year", "mode"]).any():
        raise ValueError("Annual comparisons require a unique year/mode key.")
    selected = frame[frame["year"].isin((start, end))].pivot(index="mode", columns="year", values=value_column)
    if start not in selected or end not in selected:
        return pd.DataFrame(columns=["mode", "start_value", "end_value", "absolute_change", "change_pct"])
    result = pd.DataFrame({"start_value": selected[start], "end_value": selected[end]})
    result["absolute_change"] = result["end_value"] - result["start_value"]
    result["change_pct"] = 100 * (result["end_value"] / result["start_value"].where(result["start_value"].ne(0)) - 1)
    return result.reset_index()


def _ordered_comparison(frame: pd.DataFrame, modes: Iterable[str]) -> pd.DataFrame:
    """Keep the caller's mode order and avoid manufacturing unavailable rows."""
    selected = tuple(dict.fromkeys(modes))
    indexed = frame.set_index("mode")
    return indexed.reindex([mode for mode in selected if mode in indexed.index])


def ridership_endpoints(data: DashboardData, modes: Iterable[str],
                        year_range: tuple[int, int]) -> pd.DataFrame:
    """Format selected annual journey endpoints using preserved annual totals."""
    start, end = year_range
    comparison = _ordered_comparison(
        period_change(data.table("annual_ridership"), "passenger_journeys_thousands", start, end), modes)
    columns = list(dict.fromkeys(("Transport mode", f"{start} annual journeys (million)",
                                 f"{end} annual journeys (million)", "Annual endpoint change (%)")))
    rows = [{"Transport mode": MODE_LABELS[mode],
             f"{start} annual journeys (million)": row["start_value"] / 1000,
             f"{end} annual journeys (million)": row["end_value"] / 1000,
             "Annual endpoint change (%)": row["change_pct"]}
            for mode, row in comparison.iterrows()]
    return pd.DataFrame(rows, columns=columns)


def fleet_endpoints(data: DashboardData, modes: Iterable[str], years: tuple[int, int]) -> pd.DataFrame:
    """Compare December stocks and the existing annual vehicle-day indicators."""
    start, end = years
    annual = data.table("annual_fleet")
    stock = _ordered_comparison(period_change(annual, "december_licensed_vehicles", start, end), modes)
    proxy = period_change(annual, "average_daily_journeys_per_licensed_vehicle", start, end).set_index("mode")
    columns = list(dict.fromkeys(("Transport mode", f"Dec {start} vehicles", f"Dec {end} vehicles",
                                 "December stock change (%)", "Annual proxy change (%)")))
    rows = [{"Transport mode": MODE_LABELS[mode],
             f"Dec {start} vehicles": row["start_value"],
             f"Dec {end} vehicles": row["end_value"],
             "December stock change (%)": row["change_pct"],
             "Annual proxy change (%)": proxy.loc[mode, "change_pct"]}
            for mode, row in stock.iterrows()]
    return pd.DataFrame(rows, columns=columns)


def share_endpoints(data: DashboardData, years: tuple[int, int]) -> dict[str, float]:
    """Read annual PLB subgroup shares and GMB composition, preserving denominators."""
    start, end = years
    if start > end:
        raise ValueError("The start year cannot follow the end year.")
    shares = data.table("annual_market_share")
    composition = data.table("annual_minibus_composition")
    plb = shares[shares["mode"].isin(("GMB", "RMB"))].groupby("year")["share_pct"].sum()
    gmb = composition[composition["mode"].eq("GMB")].set_index("year")["share_of_plb_pct"]
    if any(year not in plb.index or year not in gmb.index for year in years):
        raise ValueError("Selected share endpoints must be available within the validated study window.")
    return {
        "plb_start": float(plb.loc[start]),
        "plb_end": float(plb.loc[end]),
        "plb_change_pp": float(plb.loc[end] - plb.loc[start]),
        "gmb_start": float(gmb.loc[start]),
        "gmb_end": float(gmb.loc[end]),
        "gmb_change_pp": float(gmb.loc[end] - gmb.loc[start]),
    }
