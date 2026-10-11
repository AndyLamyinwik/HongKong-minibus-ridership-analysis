"""Reproducible local orchestration, export, and diagnostic reporting."""

import argparse
from collections import Counter
from contextlib import closing
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

import pandas as pd

from . import __version__
from .config import END_MONTH, MODES, PROJECT_ROOT, START_MONTH
from .database import inspect_database, replace_validation_checks, write_database
from .ingest import load_sources
from .transform import build_frames
from .validation import PreparationError, ValidationReport, reconcile_daily, validate_outputs

CSV_TABLES = ["monthly_passenger_journeys", "monthly_average_daily_journeys", "monthly_minibus_fleet"]


def json_safe(value):
    """Use JSON null for missing diagnostic values, never nonstandard NaN."""
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if value is None or value is pd.NA:
        return None
    if hasattr(value, "item"):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path: Path, value):
    path.write_text(json.dumps(json_safe(value), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def check_annual_references(passengers: pd.DataFrame, references_path: Path, report: ValidationReport):
    """Selected historical reference comparisons, never value replacement.

    Reference values are explicitly transcribed from the Phase 1 publications.
    Their source vintage differs; discrepancies are visible review warnings,
    not a reason to change the common CSV snapshot.
    """
    references = pd.read_csv(references_path, dtype=str, keep_default_na=False)
    expected_columns = ["publication", "source_url", "year", "mode", "passenger_journeys_thousands", "source_indicator", "notes"]
    if list(references.columns) != expected_columns:
        raise PreparationError("Annual reference schema does not match its documented contract.")
    annual_publication = "Annual Transport Digest 2025 section 5.3"
    monthly_publication = "December 2025 Monthly Traffic and Transport Digest Table 2.1"
    expected_keys = {(annual_publication, "2024", mode) for mode in ["GMB", "RMB", "PLB"]}
    expected_keys |= {(monthly_publication, year, mode) for year in ["2024", "2025"] for mode in ["GMB", "RMB", "PLB"]}
    actual_keys = set(references[["publication", "year", "mode"]].itertuples(index=False, name=None))
    expected_urls = {annual_publication: "https://www.td.gov.hk/mini_site/atd/2025/en/section5-3.html", monthly_publication: "https://www.td.gov.hk/filemanager/en/content_5378/2512_e.pdf"}
    amounts = pd.to_numeric(references["passenger_journeys_thousands"], errors="coerce")
    amounts_valid = amounts.notna().all() and amounts.map(lambda value: math.isfinite(float(value)) and value >= 0).all()
    urls_valid = all(row.source_url == expected_urls.get(row.publication) for row in references.itertuples(index=False))
    report.add("annual_reference_contract", len(references) == 9 and actual_keys == expected_keys and amounts_valid and urls_valid and not references.duplicated(["publication", "year", "mode"]).any(), "Nine distinct selected annual references require their documented publication, year, mode, official URL, and finite value.", {"actual_rows": len(references), "missing_keys": sorted(expected_keys - actual_keys), "unexpected_keys": sorted(actual_keys - expected_keys)})
    report.require_success()
    comparisons = []
    for row in references.to_dict("records"):
        if row["mode"] not in {"GMB", "RMB", "PLB"} or row["year"] not in {"2024", "2025"}:
            raise PreparationError("Unexpected selected annual reference year/mode.")
        values = passengers.loc[passengers["mode"].eq(row["mode"]) & passengers["month"].str.startswith(row["year"]), "passenger_journeys_thousands"]
        if len(values) != 12:
            raise PreparationError(f"Annual reference requires twelve months: {row['year']} {row['mode']}")
        total = sum((Decimal(str(value)) for value in values), Decimal(0))
        reference = Decimal(row["passenger_journeys_thousands"])
        difference = total - reference
        comparisons.append({**row, "current_snapshot_total_thousands": float(total), "reference_value_thousands": float(reference), "difference_thousands": float(difference), "rounding_tolerance_thousands": 0.5, "within_rounding_tolerance": abs(difference) <= Decimal("0.5")})
    details = {"comparisons": comparisons, "comparison_count": len(comparisons), "outside_rounding_tolerance_count": sum(not row["within_rounding_tolerance"] for row in comparisons), "scope": "Selected 2024/2025 minibus annual references only; not a full annual-publication audit."}
    if details["outside_rounding_tolerance_count"]:
        report.warn("cross_vintage_annual_references", "Older annual publications differ from the current CSV snapshot beyond whole-thousand rounding. Retain both vintages and review differences; no source values are changed.", details)
    else:
        report.add("cross_vintage_annual_references", True, "Selected older annual references agree within whole-thousand rounding.", details)


def build_summary(report, sources, inspection, frames, outputs_published, error=None):
    counts = Counter(check["status"] for check in report.checks)
    status = "failed" if counts["fail"] else "passed_with_warnings" if counts["warning"] else "passed"
    return json_safe({
        "pipeline_version": __version__, "status": status, "outputs_published": outputs_published,
        "publication_state": "published" if outputs_published else "rollback_incomplete" if error and "rollback was incomplete" in error else "not_published",
        "study_window": {"start_month": START_MONTH, "end_month": END_MONTH, "expected_months": 132},
        "check_counts": {key: counts[key] for key in ["pass", "warning", "fail"]},
        "record_counts": {name: len(frame) for name, frame in sorted(frames.items())},
        "source_files": sources, "source_inspection": inspection, "checks": report.checks,
        "error": error,
    })


def render_validation_report(summary: dict) -> str:
    """Human-readable report built from the machine-readable diagnostics."""
    publication_note = "Successful outputs are validated before replacement. A failed run must not be treated as a new validated dataset; earlier successful files are retained when replacement rollback completes."
    if summary["publication_state"] == "rollback_incomplete":
        publication_note = "Replacement rollback was incomplete. Inspect the execution error for potentially changed files and rerun from the preserved sources before using outputs."
    lines = ["# Phase 2 Validation Report", "", "Generated by the preparation pipeline from the preserved official snapshot.", "", f"**Status:** {summary['status']}. Checks: {summary['check_counts']['pass']} passed, {summary['check_counts']['warning']} warnings, {summary['check_counts']['fail']} failed.", "", "Study window: January 2015–December 2025 (132 months).", "", f"**Outputs published by this run:** {'yes' if summary['outputs_published'] else 'no'}. {publication_note}", "", "## Record counts", "", "| Table | Records |", "| --- | ---: |"]
    lines += [f"| `{table}` | {count:,} |" for table, count in summary["record_counts"].items()]
    lines += ["", "## Check results", "", "| Check | Status | Purpose |", "| --- | --- | --- |"]
    lines += [f"| `{check['check_id']}` | {check['status']} | {check['message'].replace('|', '/')} |" for check in summary["checks"]]
    lines += ["", "## Diagnostics and limitations", ""]
    for check in summary["checks"]:
        if check["status"] != "pass":
            lines += [f"### {check['check_id']}", "", check["message"], "", "```json", json.dumps(check["details"], indent=2, sort_keys=True, allow_nan=False), "```", ""]
    for key in ["operator_monthly_daily_reconciliation", "aggregate_monthly_daily_reconciliation"]:
        for check in summary["checks"]:
            if check["check_id"] == key:
                lines += [f"**{key}:** {check['details']['comparisons']:,} comparisons; maximum absolute residual {check['details']['max_absolute_difference_thousands']:.12g} thousand journeys; tolerance {check['details']['tolerance_thousands']:.12g} thousand journeys.", ""]
    lines += ["The monthly/daily check establishes arithmetic consistency, not independent corroboration of patronage. Selected annual reference sums exist only for validation; no growth, share, recovery, seasonality or journeys-per-vehicle results are calculated.", "", "## Reproduction", "", "```text", "python scripts/prepare_data.py", "python -m pytest -q", "```", "", "See [cleaning methodology](cleaning_methodology.md), [data dictionary](data_dictionary.md), and `data/processed/validation_summary.json` for field definitions and complete machine-readable detail.", ""]
    if summary["error"]:
        lines += ["Execution error: " + summary["error"], ""]
    return "\n".join(lines)


def validate_exports(output_dir: Path, frames: dict, report: ValidationReport):
    for table in CSV_TABLES:
        exported = pd.read_csv(output_dir / f"{table}.csv", keep_default_na=False, na_filter=False, float_precision="round_trip")
        report.add(f"csv_{table}_shape", list(exported.columns) == list(frames[table].columns) and len(exported) == len(frames[table]), "CSV export preserves columns and record count.")
        expected = frames[table]
        problems = []
        for column in expected:
            if pd.api.types.is_numeric_dtype(expected[column]):
                actual = pd.to_numeric(exported[column].replace("", None), errors="raise").astype("Float64")
                reference = expected[column].astype("Float64")
                if not actual.isna().equals(reference.isna()) or not (actual - reference).dropna().abs().le(1e-9).all():
                    problems.append(column)
            elif not exported[column].astype(str).equals(expected[column].astype(str)):
                problems.append(column)
        report.add(f"csv_{table}_values", not problems, "CSV round-trip preserves values, identifiers, status text, and nullness.", {"mismatched_columns": problems})


def validate_database_values(path: Path, frames: dict, report: ValidationReport):
    """Validate persisted records, including token text, rather than counts only."""
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        for table, expected in frames.items():
            columns = list(expected.columns)
            quoted = ",".join('"' + column + '"' for column in columns)
            actual = pd.read_sql_query(f'SELECT {quoted} FROM "{table}" ORDER BY rowid', connection)
            reference = expected.reset_index(drop=True)
            problems = []
            if len(actual) != len(reference):
                problems.append("record_count")
            else:
                for column in columns:
                    if pd.api.types.is_numeric_dtype(reference[column]):
                        stored = pd.to_numeric(actual[column], errors="raise").astype("Float64")
                        original = reference[column].astype("Float64")
                        if not stored.isna().equals(original.isna()) or not (stored - original).dropna().abs().le(1e-9).all():
                            problems.append(column)
                    elif not actual[column].astype(str).equals(reference[column].astype(str)):
                        problems.append(column)
            report.add(f"sqlite_values_{table}", not problems, "Persisted SQLite values, identifiers, source tokens and nullness equal the prepared records.", {"mismatched_columns": problems})


def _replace_from_copy(source: Path, target: Path):
    """Replace from a temporary file on the target filesystem, closing handles."""
    descriptor, temporary = tempfile.mkstemp(prefix=".prepare-", dir=target.parent)
    os.close(descriptor)
    temporary_path = Path(temporary)
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)


def _publish_artifacts(artifacts: list[tuple[Path, Path]], backup_dir: Path):
    """Replace reviewed outputs with rollback if any individual file is locked.

    Existing files are copied before any mutation. On a failed replacement,
    successful replacements are undone in reverse order. Paths are explicit;
    this helper never moves or deletes directories or unrelated files.
    """
    backup_dir.mkdir()
    previous = {}
    for index, (_, target) in enumerate(artifacts):
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = backup_dir / str(index)
            shutil.copy2(target, backup)
            previous[target] = backup
    replaced = []
    try:
        for source, target in artifacts:
            _replace_from_copy(source, target)
            replaced.append(target)
    except OSError as error:
        rollback_errors = []
        for target in reversed(replaced):
            try:
                if target in previous:
                    _replace_from_copy(previous[target], target)
                else:
                    target.unlink(missing_ok=True)
            except OSError as rollback_error:
                rollback_errors.append(f"{target.name}: {rollback_error}")
        if rollback_errors:
            raise PreparationError("Output replacement failed and rollback was incomplete. Inspect these potentially changed files: " + "; ".join(rollback_errors)) from error
        raise PreparationError(f"Output replacement failed; previous files were restored: {error}") from error


def run_pipeline(raw_dir: Path, output_dir: Path, manifest_path: Path, references_path: Path, report_path: Path):
    report, sources, inspection, frames = ValidationReport(), [], {}, {}
    output_dir = Path(output_dir).resolve()
    raw_dir = Path(raw_dir).resolve()
    report_path = Path(report_path).resolve()
    # Explicitly protect immutable input bytes from output path mistakes.
    if output_dir == raw_dir or output_dir.is_relative_to(raw_dir) or raw_dir.is_relative_to(output_dir):
        raise ValueError("Output directory must be separate from the raw input directory.")
    if report_path.is_relative_to(raw_dir):
        raise ValueError("Validation report must not be written inside the raw input directory.")
    protected = {Path(manifest_path).resolve(), Path(references_path).resolve()}
    protected |= {PROJECT_ROOT / item for item in ["README.md", "docs/data_sources.md", "docs/project_plan.md", "docs/cleaning_methodology.md", "docs/data_dictionary.md"]}
    if report_path.suffix.lower() != ".md" or report_path in protected:
        raise ValueError("Report path must be a Markdown diagnostic file separate from source/configuration files, processed datasets, and foundation documents.")
    output_dir.mkdir(parents=True, exist_ok=True)
    error, published = None, False
    try:
        loaded, sources, inspection = load_sources(raw_dir, manifest_path, report)
        frames = build_frames(loaded, report)
        validate_outputs(frames, report)
        reconcile_daily(frames, report)
        check_annual_references(frames["monthly_passenger_journeys"], references_path, report)
        report.warn("rmb_estimation_limit", "RMB patronage is estimated without published confidence intervals; PLB contains that estimated component. Blank status flags do not make it observed.")
        report.warn("service_scope_limit", "MTR includes changing services and cross-boundary journeys. Aggregate data cannot establish individual mode switching or causal demand effects.")
        report.warn("licensed_fleet_limit", "Licensed fleet is a month-end administrative stock, not deployed service. RMB patronage estimates partly depend on fleet counts; unsupported mileage remains null.")
        report.require_success()
        # All files are built below the output directory and validated before
        # replacing published files. No directory moves/deletions are needed.
        with tempfile.TemporaryDirectory(prefix=".build-", dir=output_dir) as working:
            build_dir = Path(working)
            for table in CSV_TABLES:
                frames[table].to_csv(build_dir / f"{table}.csv", index=False, na_rep="", encoding="utf-8", lineterminator="\n")
            validate_exports(build_dir, frames, report)
            report.require_success()
            report.checks = json_safe(report.checks)
            database_path = build_dir / "transport.sqlite"
            write_database(database_path, frames, sources, MODES, report.checks, {"pipeline_version": __version__, "study_start_month": START_MONTH, "study_end_month": END_MONTH, "comparison_group": "PLB,MTR,FRANCHISED_BUS", "source_manifest_sha256": hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(), "annual_reference_config_sha256": hashlib.sha256(Path(references_path).read_bytes()).hexdigest(), "raw_reuse_terms_url": "https://data.gov.hk/en/terms-and-conditions"})
            expected_counts = {name: len(frame) for name, frame in frames.items()}
            expected_counts.update({"source_files": len(sources), "transport_modes": len(MODES)})
            report.checks.extend(inspect_database(database_path, expected_counts))
            validate_database_values(database_path, frames, report)
            report.require_success()
            replace_validation_checks(database_path, report.checks)
            report.add("raw_sources_unchanged", all(hashlib.sha256((raw_dir / source["filename"]).read_bytes()).hexdigest() == source["sha256"] for source in sources), "Raw hashes remain unchanged after preparation and database construction.")
            report.require_success()
            replace_validation_checks(database_path, report.checks)
            write_json(build_dir / "source_inspection.json", inspection)
            success_summary = build_summary(report, sources, inspection, frames, True)
            write_json(build_dir / "validation_summary.json", success_summary)
            build_report_path = build_dir / "validation_report.md"
            build_report_path.write_text(render_validation_report(success_summary), encoding="utf-8", newline="\n")
            artifacts = [(artifact, output_dir / artifact.name) for artifact in sorted(build_dir.iterdir()) if artifact.name != "validation_report.md"]
            artifacts.append((build_report_path, report_path))
            _publish_artifacts(artifacts, build_dir / ".previous")
            published = True
    except (PreparationError, ValueError, OSError, KeyError, sqlite3.Error) as exception:
        error = str(exception)
        if not report.failed:
            report.add("pipeline_execution", False, "Preparation stopped without publishing validated datasets.", {"error_type": type(exception).__name__, "error": error})
    summary = build_summary(report, sources, inspection, frames, published, error)
    if not published:
        # Diagnostic artifacts identify a failed attempt; valid data outputs
        # remain at their last successful versions after a completed rollback.
        write_json(output_dir / "validation_summary.json", summary)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_validation_report(summary), encoding="utf-8", newline="\n")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Prepare and validate the preserved 2015–2025 TD snapshot.")
    parser.add_argument("--raw-dir", type=Path, default=PROJECT_ROOT / "data/raw")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data/processed")
    parser.add_argument("--manifest", type=Path, default=PROJECT_ROOT / "config/sources.json")
    parser.add_argument("--references", type=Path, default=PROJECT_ROOT / "config/reference_values.csv")
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "docs/validation_report.md")
    args = parser.parse_args(argv)
    try:
        summary = run_pipeline(args.raw_dir, args.output_dir, args.manifest, args.references, args.report)
    except ValueError as exception:
        parser.error(str(exception))
    print(json.dumps({"status": summary["status"], "check_counts": summary["check_counts"], "record_counts": summary["record_counts"], "outputs_published": summary["outputs_published"], "error": summary["error"]}, indent=2))
    return 1 if summary["status"] == "failed" else 0
