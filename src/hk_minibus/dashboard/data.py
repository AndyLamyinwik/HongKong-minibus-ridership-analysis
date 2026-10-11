"""Read and verify the existing analytical artifacts without modifying them."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


MODES = ("GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS")
SHARE_MODES = ("GMB", "RMB", "MTR", "FRANCHISED_BUS")
FLEET_MODES = ("GMB", "RMB")
YEARS = tuple(range(2015, 2026))
MONTHS = pd.date_range("2015-01-01", "2025-12-01", freq="MS")
SEGMENTS = {
    "pre_pandemic": (2015, 2019),
    "2019_to_2022": (2019, 2022),
    "2022_to_2025": (2022, 2025),
    "2023_to_2025": (2023, 2025),
    "2015_to_2025": (2015, 2025),
}


class DataLoadError(ValueError):
    """An existing dashboard input is unavailable or fails its data contract."""


@dataclass(frozen=True)
class DashboardData:
    """Verified local tables and preserved snapshot provenance."""

    tables: dict[str, pd.DataFrame]
    metadata: dict

    def table(self, name: str) -> pd.DataFrame:
        """Give callers a copy so display transformations cannot alter inputs."""
        return self.tables[name].copy(deep=True)


@dataclass(frozen=True)
class _Spec:
    date_key: str | None
    modes: tuple[str, ...]
    numeric: tuple[str, ...]
    qualified: bool = False


_SPECS = {
    "monthly_ridership": _Spec("month", MODES, (
        "passenger_journeys_thousands", "average_daily_journeys_thousands",
        "year", "calendar_month", "calendar_days"), True),
    "annual_ridership": _Spec("year", MODES, ("passenger_journeys_thousands",), True),
    "endpoint_comparison": _Spec(None, MODES, (
        "journeys_2015_thousands", "journeys_2019_thousands", "journeys_2025_thousands",
        "absolute_change_2015_2025_thousands", "change_2015_2025_pct",
        "recovery_2025_vs_2019_pct", "baseline_2015_2018_mean_annual_thousands",
        "recovery_2025_vs_2015_2018_mean_pct"), True),
    "recovery_2019": _Spec(None, MODES, (
        "baseline_2019_journeys_thousands", "journeys_2025_thousands",
        "absolute_change_thousands", "recovery_pct", "change_pct"), True),
    "annual_recovery": _Spec("year", MODES, (
        "passenger_journeys_thousands", "baseline_2019_journeys_thousands", "recovery_pct")),
    "monthly_market_share": _Spec("month", SHARE_MODES, (
        "passenger_journeys_thousands", "comparison_group_journeys_thousands", "share_pct"), True),
    "annual_market_share": _Spec("year", SHARE_MODES, (
        "passenger_journeys_thousands", "comparison_group_journeys_thousands", "share_pct"), True),
    "annual_minibus_composition": _Spec("year", FLEET_MODES, (
        "passenger_journeys_thousands", "plb_journeys_thousands", "share_of_plb_pct")),
    "minibus_composition": _Spec("month", FLEET_MODES, (
        "passenger_journeys_thousands", "plb_journeys_thousands", "share_of_plb_pct")),
    "annual_fleet": _Spec("year", FLEET_MODES, (
        "mean_month_end_licensed_vehicles", "december_licensed_vehicles",
        "annual_passenger_journeys_thousands", "calendar_days", "licensed_vehicle_days_proxy",
        "day_weighted_month_end_licensed_vehicles", "average_daily_journeys_per_licensed_vehicle"), True),
    "fleet_normalized": _Spec("month", FLEET_MODES, (
        "average_daily_journeys_thousands", "licensed_vehicles",
        "average_daily_journeys_per_licensed_vehicle"), True),
    "trend_segments": _Spec("segment", MODES, (
        "start_year", "end_year", "start_journeys_thousands", "end_journeys_thousands",
        "absolute_change_thousands", "change_pct", "annual_increases", "annual_decreases",
        "annual_unchanged")),
}
TABLE_NAMES = tuple(_SPECS)


def _paths(root: Path) -> list[Path]:
    return [root / "analysis" / "outputs" / f"{name}.csv" for name in TABLE_NAMES] + [
        root / "analysis" / "outputs" / "analysis_summary.json",
        root / "config" / "sources.json",
    ]


def source_fingerprint(root: Path) -> tuple[tuple[str, int, int], ...]:
    """Cache key changes when any required analytical or provenance file changes."""
    root = Path(root)
    result = []
    for path in _paths(root):
        try:
            stat = path.stat()
            if not path.is_file():
                raise OSError("not a regular file")
        except OSError as exc:
            raise DataLoadError(f"Required historical input is unavailable: {path.relative_to(root)}") from exc
        result.append((path.relative_to(root).as_posix(), stat.st_size, stat.st_mtime_ns))
    return tuple(result)


def _json(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DataLoadError(f"Cannot read valid metadata from {path.name}.") from exc
    if not isinstance(result, dict):
        raise DataLoadError(f"Metadata in {path.name} must be a JSON object.")
    return result


def _assert_close(actual: Iterable, expected: Iterable, label: str, *, tolerance: float = 1e-7) -> None:
    if not np.allclose(np.asarray(actual, dtype=float), np.asarray(expected, dtype=float),
                       rtol=0, atol=tolerance, equal_nan=False):
        raise DataLoadError(f"Historical inputs disagree: {label}. Use a consistent validated analysis snapshot.")


def _validate_table(name: str, frame: pd.DataFrame, spec: _Spec) -> pd.DataFrame:
    required = {"mode", *spec.numeric}
    if spec.date_key:
        required.add(spec.date_key)
    if spec.qualified:
        required.update(("measurement_basis", "includes_estimates"))
    if name == "annual_ridership":
        required.update(("absolute_yoy_change_thousands", "yoy_change_pct"))
    if name in ("monthly_ridership", "annual_ridership"):
        required.update(("is_provisional", "is_revised"))
    if name == "monthly_ridership":
        required.add("unit")
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise DataLoadError(f"{name}.csv lacks required columns: {', '.join(missing)}.")
    for column in spec.numeric:
        try:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        except (ValueError, TypeError) as exc:
            raise DataLoadError(f"{name}.csv has invalid numbers in {column}.") from exc
        if not np.isfinite(frame[column].to_numpy(dtype=float)).all():
            raise DataLoadError(f"{name}.csv contains missing or nonfinite {column} values.")
    if spec.date_key == "month":
        try:
            frame["month"] = pd.to_datetime(frame["month"], format="%Y-%m-%d", errors="raise")
        except (ValueError, TypeError) as exc:
            raise DataLoadError(f"{name}.csv has invalid reference months.") from exc
        expected = {(month, mode) for month in MONTHS for mode in spec.modes}
    elif spec.date_key == "year":
        try:
            frame["year"] = pd.to_numeric(frame["year"], errors="raise")
        except (ValueError, TypeError) as exc:
            raise DataLoadError(f"{name}.csv has invalid years.") from exc
        expected = {(year, mode) for year in YEARS for mode in spec.modes}
    elif spec.date_key == "segment":
        expected = {(segment, mode) for segment in SEGMENTS for mode in spec.modes}
    else:
        expected = {(mode,) for mode in spec.modes}
    key = [spec.date_key, "mode"] if spec.date_key else ["mode"]
    keys = list(frame[key].itertuples(index=False, name=None))
    if len(keys) != len(set(keys)):
        raise DataLoadError(f"{name}.csv contains duplicate observation keys.")
    if set(keys) != expected:
        raise DataLoadError(f"{name}.csv does not contain the complete 2015–2025 mode coverage.")
    if spec.qualified:
        expected_basis = frame["mode"].map({"GMB": "reported", "RMB": "estimated", "PLB": "mixed",
                                           "MTR": "reported", "FRANCHISED_BUS": "reported"})
        expected_estimates = frame["mode"].isin(("RMB", "PLB")).astype(int)
        if not frame["measurement_basis"].eq(expected_basis).all() or not frame["includes_estimates"].eq(expected_estimates).all():
            raise DataLoadError(f"{name}.csv does not retain the documented RMB/PLB estimation qualifications.")
    if name in ("monthly_ridership", "annual_ridership"):
        for flag in ("is_provisional", "is_revised"):
            if not frame[flag].isin((0, 1)).all():
                raise DataLoadError(f"{name}.csv contains invalid {flag} status flags.")
    if name == "monthly_ridership" and not frame["unit"].eq("thousand_journeys").all():
        raise DataLoadError("Monthly passenger inputs must retain thousand_journeys units.")
    for column in spec.numeric:
        if "journeys" in column and "change" not in column and (frame[column] <= 0).any():
            raise DataLoadError(f"{name}.csv contains nonpositive passenger values in {column}.")
    return frame.sort_values(key).reset_index(drop=True)


def _validate_consistency(tables: dict[str, pd.DataFrame]) -> None:
    monthly = tables["monthly_ridership"]
    annual = tables["annual_ridership"]
    if not monthly["year"].eq(monthly["month"].dt.year).all() or not monthly["calendar_month"].eq(monthly["month"].dt.month).all():
        raise DataLoadError("Monthly calendar fields do not match their reference dates.")
    _assert_close(monthly["calendar_days"], monthly["month"].dt.days_in_month, "month lengths")
    _assert_close(monthly["average_daily_journeys_thousands"],
                  monthly["passenger_journeys_thousands"] / monthly["calendar_days"], "monthly daily rates")
    _assert_close(annual["passenger_journeys_thousands"],
                  monthly.groupby(["year", "mode"])["passenger_journeys_thousands"].sum().to_numpy(), "annual/monthly totals")
    prior = annual.groupby("mode")["passenger_journeys_thousands"].shift(1)
    for column, expected in (
        ("absolute_yoy_change_thousands", annual["passenger_journeys_thousands"] - prior),
        ("yoy_change_pct", 100 * (annual["passenger_journeys_thousands"] / prior - 1)),
    ):
        try:
            actual = pd.to_numeric(annual[column], errors="raise")
        except (ValueError, TypeError) as exc:
            raise DataLoadError(f"Annual growth field {column} contains invalid numbers.") from exc
        if not actual.isna().eq(expected.isna()).all():
            raise DataLoadError("Annual growth must be missing only for the first in-window year.")
        _assert_close(actual[expected.notna()], expected[expected.notna()], column,
                      tolerance=1e-9 if column.endswith("pct") else 1e-7)
    for frame, key in ((monthly, "month"), (annual, "year")):
        wide = frame.pivot(index=key, columns="mode", values="passenger_journeys_thousands")
        _assert_close(wide["PLB"], wide["GMB"] + wide["RMB"], f"{key} PLB = GMB + RMB")
        for name in ("monthly_market_share", "minibus_composition") if key == "month" else ("annual_market_share", "annual_minibus_composition"):
            derived = tables[name]
            values = derived.merge(frame[[key, "mode", "passenger_journeys_thousands"]],
                                   on=[key, "mode"], suffixes=("", "_source"), validate="one_to_one")
            _assert_close(values["passenger_journeys_thousands"], values["passenger_journeys_thousands_source"], f"{name} numerators")
            if "share_pct" in derived:
                denominator = wide[list(SHARE_MODES)].sum(axis=1)
                expected_denominator = derived[key].map(denominator)
                percentage, denom_col = "share_pct", "comparison_group_journeys_thousands"
            else:
                expected_denominator = derived[key].map(wide["PLB"])
                percentage, denom_col = "share_of_plb_pct", "plb_journeys_thousands"
            _assert_close(derived[denom_col], expected_denominator, f"{name} denominator")
            _assert_close(derived[percentage], 100 * derived["passenger_journeys_thousands"] / derived[denom_col], f"{name} ratio", tolerance=1e-9)
            _assert_close(derived.groupby(key)[percentage].sum(), np.full(len(wide), 100), f"{name} shares sum to 100", tolerance=1e-9)
    lookup = annual.set_index(["year", "mode"])["passenger_journeys_thousands"]
    endpoints = tables["endpoint_comparison"]
    recovery = tables["recovery_2019"]
    for year in (2015, 2019, 2025):
        expected = endpoints["mode"].map(lookup.loc[year])
        _assert_close(endpoints[f"journeys_{year}_thousands"], expected, f"{year} endpoint totals")
    _assert_close(endpoints["absolute_change_2015_2025_thousands"], endpoints["journeys_2025_thousands"] - endpoints["journeys_2015_thousands"], "endpoint absolute change")
    _assert_close(endpoints["change_2015_2025_pct"], 100 * (endpoints["journeys_2025_thousands"] / endpoints["journeys_2015_thousands"] - 1), "endpoint percentage change", tolerance=1e-9)
    _assert_close(endpoints["recovery_2025_vs_2019_pct"], 100 * endpoints["journeys_2025_thousands"] / endpoints["journeys_2019_thousands"], "endpoint recovery", tolerance=1e-9)
    early_mean = annual[annual["year"].between(2015, 2018)].groupby("mode")["passenger_journeys_thousands"].mean()
    _assert_close(endpoints["baseline_2015_2018_mean_annual_thousands"], endpoints["mode"].map(early_mean), "alternative baseline")
    _assert_close(endpoints["recovery_2025_vs_2015_2018_mean_pct"], 100 * endpoints["journeys_2025_thousands"] / endpoints["baseline_2015_2018_mean_annual_thousands"], "alternative recovery", tolerance=1e-9)
    _assert_close(recovery["baseline_2019_journeys_thousands"], recovery["mode"].map(lookup.loc[2019]), "recovery baseline")
    _assert_close(recovery["journeys_2025_thousands"], recovery["mode"].map(lookup.loc[2025]), "recovery endpoint")
    _assert_close(recovery["recovery_pct"], 100 * recovery["journeys_2025_thousands"] / recovery["baseline_2019_journeys_thousands"], "recovery ratio", tolerance=1e-9)
    _assert_close(recovery["change_pct"], recovery["recovery_pct"] - 100, "recovery change", tolerance=1e-9)
    _assert_close(recovery["absolute_change_thousands"], recovery["journeys_2025_thousands"] - recovery["baseline_2019_journeys_thousands"], "recovery absolute change")
    annual_recovery = tables["annual_recovery"]
    _assert_close(annual_recovery["passenger_journeys_thousands"], annual["passenger_journeys_thousands"], "annual recovery totals")
    _assert_close(annual_recovery["baseline_2019_journeys_thousands"], annual_recovery["mode"].map(lookup.loc[2019]), "annual recovery baseline")
    _assert_close(annual_recovery["recovery_pct"], 100 * annual_recovery["passenger_journeys_thousands"] / annual_recovery["baseline_2019_journeys_thousands"], "annual recovery ratio", tolerance=1e-9)
    fleet = tables["fleet_normalized"]
    daily_lookup = monthly.set_index(["month", "mode"])["average_daily_journeys_thousands"]
    fleet_keys = pd.MultiIndex.from_frame(fleet[["month", "mode"]])
    _assert_close(fleet["average_daily_journeys_thousands"], daily_lookup.reindex(fleet_keys), "fleet daily rates")
    if (fleet["licensed_vehicles"] <= 0).any() or not fleet["licensed_vehicles"].eq(fleet["licensed_vehicles"].round()).all():
        raise DataLoadError("Monthly fleet stocks must be positive whole vehicle counts.")
    _assert_close(fleet["average_daily_journeys_per_licensed_vehicle"], fleet["average_daily_journeys_thousands"] * 1000 / fleet["licensed_vehicles"], "monthly fleet indicator")
    annual_fleet = tables["annual_fleet"]
    fleet_calendar = fleet.assign(year=fleet["month"].dt.year, days=fleet["month"].dt.days_in_month)
    proxy = (fleet_calendar["licensed_vehicles"] * fleet_calendar["days"]).groupby([fleet_calendar["year"], fleet_calendar["mode"]]).sum()
    _assert_close(annual_fleet["licensed_vehicle_days_proxy"], proxy, "licensed vehicle-day denominator")
    _assert_close(annual_fleet["calendar_days"], pd.to_datetime(annual_fleet["year"].astype(str) + "-12-31").dt.dayofyear, "annual calendar days")
    _assert_close(annual_fleet["day_weighted_month_end_licensed_vehicles"], annual_fleet["licensed_vehicle_days_proxy"] / annual_fleet["calendar_days"], "weighted fleet stock")
    _assert_close(annual_fleet["mean_month_end_licensed_vehicles"], fleet_calendar.groupby(["year", "mode"])["licensed_vehicles"].mean(), "mean month-end fleet stock")
    _assert_close(annual_fleet["december_licensed_vehicles"], fleet_calendar[fleet_calendar["month"].dt.month.eq(12)]["licensed_vehicles"], "December fleet stock")
    _assert_close(annual_fleet["annual_passenger_journeys_thousands"], lookup.reindex(pd.MultiIndex.from_frame(annual_fleet[["year", "mode"]])), "fleet annual journeys")
    _assert_close(annual_fleet["average_daily_journeys_per_licensed_vehicle"], annual_fleet["annual_passenger_journeys_thousands"] * 1000 / annual_fleet["licensed_vehicle_days_proxy"], "annual fleet indicator")
    segments = tables["trend_segments"]
    _assert_close(segments["start_year"], segments["segment"].map({name: years[0] for name, years in SEGMENTS.items()}), "segment start years")
    _assert_close(segments["end_year"], segments["segment"].map({name: years[1] for name, years in SEGMENTS.items()}), "segment end years")
    for direction in ("start", "end"):
        keys = pd.MultiIndex.from_frame(segments[[f"{direction}_year", "mode"]])
        _assert_close(segments[f"{direction}_journeys_thousands"], lookup.reindex(keys), f"segment {direction} totals")
    _assert_close(segments["absolute_change_thousands"], segments["end_journeys_thousands"] - segments["start_journeys_thousands"], "segment absolute change")
    _assert_close(segments["change_pct"], 100 * (segments["end_journeys_thousands"] / segments["start_journeys_thousands"] - 1), "segment percentage change", tolerance=1e-9)
    for row in segments.itertuples(index=False):
        changes = annual[annual["mode"].eq(row.mode) & annual["year"].between(row.start_year, row.end_year)]["passenger_journeys_thousands"].diff().dropna()
        if (row.annual_increases, row.annual_decreases, row.annual_unchanged) != (
            int(changes.gt(0).sum()), int(changes.lt(0).sum()), int(changes.eq(0).sum())
        ):
            raise DataLoadError("Trend-segment transition counts disagree with their annual records.")


def load_dashboard_data(root: Path) -> DashboardData:
    """Load complete existing Phase 3 tables, enforcing their documented meanings."""
    root = Path(root)
    source_fingerprint(root)
    summary = _json(root / "analysis" / "outputs" / "analysis_summary.json")
    sources = _json(root / "config" / "sources.json")
    check_counts = summary.get("check_counts")
    if not isinstance(check_counts, dict) or summary.get("status") not in ("passed", "passed_with_warnings") or check_counts.get("fail") != 0:
        raise DataLoadError("The historical analysis summary does not record a successful validated run.")
    checks = summary.get("checks")
    if not isinstance(checks, list) or not checks or any(
        not isinstance(check, dict) or check.get("status") not in ("pass", "warning")
        for check in checks
    ) or any(check_counts.get(status) != sum(check["status"] == status for check in checks)
             for status in ("pass", "warning")):
        raise DataLoadError("The analysis summary's check records and reported counts disagree.")
    if summary.get("scope") != {"start_month": "2015-01-01", "end_month": "2025-12-01", "months": 132}:
        raise DataLoadError("The historical analysis scope must cover all 132 months from 2015 through 2025.")
    if summary.get("comparison_group") != list(SHARE_MODES):
        raise DataLoadError("The validated comparison group must contain GMB, RMB, MTR and franchised buses once each.")
    required_metadata = ("snapshot_retrieved_on", "expected_revision_date", "publisher", "terms_url", "files")
    if any(not sources.get(key) for key in required_metadata):
        raise DataLoadError("The source manifest lacks required snapshot provenance.")
    try:
        date.fromisoformat(sources["snapshot_retrieved_on"])
        date.fromisoformat(sources["expected_revision_date"])
    except (TypeError, ValueError) as exc:
        raise DataLoadError("The source manifest has invalid retrieval or revision dates.") from exc
    if not isinstance(sources["publisher"], str) or not isinstance(sources["terms_url"], str) or not isinstance(sources["files"], list):
        raise DataLoadError("The source manifest contains malformed provenance fields.")
    record_counts = summary.get("record_counts")
    if not isinstance(record_counts, dict):
        raise DataLoadError("The analysis summary lacks its validated table row counts.")
    tables = {}
    for name, spec in _SPECS.items():
        path = root / "analysis" / "outputs" / f"{name}.csv"
        try:
            frame = pd.read_csv(path)
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            raise DataLoadError(f"Cannot read historical table {name}.csv.") from exc
        tables[name] = _validate_table(name, frame, spec)
        if record_counts.get(name) != len(frame):
            raise DataLoadError(f"{name}.csv does not match the validated analysis row count.")
    _validate_consistency(tables)
    metadata = {
        **sources,
        "sources": sources,
        "analysis_summary": summary,
        "retrieved_on": sources["snapshot_retrieved_on"],
        "revision_date": sources["expected_revision_date"],
        "publisher": sources["publisher"],
        "terms_url": sources["terms_url"],
        "scope": summary["scope"],
        "comparison_group": summary["comparison_group"],
    }
    return DashboardData(tables=tables, metadata=metadata)
