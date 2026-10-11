"""Explicit scope, units, source contracts, and transport definitions."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
START_MONTH = "2015-01-01"
END_MONTH = "2025-12-01"
MONTH_COUNT = 132
MONTHLY_UNIT = "thousand_journeys"
DAILY_UNIT = "thousand_journeys_per_day"
# Strict CSV arithmetic tolerance: 0.0001 passenger journeys, below the
# monthly CSV's finest reported quantum of 0.001 thousand (= one journey).
DAILY_TOLERANCE_THOUSANDS = 1e-7
SOURCE_BASE = "https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/"

HEADERS = {
    "td_table21": ["YR_MTH", "MODE", "TTD_PTO_CODE", "FRANCHISE_TYPE", "RAIL_LINE", "PAX", "PAX_INDI"],
    "td_table21s": ["YR_MTH", "MODE", "TTD_PTO_CODE", "RAIL_LINE", "AVG_DAILY_PAX", "AVG_DAILY_PAX_INDI"],
    "td_table22": ["YR_MTH", "MODE", "TTD_PTO_CODE", "FRANCHISE_TYPE", "RAIL_LINE", "BUS_TYPE_CODE", "KM", "KM_INDI", "KM_CROSS_HARBOUR", "KM_CROSS_HARBOUR_INDI", "NO_FLEET", "NO_FLEET_INDI", "PAX_CAP", "PAX_CAP_INDI"],
    "td_revision": ["DATA_REVISION_DATE"],
}
SOURCE_KEYS = {
    "td_table21": ["YR_MTH", "MODE", "TTD_PTO_CODE", "FRANCHISE_TYPE", "RAIL_LINE"],
    "td_table21s": ["YR_MTH", "MODE", "TTD_PTO_CODE", "RAIL_LINE"],
    "td_table22": ["YR_MTH", "MODE", "TTD_PTO_CODE", "FRANCHISE_TYPE", "RAIL_LINE", "BUS_TYPE_CODE"],
}
NUMERIC_FIELDS = {
    "td_table21": ["PAX"],
    "td_table21s": ["AVG_DAILY_PAX"],
    "td_table22": ["KM", "KM_CROSS_HARBOUR", "NO_FLEET", "PAX_CAP"],
}
RAIL_CATEGORIES = {"Local", "Airport", "LRT"}
BUS_OPERATORS = {"KMB", "CTB", "NWFB", "LWB", "NLB"}
MODES = [
    {"mode": "GMB", "label": "Green Minibus", "measurement_basis": "reported", "includes_estimates": 0, "definition": "Published GMB operator statistics; collection protocol not audited for every year."},
    {"mode": "RMB", "label": "Red Minibus", "measurement_basis": "estimated", "includes_estimates": 1, "definition": "TD survey-based estimates using licensed RMB counts and other parameters; no regular operator returns."},
    {"mode": "PLB", "label": "Total Public Light Bus", "measurement_basis": "mixed", "includes_estimates": 1, "definition": "GMB plus RMB; includes an estimated component and must not be double-counted with its components."},
    {"mode": "MTR", "label": "MTR railway services", "measurement_basis": "reported", "includes_estimates": 0, "definition": "MTRC Local (MTR Lines, including cross-boundary services), Airport Express and Light Rail; excludes Tramways and MTR buses."},
    {"mode": "FRANCHISED_BUS", "label": "Franchised buses", "measurement_basis": "reported", "includes_estimates": 0, "definition": "Contemporaneous KMB, CTB franchises, NWFB, LWB and NLB; excludes residents' services and MTR buses."},
]
MODE_LOOKUP = {item["mode"]: item for item in MODES}
