"""Structured diagnostics and checks independent of data preparation."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .config import DAILY_TOLERANCE_THOUSANDS, END_MONTH, MODE_LOOKUP, START_MONTH


class PreparationError(ValueError):
    """A source cannot be prepared without violating its contract."""


@dataclass
class ValidationReport:
    checks: list[dict[str, Any]] = field(default_factory=list)

    def add(self, check_id: str, condition: bool, message: str, details=None):
        self.checks.append({"check_id": check_id, "status": "pass" if condition else "fail", "severity": "error", "message": message, "details": details or {}})

    def warn(self, check_id: str, message: str, details=None):
        self.checks.append({"check_id": check_id, "status": "warning", "severity": "warning", "message": message, "details": details or {}})

    @property
    def failed(self) -> bool:
        return any(check["status"] == "fail" for check in self.checks)

    def require_success(self):
        if self.failed:
            failures = [check["check_id"] for check in self.checks if check["status"] == "fail"]
            raise PreparationError("Validation failed: " + ", ".join(failures))


def target_months() -> list[str]:
    return pd.date_range(START_MONTH, END_MONTH, freq="MS").strftime("%Y-%m-%d").tolist()


def validate_outputs(frames: dict[str, pd.DataFrame], report: ValidationReport):
    """Check grains, scope, metadata and values without repairing failures."""
    expected_months = set(target_months())
    for name, value_col, unit in [
        ("monthly_passenger_journeys", "passenger_journeys_thousands", "thousand_journeys"),
        ("monthly_average_daily_journeys", "average_daily_journeys_thousands", "thousand_journeys_per_day"),
    ]:
        frame = frames[name]
        expected_keys = {(month, mode) for month in expected_months for mode in MODE_LOOKUP}
        actual_keys = set(frame[["month", "mode"]].itertuples(index=False, name=None))
        report.add(f"{name}_coverage", len(frame) == 660 and actual_keys == expected_keys,
                   "Exactly 132 continuous months and five defined modes are required.",
                   {"rows": len(frame), "month_count": frame["month"].nunique(), "missing_keys": sorted(expected_keys - actual_keys)[:20], "unexpected_keys": sorted(actual_keys - expected_keys)[:20]})
        report.add(f"{name}_unique", not frame.duplicated(["month", "mode"]).any(), "Month/mode keys must be unique.")
        report.add(f"{name}_values", frame[value_col].notna().all() and frame[value_col].ge(0).all(), "Passenger values must be present and nonnegative; zeros are preserved if published.")
        report.add(f"{name}_units", frame["unit"].eq(unit).all(), "The measure uses one explicit compatible unit.", {"expected_unit": unit})
        bad_metadata = []
        for row in frame.itertuples(index=False):
            definition = MODE_LOOKUP[row.mode]
            if row.measurement_basis != definition["measurement_basis"] or row.includes_estimates != definition["includes_estimates"]:
                bad_metadata.append([row.month, row.mode])
            if row.is_provisional != int("#" in row.source_indicator) or row.is_revised != int("*" in row.source_indicator):
                bad_metadata.append([row.month, row.mode, "status_flags"])
        report.add(f"{name}_method_and_flags", not bad_metadata, "RMB estimates, mixed PLB values, and source status flags must be retained independently.", {"bad_rows": bad_metadata[:20]})
        source_name = "passenger_source_records" if value_col.startswith("passenger") else "daily_source_records"
        lineage_name = "passenger_lineage" if source_name.startswith("passenger") else "daily_lineage"
        source = frames[source_name].set_index("source_record_id")
        lineage = frames[lineage_name]
        differences = []
        missing_links = []
        propagation_errors = []
        for row in frame.itertuples(index=False):
            links = lineage.loc[(lineage["month"] == row.month) & (lineage["mode"] == row.mode), "source_record_id"]
            if len(links) != row.component_count or links.duplicated().any() or not links.isin(source.index).all():
                missing_links.append([row.month, row.mode])
                continue
            linked = source.loc[links]
            if not linked["month"].eq(row.month).all():
                missing_links.append([row.month, row.mode, "cross_month"])
            same_month = source[source["month"].eq(row.month)]
            if row.mode in {"GMB", "RMB"}:
                expected_links = same_month[same_month["operator_code"].eq(row.mode)].index
            elif row.mode == "PLB":
                expected_links = same_month[same_month["source_mode"].eq("PLB")].index
            elif row.mode == "MTR":
                expected_links = same_month[same_month["operator_code"].eq("MTRC")].index
            else:
                expected_links = same_month[same_month["source_mode"].eq("Fran_Bus")].index
            if set(links) != set(expected_links):
                missing_links.append([row.month, row.mode, "incompatible_component_set"])
            expected_indicator = "|".join(sorted({value for value in linked["source_indicator"] if value}))
            if row.source_indicator != expected_indicator:
                propagation_errors.append([row.month, row.mode])
            value = linked[value_col].sum(min_count=len(linked))
            if abs(float(value) - getattr(row, value_col)) > 1e-9:
                differences.append([row.month, row.mode, float(value), getattr(row, value_col)])
        report.add(f"{name}_lineage", not missing_links, "Every component must have an unambiguous source record in the same month.", {"bad_rows": missing_links[:20], "lineage_rows": len(lineage)})
        report.add(f"{name}_status_propagation", not propagation_errors, "Aggregate status text must retain every contributing source status token.", {"bad_rows": propagation_errors[:20]})
        report.add(f"{name}_source_values", not differences, "Every analytical value must equal its source components without rounding or adjustment.", {"mismatches": differences[:20]})
        plb = frame[frame["mode"] == "PLB"].set_index("month")[value_col]
        components = frame[frame["mode"].isin(["GMB", "RMB"])].groupby("month")[value_col].sum(min_count=2)
        report.add(f"{name}_plb_identity", ((plb - components).abs() <= 1e-9).all(), "PLB equals GMB plus RMB where both are available.")

    fleet = frames["monthly_minibus_fleet"]
    expected_keys = {(month, mode) for month in expected_months for mode in ["GMB", "RMB"]}
    actual_keys = set(fleet[["month", "mode"]].itertuples(index=False, name=None))
    report.add("fleet_coverage", len(fleet) == 264 and actual_keys == expected_keys, "Both minibus fleet series require every target month.", {"rows": len(fleet), "missing_keys": sorted(expected_keys - actual_keys)[:20]})
    report.add("fleet_unique", not fleet.duplicated(["month", "mode"]).any(), "Fleet month/mode keys must be unique.")
    report.add("fleet_counts", fleet[["licensed_vehicles", "passenger_capacity"]].notna().all().all() and fleet[["licensed_vehicles", "passenger_capacity"]].gt(0).all().all(), "Required fleet and capacity values are present positive integer counts.")
    report.add("fleet_units", fleet["fleet_unit"].eq("vehicles").all() and fleet["capacity_unit"].eq("passenger_places").all() and fleet["km_unit"].eq("thousand_vehicle_km").all(), "Fleet stocks, capacity and kilometres retain separate units.")
    report.add("fleet_basis", fleet["measurement_basis"].eq("reported").all(), "RMB licensed fleet is administrative data, independent of the RMB patronage estimate label.")
    report.add("fleet_structural_blanks", fleet.loc[fleet["mode"] == "RMB", "vehicle_km_thousands"].isna().all() and fleet["cross_harbour_vehicle_km_thousands"].isna().all(), "Unsupported minibus mileage observations remain null, never zero.")
    for numeric, token in [("licensed_vehicles", "source_fleet_text"), ("passenger_capacity", "source_capacity_text"), ("vehicle_km_thousands", "source_km_text"), ("cross_harbour_vehicle_km_thousands", "source_cross_harbour_km_text")]:
        original = pd.to_numeric(fleet[token].replace({"": None, "N.A.": None, "-": None}), errors="coerce")
        differences = (fleet[numeric].astype("Float64") - original.astype("Float64")).abs()
        same_nulls = fleet[numeric].isna().equals(original.isna())
        report.add(f"fleet_source_{numeric}", same_nulls and differences.dropna().le(1e-9).all(), "Fleet measure equals its retained source token, including nullness.")


def reconcile_daily(frames: dict[str, pd.DataFrame], report: ValidationReport) -> pd.DataFrame:
    """Compare contemporaneous monthly and daily CSVs with calendar days."""
    monthly = frames["passenger_source_records"]
    daily = frames["daily_source_records"]
    keys = ["month", "source_mode", "operator_code", "rail_category"]
    combined = monthly.groupby(keys, as_index=False)["passenger_journeys_thousands"].sum(min_count=1)
    reconciled = combined.merge(daily[keys + ["average_daily_journeys_thousands"]], on=keys, how="outer", validate="one_to_one", indicator=True)
    reconciled["days_in_month"] = pd.to_datetime(reconciled["month"]).dt.days_in_month
    reconciled["difference_thousands"] = reconciled["passenger_journeys_thousands"] - reconciled["average_daily_journeys_thousands"] * reconciled["days_in_month"]
    bad = reconciled[reconciled["_merge"].ne("both") | reconciled["difference_thousands"].isna() | reconciled["difference_thousands"].abs().gt(DAILY_TOLERANCE_THOUSANDS)]
    report.add("operator_monthly_daily_reconciliation", bad.empty, "Monthly totals agree with operator daily averages multiplied by actual calendar days; Citybus franchises are combined first.", {"comparisons": len(reconciled), "tolerance_thousands": DAILY_TOLERANCE_THOUSANDS, "max_absolute_difference_thousands": float(reconciled["difference_thousands"].abs().max()), "mismatches": bad.drop(columns="_merge").head(20).to_dict("records")})
    aggregate = frames["monthly_passenger_journeys"].merge(frames["monthly_average_daily_journeys"], on=["month", "mode"], suffixes=("_monthly", "_daily"), validate="one_to_one")
    difference = aggregate["passenger_journeys_thousands"] - aggregate["average_daily_journeys_thousands"] * pd.to_datetime(aggregate["month"]).dt.days_in_month
    report.add("aggregate_monthly_daily_reconciliation", difference.notna().all() and difference.abs().le(DAILY_TOLERANCE_THOUSANDS).all(), "The five analytical series reconcile on the same calendar basis.", {"comparisons": len(aggregate), "tolerance_thousands": DAILY_TOLERANCE_THOUSANDS, "max_absolute_difference_thousands": float(difference.abs().max())})
    return reconciled.drop(columns="_merge")
