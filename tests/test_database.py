"""Software-only synthetic fixtures; these values are never analytical outputs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from hk_minibus.database import inspect_database, replace_validation_checks, write_database


@pytest.fixture
def database_inputs() -> dict:
    """One synthetic leap-year month with all defined aggregate boundaries."""
    month = "2020-02-01"
    sources = [
        {
            "source_id": source_id,
            "filename": filename,
            "source_url": f"https://example.invalid/test-fixture/{filename}",
            "publisher": "Synthetic test fixture",
            "retrieved_on": "2026-10-11",
            "revision_date": "2026-09-21",
            "sha256": "a" * 64,
            "size_bytes": 100,
            "file_format": "csv",
        }
        for source_id, filename in (
            ("td_table21", "test_table21.csv"),
            ("td_table21s", "test_table21s.csv"),
            ("td_table22", "test_table22.csv"),
        )
    ]
    definitions = [
        ("GMB", "reported", 0), ("RMB", "estimated", 1),
        ("PLB", "mixed", 1), ("MTR", "reported", 0),
        ("FRANCHISED_BUS", "reported", 0),
    ]
    modes = [
        {"mode": mode, "label": mode, "measurement_basis": basis,
         "includes_estimates": estimated, "definition": "Synthetic fixture definition"}
        for mode, basis, estimated in definitions
    ]
    components = [
        ("PLB", "GMB", "", 290.0), ("PLB", "RMB", "", 145.0),
        ("Railways", "MTRC", "Local", 580.0),
        ("Railways", "MTRC", "Airport", 29.0),
        ("Railways", "MTRC", "LRT", 58.0),
        ("Fran_Bus", "KMB", "", 870.0),
    ]
    passenger_rows = []
    daily_rows = []
    for row_number, (source_mode, operator, rail, value) in enumerate(components, start=2):
        common = {
            "source_row_number": row_number, "month": month,
            "source_mode": source_mode, "operator_code": operator, "rail_category": rail,
            "source_indicator": "", "measurement_basis": "estimated" if operator == "RMB" else "reported",
            "includes_estimates": int(operator == "RMB"),
        }
        passenger_rows.append({
            **common, "source_record_id": f"td_table21:{row_number}", "source_id": "td_table21",
            "franchise_type": "", "passenger_journeys_thousands": value, "source_numeric_text": str(value),
        })
        daily_rows.append({
            **common, "source_record_id": f"td_table21s:{row_number}", "source_id": "td_table21s",
            "average_daily_journeys_thousands": value / 29, "source_numeric_text": str(value / 29),
        })
    selectors = {"GMB": [2], "RMB": [3], "PLB": [2, 3], "MTR": [4, 5, 6], "FRANCHISED_BUS": [7]}
    passenger_facts = []
    daily_facts = []
    passenger_lineage = []
    daily_lineage = []
    for mode, basis, estimated in definitions:
        selected = selectors[mode]
        value = sum(passenger_rows[row_number - 2]["passenger_journeys_thousands"] for row_number in selected)
        common = {
            "month": month, "mode": mode, "measurement_basis": basis, "includes_estimates": estimated,
            "is_derived": int(mode in {"PLB", "MTR", "FRANCHISED_BUS"}), "source_indicator": "",
            "is_provisional": 0, "is_revised": 0, "component_count": len(selected),
        }
        passenger_facts.append({
            **common, "passenger_journeys_thousands": value, "unit": "thousand_journeys", "source_id": "td_table21",
        })
        daily_facts.append({
            **common, "average_daily_journeys_thousands": value / 29,
            "unit": "thousand_journeys_per_day", "source_id": "td_table21s",
        })
        passenger_lineage.extend(
            {"month": month, "mode": mode, "source_record_id": f"td_table21:{row_number}"}
            for row_number in selected
        )
        daily_lineage.extend(
            {"month": month, "mode": mode, "source_record_id": f"td_table21s:{row_number}"}
            for row_number in selected
        )
    fleet = [
        {
            "month": month, "mode": mode, "licensed_vehicles": 10, "passenger_capacity": 160,
            "vehicle_km_thousands": 20.0 if mode == "GMB" else pd.NA,
            "cross_harbour_vehicle_km_thousands": pd.NA,
            "fleet_unit": "vehicles", "capacity_unit": "passenger_places", "km_unit": "thousand_vehicle_km",
            "measurement_basis": "reported", "source_id": "td_table22",
            "source_record_id": f"td_table22:{row_number}", "source_row_number": row_number,
            "source_fleet_text": "10", "source_capacity_text": "160",
            "source_km_text": "20.0" if mode == "GMB" else "", "source_cross_harbour_km_text": "",
            "fleet_indicator": "", "capacity_indicator": "", "km_indicator": "",
            "cross_harbour_km_indicator": "", "is_provisional": 0, "is_revised": 0,
        }
        for row_number, mode in enumerate(("GMB", "RMB"), start=2)
    ]
    return {
        "frames": {
            "passenger_source_records": pd.DataFrame(passenger_rows),
            "daily_source_records": pd.DataFrame(daily_rows),
            "monthly_passenger_journeys": pd.DataFrame(passenger_facts),
            "monthly_average_daily_journeys": pd.DataFrame(daily_facts),
            "monthly_minibus_fleet": pd.DataFrame(fleet),
            "passenger_lineage": pd.DataFrame(passenger_lineage),
            "daily_lineage": pd.DataFrame(daily_lineage),
        },
        "source_files": sources, "transport_modes": modes,
        "checks": [{"check_id": "fixture", "status": "pass", "severity": "info",
                    "message": "Synthetic fixture only", "details": {"synthetic": True}}],
        "metadata": {"fixture": "synthetic"},
    }


@pytest.fixture
def database_path(tmp_path: Path, database_inputs: dict) -> Path:
    path = tmp_path / "test_transport.sqlite"
    write_database(path, **database_inputs)
    return path


def test_database_roundtrip_views_and_nullable_mileage(database_path: Path, database_inputs: dict) -> None:
    expected = {table: len(frame) for table, frame in database_inputs["frames"].items()}
    assert all(check["status"] == "pass" for check in inspect_database(database_path, expected))
    with sqlite3.connect(database_path) as connection:
        comparison = connection.execute("SELECT mode FROM v_monthly_comparison_group ORDER BY mode").fetchall()
        assert comparison == [("FRANCHISED_BUS",), ("MTR",), ("PLB",)]
        # Adding GMB/RMB would count the PLB components twice in a later denominator.
        assert connection.execute("SELECT SUM(passenger_journeys_thousands) FROM v_monthly_comparison_group").fetchone()[0] == 1972.0
        assert connection.execute("SELECT DISTINCT calendar_days FROM v_daily_reconciliation_inputs").fetchall() == [(29,)]
        assert connection.execute("SELECT COUNT(*) FROM v_monthly_minibus_fleet_context").fetchone()[0] == 2
        assert connection.execute("SELECT vehicle_km_thousands FROM monthly_minibus_fleet WHERE mode='RMB'").fetchone()[0] is None
        assert connection.execute("SELECT COUNT(*) FROM v_passenger_source_lineage WHERE mode='MTR'").fetchone()[0] == 3
        wide = connection.execute("SELECT gmb_journeys_thousands, rmb_journeys_thousands, plb_journeys_thousands FROM v_monthly_passenger_wide").fetchone()
        assert wide == (290.0, 145.0, 435.0)


@pytest.mark.parametrize(
    ("column", "value"),
    [("passenger_journeys_thousands", -1), ("passenger_journeys_thousands", "invalid"),
     ("component_count", 1.5), ("month", "2020-13-01"),
     ("month", "2020-02-29"), ("month", "2014-12-01"), ("unit", "journeys"),
     ("mode", "UNKNOWN"), ("measurement_basis", "estimated"), ("is_derived", 2)],
)
def test_fact_constraints(database_path: Path, column: str, value: object) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE monthly_passenger_journeys SET {column}=? WHERE mode='GMB'", (value,))


def test_unique_fact_and_source_keys(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO monthly_passenger_journeys SELECT * FROM monthly_passenger_journeys WHERE mode='GMB'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE passenger_source_records SET operator_code='GMB' WHERE operator_code='RMB'")


def test_lineage_rejects_wrong_month_and_unknown_source(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO passenger_lineage VALUES ('2020-03-01', 'GMB', 'td_table21:2')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO passenger_lineage VALUES ('2020-02-01', 'GMB', 'not_a_source')")


def test_inspector_reports_count_and_lineage_failures(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("DELETE FROM passenger_lineage WHERE mode='MTR' AND source_record_id='td_table21:4'")
    checks = {check["check_id"]: check for check in inspect_database(database_path, {"monthly_passenger_journeys": 10})}
    assert checks["sqlite_count_monthly_passenger_journeys"]["status"] == "fail"
    assert checks["sqlite_count_monthly_passenger_journeys"]["details"] == {"expected": 10, "actual": 5}
    assert checks["sqlite_passenger_lineage_counts"]["status"] == "fail"
    assert checks["sqlite_passenger_lineage_counts"]["details"][0]["mode"] == "MTR"


def test_loader_rollback_and_existing_database_protection(tmp_path: Path, database_inputs: dict) -> None:
    path = tmp_path / "rollback.sqlite"
    database_inputs["frames"]["monthly_passenger_journeys"].loc[0, "passenger_journeys_thousands"] = -1
    with pytest.raises(sqlite3.IntegrityError):
        write_database(path, **database_inputs)
    assert not path.exists()
    database_inputs["frames"]["monthly_passenger_journeys"].loc[0, "passenger_journeys_thousands"] = 290.0
    write_database(path, **database_inputs)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_database(path, **database_inputs)
    assert path.read_bytes() == before


def test_replace_validation_checks_is_atomic(database_path: Path) -> None:
    checks = [{"check_id": "updated", "status": "warning", "severity": "warning",
               "message": "Test warning", "details": {"count": 1}}]
    replace_validation_checks(database_path, checks)
    with sqlite3.connect(database_path) as connection:
        row = connection.execute("SELECT check_id, status, details_json FROM validation_checks").fetchone()
        assert row[:2] == ("updated", "warning")
        assert json.loads(row[2]) == {"count": 1}
    checks[0]["status"] = "not_a_status"
    with pytest.raises(sqlite3.IntegrityError):
        replace_validation_checks(database_path, checks)
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT status FROM validation_checks").fetchone()[0] == "warning"


def test_bad_frame_columns_fail_without_publishing(tmp_path: Path, database_inputs: dict) -> None:
    path = tmp_path / "bad_columns.sqlite"
    database_inputs["frames"]["monthly_passenger_journeys"] = database_inputs["frames"]["monthly_passenger_journeys"].drop(columns="unit")
    with pytest.raises(ValueError, match="DataFrame columns"):
        write_database(path, **database_inputs)
    assert not path.exists()
