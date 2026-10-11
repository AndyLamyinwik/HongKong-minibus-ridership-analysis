"""Descriptive historical calculations, independent of the SQL queries.

All passenger totals remain in thousands unless a field explicitly says
journeys per licensed vehicle. No source measurement is changed here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COMPARISON_MODES = ("GMB", "RMB", "MTR", "FRANCHISED_BUS")
ALL_MODES = (*COMPARISON_MODES, "PLB")
PERIODS = {"pre_pandemic": (2015, 2019), "pandemic_disruption": (2020, 2022), "post_pandemic": (2023, 2025)}


def safe_ratio(numerator, denominator, scale=100.0):
    """Undefined denominators remain missing rather than becoming zero."""
    return numerator / denominator.replace(0, np.nan) * scale


def _period(year: pd.Series) -> pd.Series:
    return pd.Series(np.select([year.le(2019), year.le(2022)], ["pre_pandemic", "pandemic_disruption"], default="post_pandemic"), index=year.index)


def _shares(frame: pd.DataFrame, key: str) -> pd.DataFrame:
    selected = frame.loc[frame["mode"].isin(COMPARISON_MODES)].copy()
    selected["comparison_group_journeys_thousands"] = selected.groupby(key)["passenger_journeys_thousands"].transform("sum")
    selected["share_pct"] = safe_ratio(selected["passenger_journeys_thousands"], selected["comparison_group_journeys_thousands"])
    return selected[[key, "mode", "passenger_journeys_thousands", "comparison_group_journeys_thousands", "share_pct", "measurement_basis", "includes_estimates"]].sort_values([key, "mode"]).reset_index(drop=True)


def compute_tables(passengers: pd.DataFrame, daily: pd.DataFrame, fleet: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Compute annual, benchmark, share, seasonal and fleet summaries.

    The caller validates complete monthly inputs before invoking this function.
    Period comparison uses mean annual totals and day-weighted daily rates,
    avoiding comparisons of five-year totals with three-year totals.
    """
    monthly = passengers.sort_values(["month", "mode"]).reset_index(drop=True).copy()
    monthly = monthly.merge(daily[["month", "mode", "average_daily_journeys_thousands"]], on=["month", "mode"], validate="one_to_one")
    dates = pd.to_datetime(monthly["month"])
    monthly["year"] = dates.dt.year
    monthly["calendar_month"] = dates.dt.month
    monthly["calendar_days"] = dates.dt.days_in_month
    monthly["period"] = _period(monthly["year"])
    monthly["prior_year_journeys_thousands"] = monthly.groupby("mode")["passenger_journeys_thousands"].shift(12)
    monthly["absolute_yoy_change_thousands"] = monthly["passenger_journeys_thousands"] - monthly["prior_year_journeys_thousands"]
    monthly["yoy_change_pct"] = safe_ratio(monthly["absolute_yoy_change_thousands"], monthly["prior_year_journeys_thousands"])
    monthly_yoy = monthly[["month", "mode", "passenger_journeys_thousands", "prior_year_journeys_thousands", "absolute_yoy_change_thousands", "yoy_change_pct"]].copy()

    annual = monthly.groupby(["year", "mode"], as_index=False).agg(
        passenger_journeys_thousands=("passenger_journeys_thousands", "sum"),
        measurement_basis=("measurement_basis", "first"), includes_estimates=("includes_estimates", "max"),
        is_provisional=("is_provisional", "max"), is_revised=("is_revised", "max"))
    prior = annual.groupby("mode")["passenger_journeys_thousands"].shift(1)
    annual["absolute_yoy_change_thousands"] = annual["passenger_journeys_thousands"] - prior
    annual["yoy_change_pct"] = safe_ratio(annual["absolute_yoy_change_thousands"], prior)
    annual = annual[["year", "mode", "passenger_journeys_thousands", "absolute_yoy_change_thousands", "yoy_change_pct", "measurement_basis", "includes_estimates", "is_provisional", "is_revised"]]
    annual_daily = monthly.groupby(["year", "mode"], as_index=False).agg(total=("passenger_journeys_thousands", "sum"), days=("calendar_days", "sum"))
    annual_daily["annual_average_daily_journeys_thousands"] = annual_daily["total"] / annual_daily["days"]
    monthly = monthly.merge(annual_daily[["year", "mode", "annual_average_daily_journeys_thousands"]], on=["year", "mode"], validate="many_to_one")
    monthly["within_year_daily_index"] = safe_ratio(monthly["average_daily_journeys_thousands"], monthly["annual_average_daily_journeys_thousands"])
    baseline_months = monthly.loc[monthly["year"].eq(2019), ["calendar_month", "mode", "average_daily_journeys_thousands"]].rename(columns={"average_daily_journeys_thousands": "baseline_2019_same_month_daily_thousands"})
    monthly = monthly.merge(baseline_months, on=["calendar_month", "mode"], validate="many_to_one")
    monthly["same_month_2019_daily_recovery_pct"] = safe_ratio(monthly["average_daily_journeys_thousands"], monthly["baseline_2019_same_month_daily_thousands"])
    monthly = monthly.sort_values(["month", "mode"]).reset_index(drop=True)

    annual_shares, monthly_shares = _shares(annual, "year"), _shares(monthly, "month")
    baseline = annual.loc[annual["year"].eq(2019), ["mode", "passenger_journeys_thousands"]].rename(columns={"passenger_journeys_thousands": "baseline_2019_journeys_thousands"})
    annual_recovery = annual[["year", "mode", "passenger_journeys_thousands"]].merge(baseline, on="mode", validate="many_to_one")
    annual_recovery["recovery_pct"] = safe_ratio(annual_recovery["passenger_journeys_thousands"], annual_recovery["baseline_2019_journeys_thousands"])
    recovery = annual_recovery.loc[annual_recovery["year"].eq(2025)].drop(columns="year").rename(columns={"passenger_journeys_thousands": "journeys_2025_thousands"})
    recovery["absolute_change_thousands"] = recovery["journeys_2025_thousands"] - recovery["baseline_2019_journeys_thousands"]
    recovery["change_pct"] = recovery["recovery_pct"] - 100
    recovery = recovery.merge(annual.loc[annual["year"].eq(2025), ["mode", "measurement_basis", "includes_estimates"]], on="mode", validate="one_to_one")
    recovery = recovery[["mode", "baseline_2019_journeys_thousands", "journeys_2025_thousands", "absolute_change_thousands", "recovery_pct", "change_pct", "measurement_basis", "includes_estimates"]].sort_values("mode").reset_index(drop=True)

    def composition(frame, key):
        plb = frame.loc[frame["mode"].eq("PLB"), [key, "passenger_journeys_thousands"]].rename(columns={"passenger_journeys_thousands": "plb_journeys_thousands"})
        result = frame.loc[frame["mode"].isin(["GMB", "RMB"]), [key, "mode", "passenger_journeys_thousands"]].merge(plb, on=key, validate="many_to_one")
        result["share_of_plb_pct"] = safe_ratio(result["passenger_journeys_thousands"], result["plb_journeys_thousands"])
        return result.sort_values([key, "mode"]).reset_index(drop=True)

    periods = monthly.groupby(["period", "mode"], as_index=False).agg(
        years=("year", "nunique"), months=("month", "nunique"), calendar_days=("calendar_days", "sum"),
        total_passenger_journeys_thousands=("passenger_journeys_thousands", "sum"),
        measurement_basis=("measurement_basis", "first"), includes_estimates=("includes_estimates", "max"))
    periods["mean_annual_passenger_journeys_thousands"] = periods["total_passenger_journeys_thousands"] / periods["years"]
    periods["weighted_average_daily_journeys_thousands"] = periods["total_passenger_journeys_thousands"] / periods["calendar_days"]

    minima = []
    for mode, frame in monthly.groupby("mode"):
        for metric, unit in [("passenger_journeys_thousands", "thousand_journeys"), ("average_daily_journeys_thousands", "thousand_journeys_per_day")]:
            row = frame.loc[frame[metric].idxmin()]
            minima.append({"mode": mode, "metric": metric, "month": row["month"], "value": row[metric], "unit": unit, "same_month_2019_daily_recovery_pct": row["same_month_2019_daily_recovery_pct"], "measurement_basis": row["measurement_basis"]})

    seasonal = monthly.groupby(["period", "mode", "calendar_month"], as_index=False).agg(
        observations=("month", "size"), mean_passenger_journeys_thousands=("passenger_journeys_thousands", "mean"),
        mean_average_daily_journeys_thousands=("average_daily_journeys_thousands", "mean"),
        mean_within_year_daily_index=("within_year_daily_index", "mean"),
        population_sd_daily_thousands=("average_daily_journeys_thousands", lambda values: values.std(ddof=0)))
    seasonal["population_cv_daily_pct"] = safe_ratio(seasonal["population_sd_daily_thousands"], seasonal["mean_average_daily_journeys_thousands"])
    seasonal_ranges = []
    for (period, mode), frame in seasonal.groupby(["period", "mode"]):
        peak = frame.loc[frame["mean_within_year_daily_index"].idxmax()]
        trough = frame.loc[frame["mean_within_year_daily_index"].idxmin()]
        seasonal_ranges.append({"period": period, "mode": mode, "peak_calendar_month": int(peak["calendar_month"]), "trough_calendar_month": int(trough["calendar_month"]), "peak_daily_index": peak["mean_within_year_daily_index"], "trough_daily_index": trough["mean_within_year_daily_index"], "range_index_points": peak["mean_within_year_daily_index"] - trough["mean_within_year_daily_index"]})

    fleet_daily = daily[["month", "mode", "average_daily_journeys_thousands", "measurement_basis", "includes_estimates"]].merge(fleet[["month", "mode", "licensed_vehicles"]], on=["month", "mode"], validate="one_to_one")
    fleet_daily["average_daily_journeys_per_licensed_vehicle"] = safe_ratio(fleet_daily["average_daily_journeys_thousands"], fleet_daily["licensed_vehicles"], scale=1000)
    fleet_daily = fleet_daily[["month", "mode", "average_daily_journeys_thousands", "licensed_vehicles", "average_daily_journeys_per_licensed_vehicle", "measurement_basis", "includes_estimates"]].sort_values(["month", "mode"]).reset_index(drop=True)
    context = fleet_daily.merge(monthly[["month", "mode", "year", "calendar_days", "passenger_journeys_thousands"]], on=["month", "mode"], validate="one_to_one")
    context["licensed_vehicle_days_proxy"] = context["licensed_vehicles"] * context["calendar_days"]
    fleet_annual = context.groupby(["year", "mode"], as_index=False).agg(
        mean_month_end_licensed_vehicles=("licensed_vehicles", "mean"), december_licensed_vehicles=("licensed_vehicles", "last"),
        annual_passenger_journeys_thousands=("passenger_journeys_thousands", "sum"), calendar_days=("calendar_days", "sum"),
        licensed_vehicle_days_proxy=("licensed_vehicle_days_proxy", "sum"), measurement_basis=("measurement_basis", "first"), includes_estimates=("includes_estimates", "max"))
    fleet_annual["day_weighted_month_end_licensed_vehicles"] = fleet_annual["licensed_vehicle_days_proxy"] / fleet_annual["calendar_days"]
    fleet_annual["average_daily_journeys_per_licensed_vehicle"] = safe_ratio(fleet_annual["annual_passenger_journeys_thousands"], fleet_annual["licensed_vehicle_days_proxy"], scale=1000)

    endpoints = annual.pivot(index="mode", columns="year", values="passenger_journeys_thousands")
    endpoint = pd.DataFrame({"mode": endpoints.index, "journeys_2015_thousands": endpoints[2015].values, "journeys_2019_thousands": endpoints[2019].values, "journeys_2025_thousands": endpoints[2025].values})
    endpoint["absolute_change_2015_2025_thousands"] = endpoint["journeys_2025_thousands"] - endpoint["journeys_2015_thousands"]
    endpoint["change_2015_2025_pct"] = safe_ratio(endpoint["absolute_change_2015_2025_thousands"], endpoint["journeys_2015_thousands"])
    endpoint["recovery_2025_vs_2019_pct"] = safe_ratio(endpoint["journeys_2025_thousands"], endpoint["journeys_2019_thousands"])
    earlier = annual.loc[annual["year"].between(2015, 2018)].groupby("mode")["passenger_journeys_thousands"].mean()
    endpoint["baseline_2015_2018_mean_annual_thousands"] = endpoint["mode"].map(earlier)
    endpoint["recovery_2025_vs_2015_2018_mean_pct"] = safe_ratio(endpoint["journeys_2025_thousands"], endpoint["baseline_2015_2018_mean_annual_thousands"])
    endpoint = endpoint.merge(annual.loc[annual["year"].eq(2025), ["mode", "measurement_basis", "includes_estimates"]], on="mode", validate="one_to_one")

    segments, contributions = [], []
    for name, start, end in [("pre_pandemic", 2015, 2019), ("2019_to_2022", 2019, 2022), ("2022_to_2025", 2022, 2025), ("2023_to_2025", 2023, 2025), ("2015_to_2025", 2015, 2025)]:
        for mode in sorted(ALL_MODES):
            values = annual.loc[annual["mode"].eq(mode)].set_index("year")["passenger_journeys_thousands"]
            changes = values.loc[start:end].diff().dropna()
            change = values.loc[end] - values.loc[start]
            segments.append({"segment": name, "mode": mode, "start_year": start, "end_year": end, "start_journeys_thousands": values.loc[start], "end_journeys_thousands": values.loc[end], "absolute_change_thousands": change, "change_pct": change / values.loc[start] * 100, "annual_increases": int(changes.gt(0).sum()), "annual_decreases": int(changes.lt(0).sum()), "annual_unchanged": int(changes.eq(0).sum())})
            if mode in {"GMB", "RMB"}:
                total_change = endpoints.loc["PLB", end] - endpoints.loc["PLB", start]
                contributions.append({"segment": name, "mode": mode, "start_year": start, "end_year": end, "absolute_change_thousands": change, "plb_absolute_change_thousands": total_change, "contribution_to_plb_change_pct": change / total_change * 100 if total_change else np.nan})

    return {"monthly_ridership": monthly, "monthly_yoy": monthly_yoy, "annual_ridership": annual,
            "monthly_market_share": monthly_shares, "annual_market_share": annual_shares,
            "minibus_composition": composition(monthly, "month"), "annual_minibus_composition": composition(annual, "year"),
            "annual_recovery": annual_recovery, "recovery_2019": recovery, "period_summary": periods,
            "monthly_minima": pd.DataFrame(minima), "seasonality": seasonal, "seasonality_ranges": pd.DataFrame(seasonal_ranges),
            "fleet_normalized": fleet_daily, "annual_fleet": fleet_annual, "endpoint_comparison": endpoint,
            "trend_segments": pd.DataFrame(segments), "minibus_change_contributions": pd.DataFrame(contributions)}
