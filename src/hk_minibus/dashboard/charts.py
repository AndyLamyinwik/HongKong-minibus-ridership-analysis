"""Plotly presentation functions for the preserved Phase 3 analytical tables.

Functions never recompute research aggregates or alter their input frames. Indexed
``value`` columns are supplied by the display-metrics layer before filtering.
"""

from __future__ import annotations

import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go


MODE_ORDER = ("GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS")
MODE_NAMES = {
    "GMB": "GMB",
    "RMB": "RMB (estimated)",
    "PLB": "PLB (includes estimates)",
    "MTR": "MTR railway",
    "FRANCHISED_BUS": "Franchised buses",
}
MODE_COLORS = {
    "GMB": "#00796B",
    "RMB": "#BD4551",
    "PLB": "#263746",
    "MTR": "#087EA4",
    "FRANCHISED_BUS": "#B56A19",
}
MODE_DASHES = {
    "GMB": "solid", "RMB": "dash", "PLB": "dot",
    "MTR": "solid", "FRANCHISED_BUS": "dashdot",
}
MODE_SYMBOLS = {
    "GMB": "circle", "RMB": "diamond", "PLB": "square",
    "MTR": "triangle-up", "FRANCHISED_BUS": "cross",
}


def _base(title: str, *, y_title: str = "", height: int = 520) -> go.Figure:
    # Plotly titles do not automatically wrap when the container narrows.
    title_lines = title.split("<br>") if "<br>" in title else textwrap.wrap(
        title, width=32, break_long_words=False, break_on_hyphens=False,
    )
    extra_title_space = 20 * max(0, len(title_lines) - 1)
    figure = go.Figure()
    figure.update_layout(
        template="plotly_white", title={"text": "<br>".join(title_lines), "font": {"size": 17}, "x": 0},
        font={"family": "Arial, sans-serif", "size": 13, "color": "#263746"},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF", height=height + extra_title_space,
        # Rotated annual ticks plus their axis title need about 80px on mobile.
        # The separate legend area also accommodates several wrapped rows.
        margin={"l": 20, "r": 28, "t": 62 + extra_title_space, "b": 200},
        hovermode="x unified", hoverlabel={"bgcolor": "#FFFFFF", "font_size": 13},
        legend={"orientation": "h", "x": 0, "y": -0.40, "xanchor": "left", "yanchor": "top",
                "font": {"size": 11}, "maxheight": 80},
        yaxis={"title": y_title, "rangemode": "tozero", "gridcolor": "#E4E9EF", "zerolinecolor": "#CCD5DF"},
        xaxis={"showgrid": False, "zeroline": False},
    )
    return figure


def _empty(figure: go.Figure) -> go.Figure:
    figure.add_annotation(
        text="No observations for this selection", x=0.5, y=0.5,
        xref="paper", yref="paper", showarrow=False,
        font={"size": 16, "color": "#526579"},
    )
    return figure


def _require(frame: pd.DataFrame, columns: list[str], *, allowed=MODE_ORDER) -> None:
    absent = sorted(set(columns) - set(frame.columns))
    if absent:
        raise ValueError("Chart input is missing columns: " + ", ".join(absent))
    if frame.empty:
        return
    if frame[columns].isna().any().any():
        raise ValueError("Chart input contains missing values in required fields")
    invalid_modes = set(frame["mode"]) - set(allowed)
    if invalid_modes:
        raise ValueError("Unsupported modes for this chart: " + ", ".join(sorted(invalid_modes)))


def _numeric(frame: pd.DataFrame, columns: list[str], *, percentage: bool = False) -> None:
    for column in columns:
        try:
            values = pd.to_numeric(frame[column], errors="raise").to_numpy(dtype=float)
        except (ValueError, TypeError) as error:
            raise ValueError(f"Chart input {column} must be numeric") from error
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"Chart input {column} must contain finite nonnegative values")
        if percentage and (values > 100 + 1e-8).any():
            raise ValueError(f"Chart input {column} exceeds a 100% share")


