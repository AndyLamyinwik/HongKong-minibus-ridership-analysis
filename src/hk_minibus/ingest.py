"""Load source tokens, verify immutable provenance, and audit source contracts."""

import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from .config import HEADERS, NUMERIC_FIELDS, SOURCE_BASE, SOURCE_KEYS
from .validation import PreparationError, ValidationReport

MISSING_TOKENS = {"", "N.A.", "-"}
STATUS_TOKENS = {"", "#", "*", "N.A.", "-"}


def parse_numeric(tokens: pd.Series, field: str, report: ValidationReport, check_id: str) -> pd.Series:
    """Recognize official unavailable tokens; never coerce invalid text silently."""
    unavailable = tokens.isin(MISSING_TOKENS)
    parsed = pd.to_numeric(tokens.mask(unavailable, pd.NA), errors="coerce").astype("Float64")
    finite = parsed.map(lambda value: True if pd.isna(value) else math.isfinite(float(value)))
    invalid = (~unavailable & parsed.isna()) | ~finite
    report.add(check_id, not invalid.any(), f"{field}: nonblank tokens must be finite numbers.", {"invalid_count": int(invalid.sum()), "examples": tokens[invalid].head(20).to_dict()})
    return parsed


def load_sources(raw_dir: Path, manifest_path: Path, report: ValidationReport):
    """Return typed source frames, provenance records and a full-file inspection."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames, sources, inspection = {}, [], {}
    for spec in manifest["files"]:
        path = raw_dir / spec["filename"]
        source_id = spec["source_id"]
        if not path.is_file():
            report.add(f"file_{source_id}", False, "Required source file is missing.", {"filename": spec["filename"]})
            continue
        raw_bytes = path.read_bytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        report.add(f"hash_{source_id}", digest == spec["sha256"] and len(raw_bytes) == spec["size_bytes"], "Raw bytes must match the reviewed Phase 1 snapshot.", {"filename": spec["filename"], "expected_sha256": spec["sha256"], "actual_sha256": digest, "bytes": len(raw_bytes)})
        sources.append({"source_id": source_id, "filename": spec["filename"], "source_url": SOURCE_BASE + spec["filename"], "publisher": manifest["publisher"], "retrieved_on": manifest["snapshot_retrieved_on"], "revision_date": manifest["expected_revision_date"], "sha256": digest, "size_bytes": len(raw_bytes), "file_format": spec["file_format"]})
        if spec["file_format"] == "PDF":
            report.add(f"format_{source_id}", raw_bytes.startswith(b"%PDF-"), "The specification must be an actual PDF.")
            inspection[source_id] = {"filename": spec["filename"], "format": "PDF", "role": "Definitions and units; no numerical extraction in the pipeline."}
            continue
        # All cells initially remain strings: no inferred float franchise codes,
        # automatic NA conversion, or loss of intentional blank identifiers.
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8-sig")
        expected_header = HEADERS[source_id]
        report.add(f"schema_{source_id}", list(frame.columns) == expected_header, "Source column names and order must match the reviewed schema.", {"expected": expected_header, "actual": list(frame.columns)})
        if list(frame.columns) != expected_header:
            continue
        for column in frame.columns:
            frame[column] = frame[column].str.strip()
        frame["source_row_number"] = range(2, len(frame) + 2)
        frame["source_record_id"] = source_id + ":" + frame["source_row_number"].astype(str)
        frame["source_id"] = source_id
        if source_id == "td_revision":
            actual = frame["DATA_REVISION_DATE"].tolist()
            report.add("source_revision_date", actual == [manifest["expected_revision_date"]], "The revision metadata must match the manifest.", {"actual": actual, "expected": manifest["expected_revision_date"]})
            inspection[source_id] = {"filename": spec["filename"], "format": "CSV", "record_count": len(frame), "columns": expected_header, "revision_date": actual}
            continue
        dates = pd.to_datetime(frame["YR_MTH"], format="%Y%m", errors="coerce")
        valid_dates = frame["YR_MTH"].str.fullmatch(r"\d{6}") & dates.notna()
        report.add(f"dates_{source_id}", valid_dates.all(), "Reference months must be valid six-digit YYYYMM tokens.", {"invalid_rows": frame.loc[~valid_dates, ["source_record_id", "YR_MTH"]].head(20).to_dict("records")})
        frame["month"] = dates.dt.strftime("%Y-%m-%d")
        duplicates = frame.duplicated(SOURCE_KEYS[source_id], keep=False)
        report.add(f"duplicates_{source_id}", not duplicates.any(), "Full source dimension keys must be unique; duplicate records are rejected, never dropped.", {"duplicate_rows": frame.loc[duplicates, ["source_record_id"] + SOURCE_KEYS[source_id]].head(20).to_dict("records")})
        numeric_inspection = {}
        for column in NUMERIC_FIELDS[source_id]:
            tokens = frame[column].copy()
            frame[column + "__raw"] = tokens
            parsed = parse_numeric(tokens, column, report, f"numeric_{source_id}_{column}")
            report.add(f"nonnegative_{source_id}_{column}", parsed.dropna().ge(0).all(), f"{column}: negative values are invalid.", {"negative_rows": frame.loc[parsed.lt(0).fillna(False), "source_record_id"].head(20).tolist()})
            numeric_inspection[column] = {"input_dtype": "string", "prepared_dtype": "Float64 (nullable)", "blank_or_unavailable_count": int(tokens.isin(MISSING_TOKENS).sum()), "zero_count": int(parsed.eq(0).sum()), "negative_count": int(parsed.lt(0).sum())}
            frame[column] = parsed
        indicators = {}
        for column in [c for c in expected_header if c.endswith("_INDI")]:
            invalid = ~frame[column].isin(STATUS_TOKENS)
            report.add(f"indicators_{source_id}_{column}", not invalid.any(), "Status tokens must be recognized; estimate labels are separate from these tokens.", {"unrecognized": frame.loc[invalid, column].unique().tolist()})
            indicators[column] = {str(key): int(value) for key, value in frame[column].value_counts(dropna=False).items()}
        inspection[source_id] = {"filename": spec["filename"], "format": "CSV", "record_count": len(frame), "columns": expected_header, "source_key": SOURCE_KEYS[source_id], "month_count": frame["month"].nunique(), "first_month": frame["month"].min(), "last_month": frame["month"].max(), "numeric_fields": numeric_inspection, "status_counts": indicators, "dimension_blank_counts": {c: int(frame[c].eq("").sum()) for c in SOURCE_KEYS[source_id]}, "source_modes": sorted(frame["MODE"].unique()), "operator_codes": sorted(frame["TTD_PTO_CODE"].unique())}
        frames[source_id] = frame
    report.require_success()
    if set(frames) != {"td_table21", "td_table21s", "td_table22"}:
        raise PreparationError("The three required statistical source tables were not loaded.")
    return frames, sources, inspection
