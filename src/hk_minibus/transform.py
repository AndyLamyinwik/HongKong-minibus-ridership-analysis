"""Explicit transport mapping and compatible-component aggregation."""

from decimal import Decimal

import pandas as pd

from .config import DAILY_UNIT, MODE_LOOKUP, MONTHLY_UNIT
from .validation import ValidationReport, target_months


def expected_source_keys(source_id: str):
    """The reviewed historical category contract, including July 2023 change."""
    keys = set()
    for month in target_months():
        if source_id == "td_table22":
            keys.update((month, "PLB", mode, "", "", "") for mode in ["GMB", "RMB"])
            continue
        if source_id == "td_table21":
            keys.update((month, "PLB", mode, "", "") for mode in ["GMB", "RMB"])
            keys.update((month, "Railways", "MTRC", "", rail) for rail in ["Local", "Airport", "LRT"])
            keys.update((month, "Fran_Bus", bus, "", "") for bus in ["KMB", "LWB", "NLB"])
            keys.add((month, "Fran_Bus", "CTB", "2", ""))
            keys.add((month, "Fran_Bus", "CTB", "1" if month < "2023-07-01" else "3", ""))
            if month < "2023-07-01":
                keys.add((month, "Fran_Bus", "NWFB", "", ""))
        else:
            keys.update((month, "PLB", mode, "") for mode in ["GMB", "RMB"])
            keys.update((month, "Railways", "MTRC", rail) for rail in ["Local", "Airport", "LRT"])
            keys.update((month, "Fran_Bus", bus, "") for bus in ["KMB", "CTB", "LWB", "NLB"])
            if month < "2023-07-01":
                keys.add((month, "Fran_Bus", "NWFB", ""))
    return keys


def select_scope(sources: dict[str, pd.DataFrame], report: ValidationReport):
    scoped = {}
    keys_by_source = {
        "td_table21": ["month", "MODE", "TTD_PTO_CODE", "FRANCHISE_TYPE", "RAIL_LINE"],
        "td_table21s": ["month", "MODE", "TTD_PTO_CODE", "RAIL_LINE"],
        "td_table22": ["month", "MODE", "TTD_PTO_CODE", "FRANCHISE_TYPE", "RAIL_LINE", "BUS_TYPE_CODE"],
    }
    for source_id, frame in sources.items():
        in_window = frame["month"].isin(target_months())
        relevant = frame["MODE"].eq("PLB") if source_id == "td_table22" else (frame["MODE"].isin(["PLB", "Fran_Bus"]) | frame["TTD_PTO_CODE"].eq("MTRC"))
        selected = frame.loc[in_window & relevant].copy()
        expected = expected_source_keys(source_id)
        actual = set(selected[keys_by_source[source_id]].itertuples(index=False, name=None))
        report.add(f"target_components_{source_id}", actual == expected and len(selected) == len(expected), "All target components must be present exactly once under the documented historical category definitions.", {"expected_rows": len(expected), "actual_rows": len(selected), "missing_keys": sorted(expected - actual)[:30], "unexpected_keys": sorted(actual - expected)[:30], "missing_key_count": len(expected - actual), "unexpected_key_count": len(actual - expected)})
        required_numeric = ["NO_FLEET", "PAX_CAP"] if source_id == "td_table22" else ["PAX" if source_id == "td_table21" else "AVG_DAILY_PAX"]
        for column in required_numeric:
            missing = selected[column].isna()
            report.add(f"required_{source_id}_{column}", not missing.any(), "Required target measurements cannot be missing; interpolation and zero replacement are prohibited.", {"missing_rows": selected.loc[missing, "source_record_id"].head(30).tolist(), "missing_count": int(missing.sum())})
        if source_id == "td_table22":
            for column in ["NO_FLEET", "PAX_CAP"]:
                valid_counts = selected[column].dropna().gt(0) & selected[column].dropna().mod(1).eq(0)
                report.add(f"integer_{source_id}_{column}", valid_counts.all(), "Licensed fleet and capacity must be positive integer counts.")
        scoped[source_id] = selected
    report.require_success()
    return scoped


def status_union(tokens) -> str:
    return "|".join(sorted({token for token in tokens if token}))


def prepare_source_passengers(frame: pd.DataFrame, daily: bool) -> pd.DataFrame:
    value_field = "AVG_DAILY_PAX" if daily else "PAX"
    value_name = "average_daily_journeys_thousands" if daily else "passenger_journeys_thousands"
    renamed = frame.rename(columns={"MODE": "source_mode", "TTD_PTO_CODE": "operator_code", "FRANCHISE_TYPE": "franchise_type", "RAIL_LINE": "rail_category", value_field: value_name, value_field + "__raw": "source_numeric_text", value_field + "_INDI": "source_indicator"}).copy()
    renamed["measurement_basis"] = renamed["operator_code"].map(lambda value: "estimated" if value == "RMB" else "reported")
    renamed["includes_estimates"] = renamed["operator_code"].eq("RMB").astype(int)
    columns = ["source_record_id", "source_id", "source_row_number", "month", "source_mode", "operator_code"]
    if not daily:
        columns += ["franchise_type"]
    columns += ["rail_category", value_name, "source_numeric_text", "source_indicator", "measurement_basis", "includes_estimates"]
    return renamed[columns].sort_values(["month", "source_mode", "operator_code", "rail_category", "source_record_id"]).reset_index(drop=True)