def _time_frame(frame: pd.DataFrame, frequency: str, value: str, *, allowed=MODE_ORDER) -> tuple[pd.DataFrame, str]:
    if frequency not in {"Annual", "Monthly"}:
        raise ValueError("Frequency must be Annual or Monthly")
    time_column = "year" if frequency == "Annual" else "month"
    _require(frame, [time_column, "mode", value], allowed=allowed)
    _numeric(frame, [value])
    result = frame.copy(deep=True)
    if result.empty:
        return result, time_column
    if frequency == "Monthly":
        result[time_column] = pd.to_datetime(result[time_column], errors="raise")
    else:
        year_values = pd.to_numeric(result[time_column], errors="raise")
        if (year_values != year_values.astype(int)).any():
            raise ValueError("Annual chart years must be integers")
        result[time_column] = year_values.astype(int)
    if result.duplicated([time_column, "mode"]).any():
        raise ValueError("Chart input contains duplicate time/mode observations")
    return result.sort_values([time_column, "mode"]), time_column


def _time_axis(figure: go.Figure, frame: pd.DataFrame, time_column: str) -> None:
    if time_column == "year":
        figure.update_xaxes(title="Year", dtick=1, tickformat="d")
    else:
        figure.update_xaxes(title="Month", tickformat="%b %Y", hoverformat="%b %Y")


def _disruption_shading(figure: go.Figure, frame: pd.DataFrame, time_column: str) -> None:
    if frame.empty:
        return
    if time_column == "year":
        lower = max(int(frame[time_column].min()), 2020)
        upper = min(int(frame[time_column].max()), 2022)
    else:
        lower = max(frame[time_column].min(), pd.Timestamp("2020-01-01"))
        upper = min(frame[time_column].max(), pd.Timestamp("2022-12-31"))
    if lower >= upper:
        return
    figure.add_vrect(x0=lower, x1=upper, fillcolor="#DBE3EC", opacity=0.32, line_width=0, layer="below")
    figure.add_annotation(
        text="2020–2022 disruption period", x=upper, xref="x", y=1.03, yref="paper",
        showarrow=False, xanchor="right", font={"size": 11, "color": "#526579"},
    )


def _lines(figure: go.Figure, frame: pd.DataFrame, time_column: str, value: str, unit: str) -> None:
    annual = time_column == "year"
    for mode in MODE_ORDER:
        selected = frame.loc[frame["mode"].eq(mode)].sort_values(time_column)
        if selected.empty:
            continue
        figure.add_trace(go.Scatter(
            x=selected[time_column].tolist(), y=selected[value].tolist(),
            name=MODE_NAMES[mode], legendgroup=mode,
            mode="lines+markers" if annual or len(selected) == 1 else "lines",
            line={"color": MODE_COLORS[mode], "width": 3, "dash": MODE_DASHES[mode]},
            marker={"symbol": MODE_SYMBOLS[mode], "size": 7},
            connectgaps=False,
            hovertemplate=f"{MODE_NAMES[mode]}: %{{y:,.2f}} {unit}<extra></extra>",
        ))


def series_chart(
    frame: pd.DataFrame, frequency: str = "Annual", title: str = "", unit: str = "", indexed: bool = False,
) -> go.Figure:
    """Render prepared ``value`` values; normalization is never done after filters."""
    prepared, time_column = _time_frame(frame, frequency, "value")
    figure = _base(title, y_title=unit)
    _time_axis(figure, prepared, time_column)
    if prepared.empty:
        return _empty(figure)
    _lines(figure, prepared, time_column, "value", "index points" if indexed else unit)
    _disruption_shading(figure, prepared, time_column)
    if indexed:
        figure.add_hline(y=100, line_color="#8A98A8", line_dash="dot", line_width=1)
    return figure


def trend_chart(
    frame: pd.DataFrame, frequency: str = "Annual", indexed: bool = False, title: str = "Passenger journeys",
) -> go.Figure:
    """Chart millions of journeys or a prepared index with its fixed 2015 baseline."""
    if indexed:
        unit = "Index (2015 = 100)" if frequency == "Annual" else "Daily-rate index<br>(same month in 2015 = 100)"
    else:
        unit = "Million journeys / year" if frequency == "Annual" else "Million journeys / month"
    return series_chart(frame, frequency=frequency, title=title, unit=unit, indexed=indexed)


