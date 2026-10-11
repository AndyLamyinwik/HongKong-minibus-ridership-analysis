"""Read-only analytical query contracts against the preserved Phase 2 database."""

from __future__ import annotations

import hashlib
import math
import sqlite3
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "transport.sqlite"
SQL_DIRECTORY = PROJECT_ROOT / "sql" / "analysis"
ALL_MODES = {"GMB", "RMB", "PLB", "MTR", "FRANCHISED_BUS"}
COMPARISON_MODES = ALL_MODES - {"PLB"}
CONTRACTS = {
    "annual_ridership": (55, [
        "year", "mode", "passenger_journeys_thousands", "absolute_yoy_change_thousands",
        "yoy_change_pct", "measurement_basis", "includes_estimates", "is_provisional", "is_revised",
    ]),
    "monthly_yoy": (660, [
        "month", "mode", "passenger_journeys_thousands", "prior_year_journeys_thousands",
        "absolute_yoy_change_thousands", "yoy_change_pct",
    ]),
    "annual_market_share": (44, [
        "year", "mode", "passenger_journeys_thousands", "comparison_group_journeys_thousands",
        "share_pct", "measurement_basis", "includes_estimates",
    ]),
    "monthly_market_share": (528, [
        "month", "mode", "passenger_journeys_thousands", "comparison_group_journeys_thousands",
        "share_pct", "measurement_basis", "includes_estimates",
    ]),
    "recovery_2019": (5, [
        "mode", "baseline_2019_journeys_thousands", "journeys_2025_thousands",
        "absolute_change_thousands", "recovery_pct", "change_pct",
        "measurement_basis", "includes_estimates",
    ]),
    "fleet_normalized": (264, [
        "month", "mode", "average_daily_journeys_thousands", "licensed_vehicles",
        "average_daily_journeys_per_licensed_vehicle", "measurement_basis", "includes_estimates",
    ]),
}


