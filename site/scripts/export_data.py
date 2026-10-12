"""Export the existing validated research outputs as a deterministic static asset.

Run from any directory with Python 3.10 or later; no third-party packages or
network access are required. This script reads analytical outputs and writes
only site/public/data/research.json. --check is strictly read-only.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "site/public/data/research.json"
YEARS = tuple(range(2015, 2026))
MODES = ("GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS")
BASES = {"GMB": "reported", "RMB": "estimated", "PLB": "mixed",
         "MTR": "reported", "FRANCHISED_BUS": "reported"}
INPUTS = (
    "analysis/outputs/annual_ridership.csv",
    "analysis/outputs/endpoint_comparison.csv",
    "analysis/outputs/recovery_2019.csv",
    "analysis/outputs/annual_minibus_composition.csv",
    "analysis/outputs/trend_segments.csv",
    "analysis/outputs/analysis_summary.json",
    "config/sources.json",
    "src/hk_minibus/dashboard/metrics.py",
    "docs/analysis_methodology.md",
    "reports/eda_findings.md",
    "analysis/outputs/annual_market_share.csv",
    "analysis/outputs/annual_fleet.csv",
    "data/processed/monthly_minibus_fleet.csv",
    "docs/data_dictionary.md",
    "docs/data_sources.md",
    "reports/reference_discrepancies.md",
    "src/hk_minibus/dashboard/charts.py",
)
REPOSITORY = "https://github.com/AndyLamyinwik/HongKong-minibus-ridership-analysis"


def read_csv(root: Path, filename: str, required: set[str], *,
             folder: str = "analysis/outputs") -> list[dict[str, str]]:
    with (root / folder / filename).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{filename}: missing required columns")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{filename}: no analytical records")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{filename}: malformed CSV record")
    return rows


def number(value: str, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label}: a finite value is required")
    return result


def flag(value: str) -> bool:
    if value not in ("0", "1"):
        raise ValueError("Analytical flags must be 0 or 1")
    return value == "1"


def positive_integer(value: str, label: str) -> int:
    result = number(value, label)
    if result <= 0 or not result.is_integer():
        raise ValueError(f"{label}: a positive integer is required")
    return int(result)


def equal(actual: float, expected: float, label: str, tolerance: float = 1e-7) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance):
        raise ValueError(f"{label}: analytical outputs disagree")


def keyed(rows: list[dict[str, str]], columns: tuple[str, ...], label: str) -> dict:
    result = {}
    for row in rows:
        key = tuple(row[column] for column in columns)
        if key in result:
            raise ValueError(f"{label}: duplicate {columns} key {key}")
        result[key] = row
    return result


def build_export(root: Path = ROOT) -> dict:
    """Read and cross-check existing totals; never run the analytical pipeline."""
    sources = json.loads((root / "config/sources.json").read_text(encoding="utf-8"))
    summary = json.loads((root / "analysis/outputs/analysis_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") not in ("passed", "passed_with_warnings"):
        raise ValueError("The existing analysis has not passed validation")
    scope = summary.get("scope", {})
    if scope != {"start_month": "2015-01-01", "end_month": "2025-12-01", "months": 132}:
        raise ValueError("Analysis scope must contain all 132 months, 2015–2025")
    for field in ("snapshot_retrieved_on", "expected_revision_date"):
        date.fromisoformat(sources[field])

    annual_rows = read_csv(root, "annual_ridership.csv", {
        "year", "mode", "passenger_journeys_thousands", "measurement_basis",
        "includes_estimates", "is_provisional", "is_revised"})
    annual = keyed(annual_rows, ("year", "mode"), "Annual ridership")
    required_keys = {(str(year), mode) for year in YEARS for mode in MODES}
    if set(annual) != required_keys:
        raise ValueError("Annual ridership must contain exactly five modes × eleven complete years")
    values = {}
    for key, row in annual.items():
        mode = key[1]
        value = number(row["passenger_journeys_thousands"], "Annual journeys")
        if value <= 0:
            raise ValueError("Annual journeys must be positive")
        if row["measurement_basis"] != BASES[mode] or flag(row["includes_estimates"]) != (mode in ("RMB", "PLB")):
            raise ValueError("Annual measurement definitions do not match the validated mode definitions")
        flag(row["is_provisional"])
        flag(row["is_revised"])
        values[key] = value
    for year in YEARS:
        equal(values[(str(year), "GMB")] + values[(str(year), "RMB")],
              values[(str(year), "PLB")], f"{year} PLB identity")

    endpoints = keyed(read_csv(root, "endpoint_comparison.csv", {
        "mode", "journeys_2015_thousands", "journeys_2019_thousands", "journeys_2025_thousands",
        "change_2015_2025_pct", "recovery_2025_vs_2019_pct", "measurement_basis", "includes_estimates"}),
        ("mode",), "Endpoint comparisons")
    recovery = keyed(read_csv(root, "recovery_2019.csv", {
        "mode", "baseline_2019_journeys_thousands", "journeys_2025_thousands", "recovery_pct",
        "measurement_basis", "includes_estimates"}),
        ("mode",), "2019 recovery")
    if set(endpoints) != {(mode,) for mode in MODES} or set(recovery) != {(mode,) for mode in MODES}:
        raise ValueError("Endpoint and recovery outputs require all five analytical modes")
    for mode in MODES:
        row = endpoints[(mode,)]
        for year in (2015, 2019, 2025):
            equal(number(row[f"journeys_{year}_thousands"], "Endpoint journeys"),
                  values[(str(year), mode)], f"{mode} {year} endpoint")
        equal(number(row["change_2015_2025_pct"], "Endpoint change"),
              100 * (values[("2025", mode)] / values[("2015", mode)] - 1), f"{mode} endpoint change", 1e-9)
        ratio = number(recovery[(mode,)]["recovery_pct"], "Recovery percentage")
        equal(ratio, number(row["recovery_2025_vs_2019_pct"], "Endpoint recovery"), f"{mode} recovery output", 1e-9)
        equal(ratio, 100 * values[("2025", mode)] / values[("2019", mode)], f"{mode} recovery ratio", 1e-9)
        equal(number(recovery[(mode,)]["baseline_2019_journeys_thousands"], "Recovery baseline"),
              values[("2019", mode)], f"{mode} 2019 recovery baseline")
        equal(number(recovery[(mode,)]["journeys_2025_thousands"], "Recovery endpoint"),
              values[("2025", mode)], f"{mode} 2025 recovery endpoint")
        if row["measurement_basis"] != BASES[mode] or flag(row["includes_estimates"]) != (mode in ("RMB", "PLB")):
            raise ValueError("Endpoint estimation metadata disagree with the analytical definitions")
        if recovery[(mode,)]["measurement_basis"] != BASES[mode] or flag(recovery[(mode,)]["includes_estimates"]) != (mode in ("RMB", "PLB")):
            raise ValueError("Recovery estimation metadata disagree with the analytical definitions")

    composition = keyed(read_csv(root, "annual_minibus_composition.csv", {
        "year", "mode", "passenger_journeys_thousands", "plb_journeys_thousands", "share_of_plb_pct"}),
        ("year", "mode"), "Annual minibus composition")
    if set(composition) != {(str(year), mode) for year in YEARS for mode in ("GMB", "RMB")}:
        raise ValueError("Minibus composition must contain two modes × eleven complete years")
    for key, row in composition.items():
        equal(number(row["passenger_journeys_thousands"], "Composition journeys"), values[key], "Composition numerator")
        equal(number(row["plb_journeys_thousands"], "Composition denominator"), values[(key[0], "PLB")], "Composition denominator")
        equal(number(row["share_of_plb_pct"], "Composition share"), 100 * values[key] / values[(key[0], "PLB")], "Composition share", 1e-9)

    segments = keyed(read_csv(root, "trend_segments.csv", {
        "segment", "mode", "start_year", "end_year", "start_journeys_thousands", "end_journeys_thousands", "change_pct"}),
        ("segment", "mode"), "Trend segments")
    for mode in ("GMB", "RMB"):
        row = segments[("2023_to_2025", mode)]
        if row["start_year"] != "2023" or row["end_year"] != "2025":
            raise ValueError("Recent trend segment must retain its 2023–2025 bounds")
        equal(number(row["start_journeys_thousands"], "Segment start"), values[("2023", mode)], "Recent trend start")
        equal(number(row["end_journeys_thousands"], "Segment end"), values[("2025", mode)], "Recent trend end")
        equal(number(row["change_pct"], "Segment change"), 100 * (values[("2025", mode)] / values[("2023", mode)] - 1), "Recent trend change", 1e-9)

    # Read preserved four-component shares. PLB is a separate derived subtotal,
    # never a fifth component of the denominator or stacked composition.
    share_modes = ("GMB", "RMB", "MTR", "FRANCHISED_BUS")
    shares = keyed(read_csv(root, "annual_market_share.csv", {
        "year", "mode", "passenger_journeys_thousands", "comparison_group_journeys_thousands",
        "share_pct", "measurement_basis", "includes_estimates"}),
        ("year", "mode"), "Annual comparison-group shares")
    if set(shares) != {(str(year), mode) for year in YEARS for mode in share_modes}:
        raise ValueError("Comparison-group shares must contain four exclusive components × eleven years")
    share_rows = []
    denominators = []
    plb_shares = {}
    for year in YEARS:
        denominator = number(shares[(str(year), "GMB")]["comparison_group_journeys_thousands"], "Comparison-group denominator")
        if denominator <= 0:
            raise ValueError("Comparison-group denominator must be positive")
        equal(denominator, sum(values[(str(year), mode)] for mode in share_modes), f"{year} exclusive comparison-group denominator")
        denominators.append({"year": year, "journeys_thousands": denominator})
        year_shares = {}
        for mode in share_modes:
            row = shares[(str(year), mode)]
            equal(number(row["comparison_group_journeys_thousands"], "Share denominator"), denominator, "Shared annual denominator")
            equal(number(row["passenger_journeys_thousands"], "Share numerator"), values[(str(year), mode)], "Share numerator")
            share = number(row["share_pct"], "Comparison-group share")
            if share < 0 or share > 100:
                raise ValueError("Comparison-group shares must be between 0 and 100 percent")
            equal(share, 100 * values[(str(year), mode)] / denominator, "Preserved annual share", 1e-9)
            if row["measurement_basis"] != BASES[mode] or flag(row["includes_estimates"]) != (mode == "RMB"):
                raise ValueError("Comparison-group numerator estimation metadata are inconsistent")
            year_shares[mode] = share
            share_rows.append({"year": year, "mode": mode, "share_pct": share,
                               "measurement_basis": row["measurement_basis"],
                               "includes_estimates": flag(row["includes_estimates"]),
                               "is_subtotal": False})
        equal(sum(year_shares.values()), 100, "Four comparison-group shares sum to 100", 1e-9)
        plb_share = year_shares["GMB"] + year_shares["RMB"]
        equal(plb_share, 100 * values[(str(year), "PLB")] / denominator, "Derived PLB subtotal", 1e-9)
        plb_shares[year] = plb_share
        share_rows.append({"year": year, "mode": "PLB", "share_pct": plb_share,
                           "measurement_basis": "mixed", "includes_estimates": True,
                           "is_subtotal": True})

    # The annual proxy retains the Phase 3 vehicle-days denominator. Verify it
    # against preserved reported month-end stocks; do not substitute December
    # stock or average twelve monthly ratios.
    fleet_source = keyed(read_csv(root, "annual_fleet.csv", {
        "year", "mode", "mean_month_end_licensed_vehicles", "december_licensed_vehicles",
        "annual_passenger_journeys_thousands", "calendar_days", "licensed_vehicle_days_proxy",
        "measurement_basis", "includes_estimates", "day_weighted_month_end_licensed_vehicles",
        "average_daily_journeys_per_licensed_vehicle"}), ("year", "mode"), "Annual fleet")
    if set(fleet_source) != {(str(year), mode) for year in YEARS for mode in ("GMB", "RMB")}:
        raise ValueError("Annual fleet must contain two modes × eleven complete years")
    fleet_monthly = keyed(read_csv(root, "monthly_minibus_fleet.csv", {
        "month", "mode", "licensed_vehicles", "fleet_unit", "measurement_basis"}, folder="data/processed"),
        ("month", "mode"), "Reported monthly fleet")
    if set(fleet_monthly) != {(f"{year}-{month:02}-01", mode) for year in YEARS for month in range(1, 13) for mode in ("GMB", "RMB")}:
        raise ValueError("Reported fleet must contain 132 complete months for each minibus mode")
    for row in fleet_monthly.values():
        positive_integer(row["licensed_vehicles"], "Month-end licensed stock")
        if row["measurement_basis"] != "reported" or row["fleet_unit"] != "vehicles":
            raise ValueError("Licensed fleet must remain reported administrative stock in vehicles")
    fleet_rows = []
    for year in YEARS:
        days = 366 if calendar.isleap(year) else 365
        for mode in ("GMB", "RMB"):
            row = fleet_source[(str(year), mode)]
            stock = positive_integer(row["december_licensed_vehicles"], "December licensed stock")
            vehicle_days = positive_integer(row["licensed_vehicle_days_proxy"], "Licensed vehicle-days proxy")
            if positive_integer(row["calendar_days"], "Annual calendar days") != days:
                raise ValueError("Annual fleet calendar days do not match the complete calendar year")
            monthly_stocks = [positive_integer(fleet_monthly[(f"{year}-{month:02}-01", mode)]["licensed_vehicles"], "Reported licensed stock") for month in range(1, 13)]
            if stock != monthly_stocks[-1]:
                raise ValueError("December fleet stock disagrees with the reported December observation")
            expected_vehicle_days = sum(monthly_stock * calendar.monthrange(year, month)[1] for month, monthly_stock in enumerate(monthly_stocks, start=1))
            if vehicle_days != expected_vehicle_days:
                raise ValueError("Annual vehicle-days proxy disagrees with day-weighted month-end stocks")
            equal(number(row["mean_month_end_licensed_vehicles"], "Mean monthly fleet"), sum(monthly_stocks) / 12, "Arithmetic mean of month-end stocks")
            equal(number(row["day_weighted_month_end_licensed_vehicles"], "Day-weighted fleet"), vehicle_days / days, "Day-weighted fleet denominator")
            equal(number(row["annual_passenger_journeys_thousands"], "Annual fleet passenger input"), values[(str(year), mode)], "Annual proxy numerator")
            proxy = number(row["average_daily_journeys_per_licensed_vehicle"], "Annual journeys per licensed vehicle-day proxy")
            equal(proxy, 1000 * values[(str(year), mode)] / vehicle_days, "Existing annual fleet-normalized proxy", 1e-9)
            if row["measurement_basis"] != BASES[mode] or flag(row["includes_estimates"]) != (mode == "RMB"):
                raise ValueError("Fleet-normalized proxy passenger-estimation metadata are inconsistent")
            baseline = fleet_source[("2015", mode)]
            fleet_rows.append({
                "year": year, "mode": mode, "december_licensed_vehicles": stock,
                "licensed_vehicle_days_proxy": vehicle_days,
                "journeys_per_licensed_vehicle_day_proxy": proxy,
                "index_stock_2015": 100 * stock / positive_integer(baseline["december_licensed_vehicles"], "2015 December stock"),
                "index_proxy_2015": 100 * proxy / number(baseline["average_daily_journeys_per_licensed_vehicle"], "2015 annual proxy"),
                "stock_measurement_basis": "reported", "proxy_measurement_basis": row["measurement_basis"],
                "measurement_basis": row["measurement_basis"], "includes_estimates": flag(row["includes_estimates"]),
            })
    fleet_endpoints = []
    for mode in ("GMB", "RMB"):
        start = fleet_source[("2015", mode)]
        end = fleet_source[("2025", mode)]
        fleet_endpoints.append({
            "mode": mode,
            "december_vehicles_2015": positive_integer(start["december_licensed_vehicles"], "2015 December stock"),
            "december_vehicles_2025": positive_integer(end["december_licensed_vehicles"], "2025 December stock"),
            "stock_change_pct": 100 * (number(end["december_licensed_vehicles"], "2025 stock") / number(start["december_licensed_vehicles"], "2015 stock") - 1),
            "proxy_change_pct": 100 * (number(end["average_daily_journeys_per_licensed_vehicle"], "2025 annual proxy") / number(start["average_daily_journeys_per_licensed_vehicle"], "2015 annual proxy") - 1),
        })

    chart_rows = []
    for year in YEARS:
        for mode in ("GMB", "RMB"):
            row = annual[(str(year), mode)]
            value = values[(str(year), mode)]
            chart_rows.append({
                "year": year, "mode": mode, "journeys_thousands": value,
                "index_2015": 100 * value / values[("2015", mode)],
                "measurement_basis": row["measurement_basis"],
                "includes_estimates": flag(row["includes_estimates"]),
                "is_provisional": flag(row["is_provisional"]),
                "is_revised": flag(row["is_revised"]),
            })

    return {
        "schema_version": 1,
        "study": {"start_year": 2015, "end_year": 2025, "months": 132},
        "units": {"journeys": "thousands of passenger journeys", "index": "own 2015 annual journeys = 100", "percentage": "percent",
                  "stock": "licensed vehicles at December month-end", "vehicle_days_proxy": "licensed vehicle-days proxy",
                  "fleet_proxy": "passenger journeys per licensed vehicle-day proxy", "share_change": "percentage points"},
        "annual": chart_rows,
        "kpis": {
            "plb_change_pct": number(endpoints[("PLB",)]["change_2015_2025_pct"], "PLB decade change"),
            "gmb_change_pct": number(endpoints[("GMB",)]["change_2015_2025_pct"], "GMB decade change"),
            "rmb_change_pct": number(endpoints[("RMB",)]["change_2015_2025_pct"], "RMB decade change"),
            "rmb_recovery_2019_pct": number(recovery[("RMB",)]["recovery_pct"], "RMB recovery"),
        },
        "narrative": {
            "gmb_share_2015_pct": number(composition[("2015", "GMB")]["share_of_plb_pct"], "2015 GMB share"),
            "gmb_share_2025_pct": number(composition[("2025", "GMB")]["share_of_plb_pct"], "2025 GMB share"),
            "gmb_change_2023_2025_pct": number(segments[("2023_to_2025", "GMB")]["change_pct"], "Recent GMB change"),
            "rmb_change_2023_2025_pct": number(segments[("2023_to_2025", "RMB")]["change_pct"], "Recent RMB change"),
        },
        "recovery": [{"mode": mode, "recovery_pct": number(recovery[(mode,)]["recovery_pct"], "Recovery percentage"),
                      "measurement_basis": recovery[(mode,)]["measurement_basis"],
                      "includes_estimates": flag(recovery[(mode,)]["includes_estimates"])} for mode in MODES],
        "recovery_definition": {"baseline_year": 2019, "reference_year": 2025,
                                "formula": "100 × own 2025 annual journeys / own 2019 annual journeys", "unit": "percent"},
        "market_share": {
            "components": list(share_modes), "denominator_includes_estimates": True,
            "definition": "Share of GMB + RMB + MTR railway services + franchised bus journeys; PLB is the GMB/RMB subtotal, never a fifth denominator component.",
            "denominators": denominators, "annual": share_rows,
            "endpoints": {"plb_share_2015_pct": plb_shares[2015], "plb_share_2025_pct": plb_shares[2025],
                          "plb_share_change_pp": plb_shares[2025] - plb_shares[2015]},
        },
        "fleet": {
            "stock_measurement_basis": "reported",
            "definitions": {"stock": "December month-end licensed vehicles",
                            "proxy": "annual passenger journeys in thousands × 1,000 / sum(month-end licensed vehicles × calendar days)",
                            "index_stock_2015": "own December 2015 licensed stock = 100",
                            "index_proxy_2015": "own 2015 annual journeys per licensed vehicle-day proxy = 100",
                            "measurement_basis": "Annual-row measurement_basis and includes_estimates describe the proxy passenger input; licensed stock is reported for both GMB and RMB."},
            "annual": fleet_rows, "endpoints": fleet_endpoints,
        },
        "provenance": {
            "publisher": sources["publisher"],
            "snapshot_retrieved_on": sources["snapshot_retrieved_on"],
            "expected_revision_date": sources["expected_revision_date"],
            "official_urls": [
                "https://data.gov.hk/en-data/dataset/hk-td-tis_17-monthly-traffic-and-transport-digest-csv",
                "https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table21_eng.csv",
                "https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table22_eng.csv",
            ],
            "terms_url": sources["terms_url"],
            "methodology_url": REPOSITORY + "/blob/main/docs/analysis_methodology.md",
            "findings_url": REPOSITORY + "/blob/main/reports/eda_findings.md",
            "input_sha256": {filename: hashlib.sha256((root / filename).read_bytes()).hexdigest() for filename in INPUTS},
            "limitations": [
                "Red Minibus passenger journeys are estimates, with no published confidence intervals.",
                "Public Light Bus totals contain estimated Red Minibus journeys.",
                "Annual totals sum twelve monthly flows from one source vintage; figures may be revised.",
                "Journeys are aggregate patronage, not unique passengers. These comparisons do not establish causation or passenger switching.",
                "The comparison group is a defined transport subset, not all Hong Kong public transport; every share denominator contains estimated RMB journeys.",
                "MTR includes MTR Lines, Airport Express and Light Rail, including cross-boundary MTR Lines services; it excludes Tramways and MTR buses. Network coverage changed during the study.",
                "Franchised buses include each contemporaneous franchise once, with the July 2023 Citybus/NWFB merger handled in preparation.",
                "Licensed vehicle-days use reported month-end stocks as a proxy for daily availability; the indicator does not measure occupancy, deployment or operational productivity.",
                "RMB estimation uses licensed fleet information, so passenger/fleet associations are partly mechanical; no comparable RMB mileage is filled or inferred.",
                "Six older provisional annual references differ from this preserved monthly-snapshot vintage. Their specific revision causes remain unresolved; cross-vintage differences are not uncertainty bounds for RMB estimates.",
            ],
        },
    }


def render_export(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the bundled asset without changing any files")
    arguments = parser.parse_args()
    try:
        content = render_export(build_export())
        if arguments.check:
            if not DESTINATION.is_file() or DESTINATION.read_bytes() != content:
                print("Static research data are missing or stale. Run python site/scripts/export_data.py.", file=sys.stderr)
                return 1
            print("Static research data match the authoritative analytical outputs (22 annual trend observations, 4 KPIs, 5 recoveries, 55 share observations, 22 fleet observations).")
        else:
            DESTINATION.parent.mkdir(parents=True, exist_ok=True)
            DESTINATION.write_bytes(content)
            print(f"Exported site/public/data/research.json ({len(content):,} bytes; 22 annual trend observations, 4 KPIs, 5 recoveries, 55 shares, 22 fleet observations).")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Static data export failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