def recovery_bar(frame: pd.DataFrame) -> go.Figure:
    """2025 annual recovery; 100 is a benchmark, not an upper axis limit."""
    _require(frame, ["mode", "recovery_pct"])
    _numeric(frame, ["recovery_pct"])
    figure = _base("Recovery in 2025 (2019 = 100%)", height=430)
    figure.update_layout(hovermode="closest", showlegend=False,
                          xaxis={"title": "2025 / 2019 annual journeys (%)", "rangemode": "tozero", "gridcolor": "#E4E9EF"},
                          yaxis={"title": "", "autorange": "reversed"}, margin={"l": 20, "r": 60, "t": 65, "b": 50})
    if frame.empty:
        return _empty(figure)
    if frame.duplicated("mode").any():
        raise ValueError("Recovery chart requires one observation per mode")
    ordered = frame.set_index("mode").reindex([mode for mode in MODE_ORDER if mode in set(frame["mode"])]).reset_index()
    modes = ordered["mode"].tolist()
    figure.add_trace(go.Bar(
        x=ordered.recovery_pct.tolist(), y=[MODE_NAMES[mode] for mode in modes], orientation="h",
        marker_color=[MODE_COLORS[mode] for mode in modes], text=[f"{value:.2f}%" for value in ordered.recovery_pct],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>2025 / 2019: %{x:.2f}%<extra></extra>",
    ))
    upper = max(110.0, float(ordered.recovery_pct.max()) * 1.15)
    figure.update_xaxes(range=[0, upper], ticksuffix="%")
    figure.add_vline(x=100, line_color="#526579", line_dash="dash", line_width=1.5)
    figure.add_annotation(x=100, y=1.06, xref="x", yref="paper", text="2019 = 100%", showarrow=False, font={"size": 11})
    return figure


def baseline_comparison_chart(frame: pd.DataFrame) -> go.Figure:
    """Paired annual totals in millions, keeping the five distinct series separate."""
    columns = ["baseline_2019_journeys_thousands", "journeys_2025_thousands"]
    _require(frame, ["mode", *columns])
    _numeric(frame, columns)
    figure = _base("Annual journeys: 2019 and 2025", height=460)
    figure.update_layout(hovermode="closest", barmode="group",
                          xaxis={"title": "Million journeys / year", "rangemode": "tozero", "gridcolor": "#E4E9EF"},
                          yaxis={"title": "", "autorange": "reversed"})
    if frame.empty:
        return _empty(figure)
    if frame.duplicated("mode").any():
        raise ValueError("Baseline comparison requires one observation per mode")
    selected = frame.set_index("mode").reindex([mode for mode in MODE_ORDER if mode in set(frame["mode"])]).reset_index()
    names = [MODE_NAMES[mode] for mode in selected["mode"]]
    for year, column, color, pattern in [(2019, columns[0], "#91A1B3", "/"), (2025, columns[1], "#263746", "")]:
        values = (selected[column] / 1000).tolist()
        figure.add_trace(go.Bar(
            x=values, y=names, name=str(year), orientation="h", marker={"color": color, "pattern": {"shape": pattern}},
            text=[f"{value:,.1f}" for value in values], textposition="auto",
            hovertemplate=f"%{{y}}<br>{year}: %{{x:,.3f}} million journeys<extra></extra>",
        ))
    return figure


def recovery_trend_chart(frame: pd.DataFrame) -> go.Figure:
    prepared, time_column = _time_frame(frame, "Annual", "recovery_pct")
    figure = _base("Annual recovery (2019 = 100%)", y_title="Annual journeys / 2019 journeys (%)")
    _time_axis(figure, prepared, time_column)
    if prepared.empty:
        return _empty(figure)
    _lines(figure, prepared, time_column, "recovery_pct", "% of 2019")
    _disruption_shading(figure, prepared, time_column)
    figure.add_hline(y=100, line_color="#8A98A8", line_dash="dash", line_width=1.5)
    figure.update_yaxes(ticksuffix="%")
    return figure


