"""Build and inspect the portable SQLite data preparation layer.

The loader inserts already prepared frames in one transaction. It never changes
source values, aggregates measures, or computes analytical results.
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


FRAME_TABLES = (
    "passenger_source_records",
    "daily_source_records",
    "monthly_passenger_journeys",
    "monthly_average_daily_journeys",
    "monthly_minibus_fleet",
    "passenger_lineage",
    "daily_lineage",
)
VIEW_NAMES = (
    "v_monthly_comparison_group",
    "v_monthly_minibus_journeys",
    "v_monthly_minibus_fleet_context",
    "v_passenger_source_lineage",
    "v_daily_reconciliation_inputs",
    "v_monthly_passenger_wide",
)
_SQL_DIRECTORY = Path(__file__).resolve().parents[2] / "sql"


def _sqlite_value(value: Any) -> Any:
    """Convert Pandas nullable scalars without silently storing NaN as zero."""
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite numeric values cannot be loaded into SQLite")
    return value


def _table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]


def _insert_records(
    connection: sqlite3.Connection, table: str, records: list[dict[str, Any]]
) -> None:
    columns = _table_columns(connection, table)
    expected = set(columns)
    for row_number, record in enumerate(records, start=1):
        if set(record) != expected:
            missing = sorted(expected - set(record))
            extra = sorted(set(record) - expected)
            raise ValueError(
                f"{table} record {row_number} columns differ: missing={missing}, extra={extra}"
            )
    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(f'"{column}"' for column in columns)
    connection.executemany(
        f'INSERT INTO "{table}" ({column_list}) VALUES ({placeholders})',
        [tuple(_sqlite_value(record[column]) for column in columns) for record in records],
    )


def _check_records(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": check["check_id"],
            "status": check["status"],
            "severity": check["severity"],
            "message": check["message"],
            "details_json": json.dumps(check["details"], sort_keys=True, allow_nan=False),
        }
        for check in checks
    ]


def write_database(
    path: Path,
    frames: dict[str, pd.DataFrame],
    source_files: list[dict[str, Any]],
    transport_modes: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    metadata: dict[str, str],
) -> None:
    """Create a new database transactionally, refusing to overwrite an old one.

    Callers can build in a temporary directory and replace published outputs only
    after validation. A failed build removes the newly created database.
    """
    path = Path(path).resolve()
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing database: {path}")
    if set(frames) != set(FRAME_TABLES):
        raise ValueError(
            f"Database frames differ: missing={sorted(set(FRAME_TABLES) - set(frames))}, "
            f"extra={sorted(set(frames) - set(FRAME_TABLES))}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        schema = (_SQL_DIRECTORY / "schema.sql").read_text(encoding="utf-8")
        views = (_SQL_DIRECTORY / "views.sql").read_text(encoding="utf-8")
        # executescript commits any preceding transaction. Begin inside the script
        # so that schema, views, and all subsequent inserts share one transaction.
        connection.executescript("BEGIN IMMEDIATE;\n" + schema + "\n" + views)
        _insert_records(connection, "source_files", source_files)
        _insert_records(connection, "transport_modes", transport_modes)
        _insert_records(
            connection, "metadata", [{"key": key, "value": value} for key, value in metadata.items()]
        )
        for table in FRAME_TABLES:
            frame = frames[table]
            expected = set(_table_columns(connection, table))
            if not frame.columns.is_unique or set(frame.columns) != expected:
                raise ValueError(f"{table} DataFrame columns do not match the SQL schema")
            _insert_records(connection, table, frame.to_dict(orient="records"))
        _insert_records(connection, "validation_checks", _check_records(checks))
        connection.commit()
    except BaseException:
        connection.rollback()
        connection.close()
        path.unlink(missing_ok=True)
        raise
    else:
        connection.close()


def _check(check_id: str, passed: bool, message: str, details: Any) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if passed else "fail",
        "severity": "error",
        "message": message,
        "details": details,
    }


def inspect_database(path: Path, expected_counts: dict[str, int]) -> list[dict[str, Any]]:
    """Verify persisted integrity, expected row counts, and lineage cardinality."""
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    unknown = set(expected_counts) - set(FRAME_TABLES) - {"source_files", "transport_modes", "metadata", "validation_checks"}
    if unknown:
        raise ValueError(f"Unknown database tables for row count validation: {sorted(unknown)}")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        checks = [_check("sqlite_integrity", integrity == ["ok"], "SQLite file integrity", integrity)]
        foreign_keys = [list(row) for row in connection.execute("PRAGMA foreign_key_check")]
        checks.append(_check("sqlite_foreign_keys", not foreign_keys, "SQLite foreign-key integrity", foreign_keys))
        for table, expected in sorted(expected_counts.items()):
            actual = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            checks.append(
                _check(f"sqlite_count_{table}", actual == expected, f"Persisted row count for {table}",
                       {"expected": expected, "actual": actual})
            )
        actual_views = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'view'")
        }
        missing_views = sorted(set(VIEW_NAMES) - actual_views)
        checks.append(_check("sqlite_views", not missing_views, "Required SQL views exist", {"missing": missing_views}))
        for fact, lineage, label in (
            ("monthly_passenger_journeys", "passenger_lineage", "passenger"),
            ("monthly_average_daily_journeys", "daily_lineage", "daily"),
        ):
            mismatches = [
                {"month": row[0], "mode": row[1], "expected": row[2], "actual": row[3]}
                for row in connection.execute(
                    f"SELECT f.month, f.mode, f.component_count, COUNT(l.source_record_id) "
                    f"FROM {fact} f LEFT JOIN {lineage} l ON l.month=f.month AND l.mode=f.mode "
                    "GROUP BY f.month, f.mode HAVING COUNT(l.source_record_id) <> f.component_count"
                )
            ]
            checks.append(
                _check(f"sqlite_{label}_lineage_counts", not mismatches,
                       f"Each {label} observation has its declared source components", mismatches)
            )
        return checks
    finally:
        connection.close()


def replace_validation_checks(path: Path, checks: list[dict[str, Any]]) -> None:
    """Replace saved validation results atomically after inspecting the database."""
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            connection.execute("DELETE FROM validation_checks")
            _insert_records(connection, "validation_checks", _check_records(checks))
    finally:
        connection.close()
