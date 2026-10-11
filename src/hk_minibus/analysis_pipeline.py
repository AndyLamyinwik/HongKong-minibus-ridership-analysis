"""Read-only input verification and reproducible Phase 3 output generation."""

from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

import numpy as np
import pandas as pd

from .analysis import ALL_MODES, COMPARISON_MODES, compute_tables
from .config import PROJECT_ROOT
from .pipeline import _publish_artifacts, write_json
from .validation import PreparationError, ValidationReport, target_months

INPUT_TABLES = ("monthly_passenger_journeys", "monthly_average_daily_journeys", "monthly_minibus_fleet")
SQL_QUERIES = ("annual_ridership", "monthly_yoy", "annual_market_share", "monthly_market_share", "recovery_2019", "fleet_normalized")
ANALYSIS_VERSION = "1.0.0"


def protected_input_hashes(root: Path) -> dict[str, str]:
    files = [*sorted((root / "data/raw").glob("*")), *sorted((root / "data/processed").glob("*")), root / "config/sources.json", root / "config/reference_values.csv"]
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files if path.is_file()}


def compare_frames(expected: pd.DataFrame, actual: pd.DataFrame) -> dict:
    """Compare numeric values, missingness, identifiers and quality metadata."""
    problems, differences = [], {}
    if list(actual.columns) != list(expected.columns) or len(actual) != len(expected):
        return {"equal": False, "problems": ["columns_or_row_count"], "expected_rows": len(expected), "actual_rows": len(actual)}
    for column in expected:
        left, right = expected[column].reset_index(drop=True), actual[column].reset_index(drop=True)
        if pd.api.types.is_numeric_dtype(left):
            right = pd.to_numeric(right.replace("", None), errors="coerce")
            if not left.isna().equals(right.isna()):
                problems.append(column + ":nullness")
            residual = (left.astype(float) - right.astype(float)).abs().dropna()
            tolerance = 1e-9 if column.endswith("pct") else 1e-7
            maximum = float(residual.max()) if len(residual) else 0.0
            differences[column] = maximum
            if maximum > tolerance:
                problems.append(column + ":value")
        else:
            left = left.fillna("").astype(str)
            right = right.fillna("").astype(str)
            if not left.equals(right):
                problems.append(column + ":text")
    return {"equal": not problems, "problems": problems, "rows": len(expected), "maximum_absolute_differences": differences}


def load_inputs(root: Path, report: ValidationReport):
    summary = json.loads((root / "data/processed/validation_summary.json").read_text(encoding="utf-8"))
    report.add("phase2_validated_run", summary["outputs_published"] and summary["check_counts"]["fail"] == 0, "Inputs must come from a successful Phase 2 validation run.", {"status": summary["status"], "check_counts": summary["check_counts"]})
    manifest = json.loads((root / "config/sources.json").read_text(encoding="utf-8"))
    raw_problems = [item["filename"] for item in manifest["files"] if hashlib.sha256((root / "data/raw" / item["filename"]).read_bytes()).hexdigest() != item["sha256"]]
    report.add("official_snapshot_hashes", not raw_problems, "All preserved official source files match the reviewed hashes.", {"mismatched_files": raw_problems})
    frames = []
    database_path = (root / "data/processed/transport.sqlite").resolve()
    with closing(sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only = ON")
        report.add("input_database_integrity", connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)] and not connection.execute("PRAGMA foreign_key_check").fetchall(), "The existing database passes integrity and foreign-key checks.")
        for name in INPUT_TABLES:
            frame = pd.read_csv(root / "data/processed" / f"{name}.csv", keep_default_na=False, float_precision="round_trip")
            if name == "monthly_minibus_fleet":
                for column in ["vehicle_km_thousands", "cross_harbour_vehicle_km_thousands"]:
                    frame[column] = pd.to_numeric(frame[column].replace("", None), errors="raise")
            sql_frame = pd.read_sql_query(f'SELECT * FROM "{name}" ORDER BY month,mode', connection)
            frame = frame.sort_values(["month", "mode"]).reset_index(drop=True)
            detail = compare_frames(frame, sql_frame[frame.columns])
            report.add(f"input_csv_sql_{name}", detail["equal"], "Existing CSV and SQLite observations agree, including quality metadata and nullness.", detail)
            modes = ("GMB", "RMB") if name == "monthly_minibus_fleet" else ALL_MODES
            expected = {(month, mode) for month in target_months() for mode in modes}
            actual = set(frame[["month", "mode"]].itertuples(index=False, name=None))
            report.add(f"input_coverage_{name}", len(frame) == len(expected) and actual == expected and not frame.duplicated(["month", "mode"]).any(), "All required month/mode observations must occur exactly once.", {"rows": len(frame), "missing_keys": sorted(expected - actual)[:10], "unexpected_keys": sorted(actual - expected)[:10]})
            if name == "monthly_minibus_fleet":
                units_ok = frame["fleet_unit"].eq("vehicles").all() and frame["capacity_unit"].eq("passenger_places").all()
                values_ok = frame["licensed_vehicles"].gt(0).all() and frame["passenger_capacity"].gt(0).all()
            else:
                value = "passenger_journeys_thousands" if name == "monthly_passenger_journeys" else "average_daily_journeys_thousands"
                unit = "thousand_journeys" if name == "monthly_passenger_journeys" else "thousand_journeys_per_day"
                units_ok = frame["unit"].eq(unit).all()
                values_ok = np.isfinite(frame[value]).all() and frame[value].ge(0).all()
                basis_ok = frame.loc[frame["mode"].eq("RMB"), "measurement_basis"].eq("estimated").all() and frame.loc[frame["mode"].eq("PLB"), "measurement_basis"].eq("mixed").all()
                report.add(f"input_estimates_{name}", basis_ok and frame["includes_estimates"].eq(frame["mode"].isin(["RMB", "PLB"]).astype(int)).all(), "RMB and mixed PLB qualifications are retained independently of source flags.")
            report.add(f"input_units_values_{name}", units_ok and values_ok, "Analysis inputs retain valid measurements and their documented units.")
            frames.append(frame)
        stored_checks = connection.execute("SELECT check_id,status,severity,message,details_json FROM validation_checks ORDER BY rowid").fetchall()
        actual_checks = [{"check_id": row[0], "status": row[1], "severity": row[2], "message": row[3], "details": json.loads(row[4])} for row in stored_checks]
        report.add("phase2_metadata_consistency", actual_checks == summary["checks"], "SQLite validation metadata agrees with the preserved Phase 2 JSON.")
    report.require_success()
    return frames, summary