def aggregate_passengers(source: pd.DataFrame, daily: bool):
    value_name = "average_daily_journeys_thousands" if daily else "passenger_journeys_thousands"
    facts, links = [], []
    for month, month_rows in source.groupby("month", sort=True):
        for mode in MODE_LOOKUP:
            if mode in {"GMB", "RMB"}:
                selected = month_rows[month_rows["operator_code"] == mode]
            elif mode == "PLB":
                selected = month_rows[month_rows["source_mode"] == "PLB"]
            elif mode == "MTR":
                selected = month_rows[month_rows["operator_code"] == "MTRC"]
            else:
                selected = month_rows[month_rows["source_mode"] == "Fran_Bus"]
            expected = 1 if mode in {"GMB", "RMB"} else 2 if mode == "PLB" else 3 if mode == "MTR" else (5 if daily else 6) if month < "2023-07-01" else (4 if daily else 5)
            # A checked component set, not skip-na summation, determines whether
            # this aggregate is valid. This guard also protects standalone use.
            if len(selected) != expected or selected[value_name].isna().any():
                raise ValueError(f"Incomplete {mode} components for {month}: expected {expected}, found {len(selected)}")
            definition = MODE_LOOKUP[mode]
            indicator = status_union(selected["source_indicator"])
            # Sum decimal source tokens before storing a float; this avoids
            # introducing binary summation tails in published decimal totals.
            amount = sum((Decimal(token) for token in selected["source_numeric_text"]), Decimal(0))
            facts.append({"month": month, "mode": mode, value_name: float(amount), "unit": DAILY_UNIT if daily else MONTHLY_UNIT, "measurement_basis": definition["measurement_basis"], "includes_estimates": definition["includes_estimates"], "is_derived": int(mode not in {"GMB", "RMB"}), "source_id": "td_table21s" if daily else "td_table21", "source_indicator": indicator, "is_provisional": int("#" in indicator), "is_revised": int("*" in indicator), "component_count": expected})
            links.extend({"month": month, "mode": mode, "source_record_id": key} for key in selected["source_record_id"])
    return pd.DataFrame(facts).sort_values(["month", "mode"]).reset_index(drop=True), pd.DataFrame(links).sort_values(["month", "mode", "source_record_id"]).reset_index(drop=True)


def prepare_fleet(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.rename(columns={"TTD_PTO_CODE": "mode", "NO_FLEET": "licensed_vehicles", "PAX_CAP": "passenger_capacity", "KM": "vehicle_km_thousands", "KM_CROSS_HARBOUR": "cross_harbour_vehicle_km_thousands", "NO_FLEET__raw": "source_fleet_text", "PAX_CAP__raw": "source_capacity_text", "KM__raw": "source_km_text", "KM_CROSS_HARBOUR__raw": "source_cross_harbour_km_text", "NO_FLEET_INDI": "fleet_indicator", "PAX_CAP_INDI": "capacity_indicator", "KM_INDI": "km_indicator", "KM_CROSS_HARBOUR_INDI": "cross_harbour_km_indicator"}).copy()
    result["licensed_vehicles"] = result["licensed_vehicles"].astype("Int64")
    result["passenger_capacity"] = result["passenger_capacity"].astype("Int64")
    result["fleet_unit"] = "vehicles"
    result["capacity_unit"] = "passenger_places"
    result["km_unit"] = "thousand_vehicle_km"
    result["measurement_basis"] = "reported"
    statuses = result[["fleet_indicator", "capacity_indicator", "km_indicator", "cross_harbour_km_indicator"]].agg("|".join, axis=1)
    result["is_provisional"] = statuses.str.contains("#", regex=False).astype(int)
    result["is_revised"] = statuses.str.contains("*", regex=False).astype(int)
    columns = ["month", "mode", "licensed_vehicles", "passenger_capacity", "vehicle_km_thousands", "cross_harbour_vehicle_km_thousands", "fleet_unit", "capacity_unit", "km_unit", "measurement_basis", "source_id", "source_record_id", "source_row_number", "source_fleet_text", "source_capacity_text", "source_km_text", "source_cross_harbour_km_text", "fleet_indicator", "capacity_indicator", "km_indicator", "cross_harbour_km_indicator", "is_provisional", "is_revised"]
    return result[columns].sort_values(["month", "mode"]).reset_index(drop=True)


def build_frames(sources: dict[str, pd.DataFrame], report: ValidationReport) -> dict[str, pd.DataFrame]:
    scoped = select_scope(sources, report)
    passenger_source = prepare_source_passengers(scoped["td_table21"], daily=False)
    daily_source = prepare_source_passengers(scoped["td_table21s"], daily=True)
    passengers, passenger_links = aggregate_passengers(passenger_source, daily=False)
    daily, daily_links = aggregate_passengers(daily_source, daily=True)
    return {"passenger_source_records": passenger_source, "daily_source_records": daily_source, "monthly_passenger_journeys": passengers, "monthly_average_daily_journeys": daily, "monthly_minibus_fleet": prepare_fleet(scoped["td_table22"]), "passenger_lineage": passenger_links, "daily_lineage": daily_links}