@pytest.fixture
def read_only_connection():
    """SQLite refuses file mutations; each test also closes its own connection."""
    connection = sqlite3.connect(DATABASE_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = ON")
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def execute_query(connection: sqlite3.Connection, name: str) -> list[sqlite3.Row]:
    return connection.execute((SQL_DIRECTORY / f"{name}.sql").read_text(encoding="utf-8")).fetchall()


def annual_source_totals(connection: sqlite3.Connection) -> dict[tuple[int, str], float]:
    """Independent Python reduction of monthly facts, rather than SQL aggregation."""
    groups: dict[tuple[int, str], list[float]] = {}
    for row in connection.execute(
        "SELECT month, mode, passenger_journeys_thousands FROM monthly_passenger_journeys"
    ):
        groups.setdefault((int(row["month"][:4]), row["mode"]), []).append(
            row["passenger_journeys_thousands"]
        )
    assert all(len(values) == 12 for values in groups.values())
    return {key: math.fsum(values) for key, values in groups.items()}


@pytest.mark.parametrize("name", list(CONTRACTS))
def test_query_shape_order_and_finite_values(read_only_connection, name: str) -> None:
    rows = execute_query(read_only_connection, name)
    count, columns = CONTRACTS[name]
    assert len(rows) == count
    assert rows[0].keys() == columns
    period = "year" if "year" in columns else "month" if "month" in columns else None
    keys = [(row[period], row["mode"]) if period else (row["mode"],) for row in rows]
    assert keys == sorted(keys)
    assert len(set(keys)) == len(keys)
    for row in rows:
        assert all(math.isfinite(value) for value in row if isinstance(value, (int, float)))


def test_annual_totals_growth_and_estimation_flags(read_only_connection) -> None:
    source = annual_source_totals(read_only_connection)
    rows = execute_query(read_only_connection, "annual_ridership")
    assert {row["mode"] for row in rows} == ALL_MODES
    for row in rows:
        year, mode = row["year"], row["mode"]
        current = source[(year, mode)]
        assert row["passenger_journeys_thousands"] == pytest.approx(current, abs=1e-8)
        if year == 2015:
            assert row["absolute_yoy_change_thousands"] is None
            assert row["yoy_change_pct"] is None
        else:
            previous = source[(year - 1, mode)]
            assert row["absolute_yoy_change_thousands"] == pytest.approx(current - previous, abs=1e-8)
            assert row["yoy_change_pct"] == pytest.approx((current / previous - 1) * 100, abs=1e-10)
        assert row["includes_estimates"] == int(mode in {"RMB", "PLB"})
        assert row["measurement_basis"] == (
            "estimated" if mode == "RMB" else "mixed" if mode == "PLB" else "reported"
        )
    for year in range(2015, 2026):
        assert source[(year, "PLB")] == pytest.approx(
            source[(year, "GMB")] + source[(year, "RMB")], abs=1e-8
        )


def test_monthly_yoy_uses_same_month_and_first_year_null(read_only_connection) -> None:
    source = {
        (row["month"], row["mode"]): row["passenger_journeys_thousands"]
        for row in read_only_connection.execute(
            "SELECT month, mode, passenger_journeys_thousands FROM monthly_passenger_journeys"
        )
    }
    rows = execute_query(read_only_connection, "monthly_yoy")
    for row in rows:
        month, mode = row["month"], row["mode"]
        if month.startswith("2015-"):
            assert all(row[key] is None for key in (
                "prior_year_journeys_thousands", "absolute_yoy_change_thousands", "yoy_change_pct"
            ))
        else:
            prior_month = f"{int(month[:4]) - 1}{month[4:]}"
            previous = source[(prior_month, mode)]
            current = source[(month, mode)]
            assert row["prior_year_journeys_thousands"] == previous
            assert row["absolute_yoy_change_thousands"] == pytest.approx(current - previous, abs=1e-8)
            assert row["yoy_change_pct"] == pytest.approx((current / previous - 1) * 100, abs=1e-10)
    assert sum(row["yoy_change_pct"] is None for row in rows) == 60


@pytest.mark.parametrize("name,period", [
    ("annual_market_share", "year"), ("monthly_market_share", "month"),
])
def test_market_share_denominator_has_no_overlapping_plb(read_only_connection, name, period) -> None:
    rows = execute_query(read_only_connection, name)
    groups: dict[object, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(row[period], []).append(row)
        assert row["includes_estimates"] == int(row["mode"] == "RMB")
    if period == "year":
        source = annual_source_totals(read_only_connection)
    else:
        source = {
            (row["month"], row["mode"]): row["passenger_journeys_thousands"]
            for row in read_only_connection.execute(
                "SELECT month, mode, passenger_journeys_thousands FROM monthly_passenger_journeys"
            )
        }
    for identifier, observations in groups.items():
        assert {row["mode"] for row in observations} == COMPARISON_MODES
        expected = math.fsum(source[(identifier, mode)] for mode in COMPARISON_MODES)
        equivalent = math.fsum(source[(identifier, mode)] for mode in ("PLB", "MTR", "FRANCHISED_BUS"))
        assert expected == pytest.approx(equivalent, abs=1e-8)
        for row in observations:
            assert row["comparison_group_journeys_thousands"] == pytest.approx(expected, abs=1e-8)
            assert row["share_pct"] == pytest.approx(
                source[(identifier, row["mode"])] / expected * 100, abs=1e-10
            )
        assert math.fsum(row["share_pct"] for row in observations) == pytest.approx(100.0, abs=1e-10)


def test_annual_share_is_ratio_of_totals_not_monthly_share_average(read_only_connection) -> None:
    totals = annual_source_totals(read_only_connection)
    for row in execute_query(read_only_connection, "annual_market_share"):
        year, mode = row["year"], row["mode"]
        denominator = math.fsum(totals[(year, item)] for item in COMPARISON_MODES)
        assert row["share_pct"] == pytest.approx(totals[(year, mode)] / denominator * 100, abs=1e-10)


def test_recovery_has_full_year_2019_baseline(read_only_connection) -> None:
    source = annual_source_totals(read_only_connection)
    for row in execute_query(read_only_connection, "recovery_2019"):
        mode = row["mode"]
        baseline = source[(2019, mode)]
        endpoint = source[(2025, mode)]
        assert row["baseline_2019_journeys_thousands"] == pytest.approx(baseline, abs=1e-8)
        assert row["journeys_2025_thousands"] == pytest.approx(endpoint, abs=1e-8)
        assert row["absolute_change_thousands"] == pytest.approx(endpoint - baseline, abs=1e-8)
        assert row["recovery_pct"] == pytest.approx(endpoint / baseline * 100, abs=1e-10)
        assert row["change_pct"] == pytest.approx(row["recovery_pct"] - 100, abs=1e-10)


def test_fleet_ratio_uses_daily_rate_and_individual_journey_scaling(read_only_connection) -> None:
    source = {
        (row["month"], row["mode"]): (row["average_daily_journeys_thousands"], row["licensed_vehicles"])
        for row in read_only_connection.execute(
            "SELECT d.month, d.mode, d.average_daily_journeys_thousands, f.licensed_vehicles "
            "FROM monthly_average_daily_journeys d JOIN monthly_minibus_fleet f "
            "ON d.month=f.month AND d.mode=f.mode"
        )
    }
    for row in execute_query(read_only_connection, "fleet_normalized"):
        daily, licensed = source[(row["month"], row["mode"])]
        assert row["average_daily_journeys_thousands"] == daily
        assert row["licensed_vehicles"] == licensed
        assert row["average_daily_journeys_per_licensed_vehicle"] == pytest.approx(
            daily * 1000 / licensed, abs=1e-10
        )
        assert row["includes_estimates"] == int(row["mode"] == "RMB")
        assert row["measurement_basis"] == ("estimated" if row["mode"] == "RMB" else "reported")


def test_all_queries_leave_database_bytes_unchanged(read_only_connection) -> None:
    before = hashlib.sha256(DATABASE_PATH.read_bytes()).hexdigest()
    for name in CONTRACTS:
        execute_query(read_only_connection, name)
    after = hashlib.sha256(DATABASE_PATH.read_bytes()).hexdigest()
    assert after == before
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        read_only_connection.execute("CREATE TABLE test_write_forbidden (id INTEGER)")