def validate_calculations(tables: dict[str, pd.DataFrame], report: ValidationReport):
    monthly, annual = tables["monthly_ridership"], tables["annual_ridership"]
    source_annual = monthly.groupby(["year", "mode"])["passenger_journeys_thousands"].sum()
    actual_annual = annual.set_index(["year", "mode"])["passenger_journeys_thousands"]
    report.add("annual_totals_twelve_months", monthly.groupby(["year", "mode"]).size().eq(12).all() and (source_annual - actual_annual).abs().le(1e-7).all(), "Each annual total equals exactly twelve monthly flows, with no summed daily rates.")
    for name, key in [("monthly_ridership", "month"), ("annual_ridership", "year")]:
        wide = tables[name].pivot(index=key, columns="mode", values="passenger_journeys_thousands")
        residual = wide.GMB + wide.RMB - wide.PLB
        report.add(f"{name}_plb_identity", residual.abs().le(1e-7).all(), "GMB plus RMB equals PLB within floating-point calculation tolerance.", {"maximum_absolute_residual_thousands": float(residual.abs().max())})
    for name, key in [("monthly_market_share", "month"), ("annual_market_share", "year")]:
        shares = tables[name]
        sums = shares.groupby(key)["share_pct"].sum()
        groups = monthly if key == "month" else annual
        denominator = groups.loc[groups["mode"].isin(["PLB", "MTR", "FRANCHISED_BUS"])].groupby(key)["passenger_journeys_thousands"].sum()
        actual = shares.groupby(key)["comparison_group_journeys_thousands"].first()
        report.add(f"{name}_denominator", set(shares["mode"]) == set(COMPARISON_MODES) and shares.groupby(key).size().eq(4).all() and (denominator - actual).abs().le(1e-7).all(), "Four nonoverlapping series equal the PLB + MTR + franchised-bus denominator.")
        report.add(f"{name}_100_percent", (sums - 100).abs().le(1e-9).all(), "Comparison-group shares sum to 100%, without adding PLB again.", {"maximum_absolute_residual_percentage_points": float((sums - 100).abs().max())})
    annual_daily = monthly.groupby(["year", "mode"]).apply(lambda frame: (frame["average_daily_journeys_thousands"] * frame["calendar_days"]).sum(), include_groups=False)
    report.add("daily_calendar_weighting", (annual_daily - actual_annual).abs().le(1e-7).all(), "Calendar-day-weighted daily rates reproduce annual monthly-flow totals, including leap years.")
    baseline = tables["annual_recovery"].query("year == 2019")
    report.add("recovery_baseline_100", baseline["recovery_pct"].sub(100).abs().le(1e-9).all(), "Each mode's own full-year 2019 recovery index is 100%.")
    seasonality = tables["seasonality"]
    expected_counts = seasonality["period"].map({"pre_pandemic": 5, "pandemic_disruption": 3, "post_pandemic": 3})
    report.add("seasonality_period_grain", len(seasonality) == 180 and seasonality["observations"].eq(expected_counts).all(), "Calendar profiles contain equal-year observations within each stated period.")
    weighted_index = monthly.groupby(["year", "mode"]).apply(lambda frame: (frame["within_year_daily_index"] * frame["calendar_days"]).sum() / frame["calendar_days"].sum(), include_groups=False)
    report.add("within_year_daily_normalization", weighted_index.sub(100).abs().le(1e-9).all(), "Each year's day-weighted normalized monthly daily profile has baseline 100.")
    fleet = tables["fleet_normalized"]
    expected_proxy = fleet["average_daily_journeys_thousands"] * 1000 / fleet["licensed_vehicles"]
    report.add("fleet_proxy_units", len(fleet) == 264 and fleet["average_daily_journeys_per_licensed_vehicle"].sub(expected_proxy).abs().le(1e-9).all(), "Fleet normalization converts thousands to individual journeys and uses licensed stock.")
    report.require_success()


