"""Static research figures from the validated Phase 3 analytical tables.

Charts consume analytical outputs rather than reading or rewriting Phase 2
datasets. Displaying thousands of journeys as millions changes only the chart
scale; the saved numerical tables retain their analytical units and precision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, PercentFormatter
import pandas as pd


COLOURS = {
    "GMB": "#00796B",
    "RMB": "#BD4551",
    "PLB": "#263746",
    "MTR": "#0072B2",
    "FRANCHISED_BUS": "#D55E00",
}
LABELS = {
    "GMB": "Green Minibuses (GMB)",
    "RMB": "Red Minibuses (RMB, estimated)",
    "PLB": "Public Light Buses (GMB + RMB)",
    "MTR": "MTR railway services",
    "FRANCHISED_BUS": "Franchised buses",
}
SOURCE_NOTE = (
    "Source: Transport Department, HKSAR Government; preserved CSV snapshot "
    "revised 21 September 2026."
)
STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "axes.edgecolor": "#BDC6CD",
    "axes.labelcolor": "#263746",
    "text.color": "#263746",
    "xtick.color": "#485A68",
    "ytick.color": "#485A68",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "legend.frameon": False,
    "lines.linewidth": 2.2,
    "grid.color": "#DDE3E8",
    "grid.linewidth": 0.7,
    "grid.alpha": 0.9,
    "axes.axisbelow": True,
}


def _table(tables: dict[str, pd.DataFrame], name: str, columns: list[str]) -> pd.DataFrame:
    if name not in tables:
        raise ValueError(f"Figure input is missing analytical table {name!r}.")
    frame = tables[name].copy()
    absent = set(columns) - set(frame.columns)
    if absent:
        raise ValueError(f"Figure input {name!r} is missing columns: {sorted(absent)}")
    if frame.empty or frame[columns].isna().any().any():
        raise ValueError(f"Required figure fields in {name!r} must be present and nonnull.")
    return frame


def _heading(fig: Any, title: str, subtitle: str) -> None:
    fig.text(0.085, 0.963, title, fontsize=18, fontweight="bold", va="top")
    fig.text(0.085, 0.915, subtitle, fontsize=10.5, va="top", color="#485A68")


def _footer(fig: Any, note: str, tables: list[str]) -> None:
    fig.text(
        0.085, 0.035,
        f"{note}\n{SOURCE_NOTE}\nAnalysis outputs: {', '.join(name + '.csv' for name in tables)}.",
        fontsize=8.3, color="#485A68", va="bottom", linespacing=1.45,
    )


def _axis(ax: Any, ylabel: str, *, percent: bool = False) -> None:
    ax.set_ylabel(ylabel, labelpad=12)
    ax.grid(axis="y")
    ax.tick_params(axis="both", length=0, pad=7)
    if percent:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    else:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))


def _months(ax: Any, dates: pd.Series, *, disruption: bool = False) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(dates.min(), dates.max())
    if disruption:
        ax.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2023-01-01"),
                   color="#8899A6", alpha=0.12, zorder=0)


def _years(ax: Any, years: pd.Series) -> None:
    values = sorted(years.unique())
    ax.set_xticks(values)
    ax.set_xlim(min(values) - 0.2, max(values) + 0.2)


def _legend(fig: Any, ax: Any, *, columns: int = 2, y: float = 0.881) -> None:
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.078, y),
               ncol=columns, fontsize=9.3, columnspacing=2, handlelength=2.5)


def _save(fig: Any, output_dir: Path, figure_id: str, title: str,
          source_tables: list[str]) -> dict[str, Any]:
    filename = f"{figure_id}.png"
    try:
        fig.savefig(output_dir / filename, dpi=180)
    finally:
        plt.close(fig)
    return {"figure_id": figure_id, "filename": filename,
            "title": title, "source_tables": source_tables}


def _monthly(tables: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
    table = _table(tables, "monthly_ridership", ["month", "mode", "passenger_journeys_thousands"])
    table["month"] = pd.to_datetime(table["month"])
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.subplots_adjust(left=0.085, right=0.965, top=0.82, bottom=0.19)
    title = "Monthly minibus passenger journeys, 2015–2025"
    _heading(fig, title, "Monthly totals; the shaded interval identifies the 2020–2022 disruption period.")
    for mode in ("GMB", "RMB"):
        data = table.loc[table["mode"].eq(mode)].sort_values("month")
        ax.plot(data["month"], data["passenger_journeys_thousands"] / 1000,
                color=COLOURS[mode], label=LABELS[mode])
    _axis(ax, "Passenger journeys (millions per month)")
    _months(ax, table["month"], disruption=True)
    ax.set_ylim(bottom=0)
    _legend(fig, ax)
    _footer(fig, "Monthly totals vary with calendar days. RMB values are estimates; journeys do not count unique people.",
            ["monthly_ridership"])
    return _save(fig, output_dir, "01_monthly_minibus_ridership", title, ["monthly_ridership"])


def _annual(tables: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
    table = _table(tables, "annual_ridership", ["year", "mode", "passenger_journeys_thousands"])
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.subplots_adjust(left=0.085, right=0.965, top=0.82, bottom=0.19)
    title = "Annual minibus passenger journeys, 2015–2025"
    _heading(fig, title, "Calendar-year totals calculated from the consistently prepared monthly records.")
    for mode in ("PLB", "GMB", "RMB"):
        data = table.loc[table["mode"].eq(mode)].sort_values("year")
        ax.plot(data["year"], data["passenger_journeys_thousands"] / 1000,
                color=COLOURS[mode], label=LABELS[mode], marker="o", markersize=4.5)
    _axis(ax, "Passenger journeys (millions per year)")
    _years(ax, table["year"])
    ax.set_ylim(bottom=0)
    _legend(fig, ax, columns=3)
    _footer(fig, "PLB is the sum of GMB and estimated RMB journeys; the three lines are overlapping series.",
            ["annual_ridership"])
    return _save(fig, output_dir, "02_annual_minibus_ridership", title, ["annual_ridership"])


def _composition(tables: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
    table = _table(tables, "minibus_composition", ["month", "mode", "share_of_plb_pct"])
    table["month"] = pd.to_datetime(table["month"])
    wide = table.pivot(index="month", columns="mode", values="share_of_plb_pct").sort_index()
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.subplots_adjust(left=0.085, right=0.965, top=0.82, bottom=0.19)
    title = "Composition of Public Light Bus journeys"
    _heading(fig, title, "Each month’s PLB passenger journeys = GMB journeys + RMB journeys; shares sum to 100%.")
    ax.stackplot(wide.index, wide["GMB"], wide["RMB"],
                 colors=[COLOURS["GMB"], COLOURS["RMB"]],
                 labels=[LABELS["GMB"], LABELS["RMB"]], alpha=0.9)
    _axis(ax, "Share of PLB passenger journeys", percent=True)
    _months(ax, table["month"])
    ax.set_ylim(0, 100)
    _legend(fig, ax)
    _footer(fig, "Composition reflects passenger journeys rather than passengers or fleet shares. RMB and therefore PLB include estimates.",
            ["minibus_composition"])
    return _save(fig, output_dir, "03_minibus_composition", title, ["minibus_composition"])


def _recovery(tables: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
    table = _table(tables, "annual_recovery", ["year", "mode", "recovery_pct"])
    fig, ax = plt.subplots(figsize=(12, 7.5))
    fig.subplots_adjust(left=0.085, right=0.965, top=0.795, bottom=0.22)
    title = "Passenger journeys relative to the 2019 baseline"
    _heading(fig, title, "Annual journeys / the same mode’s 2019 annual journeys × 100; 2019 = 100.")
    for mode in ("GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"):
        data = table.loc[table["mode"].eq(mode)].sort_values("year")
        ax.plot(data["year"], data["recovery_pct"], color=COLOURS[mode],
                label=LABELS[mode], marker="o", markersize=3.5,
                linestyle="--" if mode == "PLB" else "-")
    ax.axhline(100, color="#8899A6", linewidth=1.1, linestyle=(0, (3, 3)), zorder=0)
    _axis(ax, "Annual journeys index (2019 = 100)")
    _years(ax, table["year"])
    ax.set_ylim(bottom=0)
    _legend(fig, ax, columns=3)
    _footer(fig, "RMB is estimated; PLB overlaps its GMB/RMB components. MTR includes MTR Lines, Airport Express and Light Rail.\n"
            "Service coverage can change. A relative index is descriptive and does not identify causes of recovery differences.",
            ["annual_recovery"])
    return _save(fig, output_dir, "04_recovery_2019_baseline", title, ["annual_recovery"])


def _market_share(tables: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
    table = _table(tables, "annual_market_share", ["year", "mode", "share_pct"])
    wide = table.pivot(index="year", columns="mode", values="share_pct").sort_index()
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True,
                            gridspec_kw={"height_ratios": [1.1, 1]})
    fig.subplots_adjust(left=0.085, right=0.965, top=0.825, bottom=0.175, hspace=0.30)
    title = "Passenger shares within the defined transport comparison group"
    _heading(fig, title, "Annual denominator: GMB + RMB + MTR railway services + franchised buses; PLB is not added again.")
    modes = ["GMB", "RMB", "FRANCHISED_BUS", "MTR"]
    axes[0].stackplot(wide.index, *[wide[mode] for mode in modes],
                      colors=[COLOURS[mode] for mode in modes],
                      labels=[LABELS[mode] for mode in modes], alpha=0.9)
    _axis(axes[0], "Share of comparison group", percent=True)
    axes[0].set_ylim(0, 100)
    for mode in ("GMB", "RMB"):
        axes[1].plot(wide.index, wide[mode], color=COLOURS[mode], marker="o",
                     markersize=4, label=LABELS[mode])
    axes[1].plot(wide.index, wide["GMB"] + wide["RMB"], color=COLOURS["PLB"],
                 marker="o", markersize=4, linestyle="--", label="PLB share (GMB + RMB)")
    axes[1].set_title("Minibus shares on a separate, zero-based scale", loc="left", pad=13)
    _axis(axes[1], "Share of comparison group", percent=True)
    _years(axes[1], table["year"])
    axes[1].set_ylim(0, max(float((wide["GMB"] + wide["RMB"]).max()) * 1.15, 1))
    axes[1].legend(loc="upper right", fontsize=8.9)
    _legend(fig, axes[0], columns=2, y=0.884)
    _footer(fig, "Shares describe this comparison group, not all Hong Kong public transport. RMB and the denominator include estimates.\n"
            "Changes in rail service coverage and bus operating conditions limit interpretation as traveller mode switching.",
            ["annual_market_share"])
    return _save(fig, output_dir, "05_comparison_group_market_share", title, ["annual_market_share"])


def _seasonality(tables: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
    table = _table(tables, "seasonality", ["period", "mode", "calendar_month", "mean_within_year_daily_index"])
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    fig.subplots_adjust(left=0.085, right=0.965, top=0.78, bottom=0.225, wspace=0.15)
    title = "Calendar-month patterns in average daily minibus journeys"
    _heading(fig, title, "Within each year, monthly daily journeys / that year’s calendar-weighted daily average × 100.")
    periods = [("pre_pandemic", "Pre-pandemic: 2015–2019", "#0072B2"),
               ("post_pandemic", "Post-pandemic: 2023–2025", "#D55E00")]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for ax, mode in zip(axes, ("GMB", "RMB"), strict=True):
        for period, label, colour in periods:
            data = table.loc[table["period"].eq(period) & table["mode"].eq(mode)].sort_values("calendar_month")
            ax.plot(data["calendar_month"], data["mean_within_year_daily_index"],
                    color=colour, marker="o", markersize=4, label=label)
        ax.axhline(100, color="#8899A6", linewidth=1.1, linestyle=(0, (3, 3)), zorder=0)
        ax.set_title(LABELS[mode], loc="left", fontweight="bold", pad=14)
        ax.set_xticks(range(1, 13), months, rotation=45, ha="right")
        ax.set_xlim(0.7, 12.3)
        _axis(ax, "Mean within-year daily index" if mode == "GMB" else "")
    _legend(fig, axes[0], columns=2)
    _footer(fig, "Calendar months are averaged equally across years within each period. Daily rates remove differences in month length.\n"
            "The vertical scale is centred near 100 to reveal variation. Holidays, composition and short period lengths remain confounders; RMB is estimated.",
            ["seasonality"])
    return _save(fig, output_dir, "06_minibus_seasonality", title, ["seasonality"])


def _fleet(tables: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, Any]:
    table = _table(tables, "annual_fleet", ["year", "mode", "mean_month_end_licensed_vehicles",
                    "annual_passenger_journeys_thousands", "average_daily_journeys_per_licensed_vehicle"])
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True, sharey="row")
    fig.subplots_adjust(left=0.085, right=0.965, top=0.78, bottom=0.18,
                        wspace=0.17, hspace=0.33)
    title = "Minibus journeys and licensed fleet, 2015–2025"
    _heading(fig, title, "Upper panels compare indices; lower panels show a descriptive fleet-normalized daily demand indicator.")
    for column, mode in enumerate(("GMB", "RMB")):
        data = table.loc[table["mode"].eq(mode)].sort_values("year")
        baseline = data.loc[data["year"].eq(2015)]
        if len(baseline) != 1:
            raise ValueError(f"Fleet chart requires exactly one 2015 baseline for {mode}.")
        journeys_base = float(baseline["annual_passenger_journeys_thousands"].iloc[0])
        fleet_base = float(baseline["mean_month_end_licensed_vehicles"].iloc[0])
        if journeys_base <= 0 or fleet_base <= 0:
            raise ValueError("Fleet chart baseline must be positive.")
        upper, lower = axes[0, column], axes[1, column]
        upper.plot(data["year"], data["annual_passenger_journeys_thousands"] / journeys_base * 100,
                   color=COLOURS[mode], marker="o", markersize=4, label="Passenger journeys")
        upper.plot(data["year"], data["mean_month_end_licensed_vehicles"] / fleet_base * 100,
                   color="#778796", linestyle="--", marker="s", markersize=3.5,
                   label="Mean month-end licensed vehicles")
        upper.axhline(100, color="#BDC6CD", linestyle=(0, (3, 3)), linewidth=1, zorder=0)
        upper.set_title(LABELS[mode], loc="left", fontweight="bold", pad=13)
        _axis(upper, "Index (2015 = 100)" if column == 0 else "")
        upper.set_ylim(bottom=0)
        lower.plot(data["year"], data["average_daily_journeys_per_licensed_vehicle"],
                   color=COLOURS[mode], marker="o", markersize=4)
        _axis(lower, "Journeys per day per licensed vehicle" if column == 0 else "")
        _years(lower, table["year"])
        lower.set_ylim(bottom=0)
        lower.tick_params(axis="x", labelsize=8.5)
    _legend(fig, axes[0, 0], columns=2)
    _footer(fig, "Daily indicator = annual journeys / sum(month-end licensed vehicles × calendar days), using each month-end stock as a monthly proxy.\n"
            "Licensed vehicles are administrative stock, not deployed fleet. This is not occupancy, operational productivity or utilization.\n"
            "RMB patronage is estimated using licensed counts among other inputs, so patronage and fleet are not independent measurements.",
            ["annual_fleet"])
    return _save(fig, output_dir, "07_fleet_and_fleet_normalized_ridership", title, ["annual_fleet"])


def generate_figures(tables: dict[str, pd.DataFrame], output_dir: Path) -> list[dict[str, Any]]:
    """Save seven research figures and return the corresponding figure manifest.

    Only the destination directory is written. Inputs are copied before any
    display conversion. Output filenames and rendering settings are stable.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(STYLE):
        return [draw(tables, output_dir) for draw in (
            _monthly, _annual, _composition, _recovery, _market_share,
            _seasonality, _fleet,
        )]