def _shares(
    frame: pd.DataFrame, frequency: str, column: str, title: str, allowed: tuple[str, ...], style: str,
) -> go.Figure:
    if style not in {"Area", "Lines"}:
        raise ValueError("Share style must be Area or Lines")
    prepared, time_column = _time_frame(frame, frequency, column, allowed=allowed)
    _numeric(prepared, [column], percentage=True)
    figure = _base(title, y_title="Share (%)")
    figure.update_yaxes(range=[0, 100], ticksuffix="%")
    _time_axis(figure, prepared, time_column)
    if prepared.empty:
        return _empty(figure)
    if style == "Lines":
        _lines(figure, prepared, time_column, column, "%")
    elif prepared[time_column].nunique() == 1:
        # A filled area has no width at one time point. A stacked bar keeps that
        # selection visible and retains each component's original denominator.
        figure.update_layout(barmode="stack")
        for mode in MODE_ORDER:
            selected = prepared.loc[prepared["mode"].eq(mode)]
            if selected.empty:
                continue
            figure.add_trace(go.Bar(
                x=selected[time_column].tolist(), y=selected[column].tolist(),
                name=MODE_NAMES[mode], legendgroup=mode,
                marker={"color": MODE_COLORS[mode]},
                width=0.65 if time_column == "year" else 20 * 24 * 60 * 60 * 1000,
                text=[f"{value:.2f}%" for value in selected[column]], textposition="auto",
                hovertemplate=f"{MODE_NAMES[mode]}: %{{y:.2f}}%<extra></extra>",
            ))
    else:
        for mode in MODE_ORDER:
            selected = prepared.loc[prepared["mode"].eq(mode)].sort_values(time_column)
            if selected.empty:
                continue
            figure.add_trace(go.Scatter(
                x=selected[time_column].tolist(), y=selected[column].tolist(),
                mode="lines", name=MODE_NAMES[mode], legendgroup=mode,
                line={"color": MODE_COLORS[mode], "width": 1.5, "dash": MODE_DASHES[mode]},
                stackgroup="preserved_shares", connectgaps=False,
                hovertemplate=f"{MODE_NAMES[mode]}: %{{y:.2f}}%<extra></extra>",
            ))
    return figure


def share_chart(frame: pd.DataFrame, frequency: str = "Annual", style: str = "Area") -> go.Figure:
    """Use stored four-mode shares, without PLB double counting or renormalization."""
    return _shares(frame, frequency, "share_pct", "Share within selected public transport modes",
                   ("GMB", "RMB", "MTR", "FRANCHISED_BUS"), style)


def composition_chart(frame: pd.DataFrame, frequency: str = "Annual") -> go.Figure:
    return _shares(frame, frequency, "share_of_plb_pct", "Composition of public light bus journeys",
                   ("GMB", "RMB"), "Area")


def fleet_chart(
    frame: pd.DataFrame, frequency: str = "Monthly", metric: str = "Licensed fleet", indexed: bool = False,
) -> go.Figure:
    """Render fleet source columns, or already indexed ``value`` from display metrics.

    Annual licensed stock means December stock. The annual journey indicator is
    the Phase 3 vehicle-days-weighted proxy, never a mean of monthly ratios.
    """
    if metric not in {"Licensed fleet", "Journeys per licensed vehicle-day proxy"}:
        raise ValueError("Unsupported fleet metric")
    _require(frame, ["mode"], allowed=("GMB", "RMB"))
    if indexed:
        if frequency != "Annual":
            raise ValueError("Indexed fleet charts require an annual series")
        return series_chart(frame, frequency, f"{metric}, 2015 = 100", "Index (2015 = 100)", indexed=True)
    if metric == "Licensed fleet":
        column = "december_licensed_vehicles" if frequency == "Annual" else "licensed_vehicles"
        title = "Licensed fleet at December month-end" if frequency == "Annual" else "Licensed fleet at month-end"
        unit = "Licensed vehicles"
    else:
        column = "average_daily_journeys_per_licensed_vehicle"
        title = "Journeys relative to licensed fleet"
        unit = "Journeys / licensed vehicle-day proxy"
    _require(frame, ["mode", column], allowed=("GMB", "RMB"))
    prepared = frame.copy(deep=True)
    prepared["value"] = prepared[column]
    return series_chart(prepared, frequency, title, unit)