def annual_reference_table(tables, phase2_summary):
    comparisons = next(check["details"]["comparisons"] for check in phase2_summary["checks"] if check["check_id"] == "cross_vintage_annual_references")
    result = pd.DataFrame(comparisons)
    result["relative_difference_pct"] = result["difference_thousands"] / result["reference_value_thousands"] * 100
    endpoint = tables["endpoint_comparison"].set_index("mode")
    result["endpoint_2015_change_sensitivity_pp"] = result.apply(lambda row: -row["difference_thousands"] / endpoint.loc[row["mode"], "journeys_2015_thousands"] * 100 if row["year"] == "2025" else np.nan, axis=1)
    result["endpoint_2019_recovery_sensitivity_pp"] = result.apply(lambda row: -row["difference_thousands"] / endpoint.loc[row["mode"], "journeys_2019_thousands"] * 100 if row["year"] == "2025" else np.nan, axis=1)
    return result


def rebase_report_links(text: str, root: Path, analysis_dir: Path, report_path: Path) -> str:
    """Keep local artifact links correct when output destinations are customized."""
    canonical_parent = root / "reports"
    def replace(match):
        value = match.group(1)
        if value.startswith(("https://", "http://")):
            return match.group(0)
        target = (canonical_parent / value).resolve()
        if target.is_relative_to(root / "analysis"):
            target = analysis_dir / target.relative_to(root / "analysis")
        relative = os.path.relpath(target, report_path.parent).replace("\\", "/")
        return "](" + ("<" + relative + ">" if any(character in relative for character in " ()") else relative) + ")"
    return re.sub(r"\]\(([^)]+)\)", replace, text)


def run_analysis(root: Path = PROJECT_ROOT, analysis_dir: Path | None = None, report_path: Path | None = None) -> dict:
    root = Path(root).resolve()
    analysis_dir = (analysis_dir or root / "analysis").resolve()
    report_path = (report_path or root / "reports/eda_findings.md").resolve()
    protected_dirs = [root / "data/raw", root / "data/processed", root / "src", root / "sql", root / "config", root / "tests"]
    if any(analysis_dir == path or analysis_dir.is_relative_to(path) or path.is_relative_to(analysis_dir) for path in protected_dirs):
        raise ValueError("Analysis outputs must be separate from existing input, preparation, configuration and test directories.")
    protected_files = {root / "README.md", root / "reports/reference_discrepancies.md", *sorted((root / "docs").glob("*.md"))}
    if report_path.suffix != ".md" or report_path in protected_files or any(report_path.is_relative_to(path) for path in protected_dirs):
        raise ValueError("Findings report must be a separate Markdown file, outside protected project inputs.")
    before, report = protected_input_hashes(root), ValidationReport()
    inputs, phase2_summary = load_inputs(root, report)
    tables = compute_tables(*inputs)
    validate_calculations(tables, report)
    sql_results = {}
    sql_hashes = {}
    database = (root / "data/processed/transport.sqlite").resolve()
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only = ON")
        for name in SQL_QUERIES:
            path = root / "sql/analysis" / f"{name}.sql"
            sql_hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            sql_results[name] = pd.read_sql_query(path.read_text(encoding="utf-8"), connection)
            detail = compare_frames(tables[name], sql_results[name])
            report.add(f"sql_pandas_{name}", detail["equal"], "Independently calculated Pandas and SQL results agree, including undefined values and metadata.", detail)
    report.require_success()
    tables["annual_reference_comparisons"] = annual_reference_table(tables, phase2_summary)
    report.warn("annual_reference_revision_reasons", "Six older provisional annual references differ beyond rounding; publication updates are supported, but case-specific revision reasons remain unresolved.", {"investigation": "reports/reference_discrepancies.md", "outside_tolerance": 6})
    report.warn("estimation_and_service_boundaries", "RMB and PLB include estimates; all comparison-group denominators contain RMB. MTR service coverage changes, and these aggregate data do not identify causal effects or individual switching.")
    report.warn("seasonality_and_fleet_proxy", "Calendar profiles have five pre-period and three post-period years; within-year normalization does not remove trend or calendar shifts. Licensed stock is a deployment proxy and enters RMB estimation.")
    analysis_dir.mkdir(parents=True, exist_ok=True)
    from .figures import generate_figures
    from .analysis_report import render_findings
    with tempfile.TemporaryDirectory(prefix=".analysis-build-", dir=analysis_dir) as working:
        build = Path(working)
        outputs = build / "outputs"
        figures_dir = build / "figures"
        outputs.mkdir()
        (outputs / "sql").mkdir()
        for name, frame in tables.items():
            path = outputs / f"{name}.csv"
            frame.to_csv(path, index=False, na_rep="", encoding="utf-8", lineterminator="\n")
            exported = pd.read_csv(path, keep_default_na=False, float_precision="round_trip")
            detail = compare_frames(frame, exported)
            report.add(f"export_{name}", detail["equal"], "Analytical CSV round-trip preserves values, units, metadata and defined missingness.", detail)
        for name, frame in sql_results.items():
            frame.to_csv(outputs / "sql" / f"{name}.csv", index=False, na_rep="", encoding="utf-8", lineterminator="\n")
        figures = generate_figures(tables, figures_dir)
        report.add("research_figures", len(figures) == 7 and all((figures_dir / item["filename"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for item in figures), "Seven exploratory figures are generated as actual PNG files.")
        report.add("phase1_phase2_inputs_unchanged", protected_input_hashes(root) == before, "All raw, processed, database and source-configuration files retain their original bytes.")
        report.require_success()
        summary = {"analysis_version": ANALYSIS_VERSION, "status": "passed_with_warnings", "scope": {"start_month": "2015-01-01", "end_month": "2025-12-01", "months": 132}, "comparison_group": list(COMPARISON_MODES), "input_sha256": before, "sql_sha256": sql_hashes, "phase2_check_counts": phase2_summary["check_counts"], "record_counts": {name: len(frame) for name, frame in tables.items()}, "sql_record_counts": {name: len(frame) for name, frame in sql_results.items()}, "check_counts": {status: sum(check["status"] == status for check in report.checks) for status in ["pass", "warning", "fail"]}, "checks": report.checks, "figures": figures}
        write_json(outputs / "analysis_summary.json", summary)
        build_report = build / "eda_findings.md"
        build_report.write_text(rebase_report_links(render_findings(tables, summary), root, analysis_dir, report_path), encoding="utf-8", newline="\n")
        artifacts = [(path, analysis_dir / "outputs" / path.relative_to(outputs)) for path in sorted(outputs.rglob("*")) if path.is_file()]
        artifacts += [(figures_dir / item["filename"], analysis_dir / "figures" / item["filename"]) for item in figures]
        artifacts.append((build_report, report_path))
        _publish_artifacts(artifacts, build / ".previous")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Reproduce Phase 3 descriptive analysis from validated local inputs.")
    parser.add_argument("--analysis-dir", type=Path, default=PROJECT_ROOT / "analysis")
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "reports/eda_findings.md")
    args = parser.parse_args(argv)
    try:
        summary = run_analysis(analysis_dir=args.analysis_dir, report_path=args.report)
    except (PreparationError, ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, indent=2))
        return 1
    print(json.dumps({"status": summary["status"], "check_counts": summary["check_counts"], "record_counts": summary["record_counts"], "figures": len(summary["figures"])}, indent=2))
    return 0
