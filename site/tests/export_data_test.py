"""Failure-path checks for the static export, using isolated input copies only."""

from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export_data.py"
SPEC = importlib.util.spec_from_file_location("research_static_export", SCRIPT)
EXPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORT)


class ExportContractTests(unittest.TestCase):
    def setUp(self):
        qa = EXPORT.ROOT / ".portfolio-qa"
        qa.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="export-contract-", dir=qa)
        self.root = Path(self.temporary.name).resolve()
        self.assertTrue(self.root.is_relative_to(qa.resolve()))
        for filename in EXPORT.INPUTS:
            destination = self.root / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(EXPORT.ROOT / filename, destination)

    def tearDown(self):
        self.assertTrue(self.root.is_relative_to((EXPORT.ROOT / ".portfolio-qa").resolve()))
        self.temporary.cleanup()

    def change_csv(self, filename, change, folder="analysis/outputs"):
        path = self.root / folder / filename
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            headers, rows = reader.fieldnames, list(reader)
        change(rows)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def test_valid_copy_exports_identical_bytes(self):
        self.assertEqual(EXPORT.render_export(EXPORT.build_export(self.root)),
                         EXPORT.render_export(EXPORT.build_export(EXPORT.ROOT)))

    def test_incomplete_component_shares_are_rejected(self):
        self.change_csv("annual_market_share.csv", lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, "four exclusive components"):
            EXPORT.build_export(self.root)

    def test_duplicate_component_share_is_rejected(self):
        self.change_csv("annual_market_share.csv", lambda rows: rows.append(dict(rows[0])))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            EXPORT.build_export(self.root)

    def test_plb_cannot_be_a_fifth_denominator_component(self):
        self.change_csv("annual_market_share.csv", lambda rows: rows.append({**rows[0], "mode": "PLB"}))
        with self.assertRaisesRegex(ValueError, "four exclusive components"):
            EXPORT.build_export(self.root)

    def test_zero_comparison_group_denominator_is_rejected(self):
        self.change_csv("annual_market_share.csv", lambda rows: next(row for row in rows if row["mode"] == "GMB").update(comparison_group_journeys_thousands="0"))
        with self.assertRaisesRegex(ValueError, "denominator must be positive"):
            EXPORT.build_export(self.root)

    def test_nonfinite_component_share_is_rejected(self):
        self.change_csv("annual_market_share.csv", lambda rows: rows[0].update(share_pct="NaN"))
        with self.assertRaisesRegex(ValueError, "finite value"):
            EXPORT.build_export(self.root)

    def test_wrong_stored_share_is_rejected(self):
        self.change_csv("annual_market_share.csv", lambda rows: rows[0].update(share_pct="50"))
        with self.assertRaisesRegex(ValueError, "Preserved annual share"):
            EXPORT.build_export(self.root)

    def test_rmb_recovery_cannot_be_mislabeled_reported(self):
        self.change_csv("recovery_2019.csv", lambda rows: next(row for row in rows if row["mode"] == "RMB").update(measurement_basis="reported", includes_estimates="0"))
        with self.assertRaisesRegex(ValueError, "Recovery estimation metadata"):
            EXPORT.build_export(self.root)

    def test_wrong_december_licensed_stock_is_rejected(self):
        self.change_csv("annual_fleet.csv", lambda rows: rows[0].update(december_licensed_vehicles="3204"))
        with self.assertRaisesRegex(ValueError, "reported December observation"):
            EXPORT.build_export(self.root)

    def test_wrong_vehicle_days_denominator_is_rejected(self):
        self.change_csv("annual_fleet.csv", lambda rows: rows[0].update(licensed_vehicle_days_proxy="1158128"))
        with self.assertRaisesRegex(ValueError, "day-weighted month-end stocks"):
            EXPORT.build_export(self.root)

    def test_december_only_proxy_is_rejected(self):
        def replace_proxy(rows):
            row = rows[0]
            wrong = float(row["annual_passenger_journeys_thousands"]) * 1000 / (int(row["calendar_days"]) * int(row["december_licensed_vehicles"]))
            row["average_daily_journeys_per_licensed_vehicle"] = str(wrong)
        self.change_csv("annual_fleet.csv", replace_proxy)
        with self.assertRaisesRegex(ValueError, "Existing annual fleet-normalized proxy"):
            EXPORT.build_export(self.root)

    def test_leap_year_day_count_cannot_be_replaced_by_365(self):
        self.change_csv("annual_fleet.csv", lambda rows: next(row for row in rows if row["year"] == "2024").update(calendar_days="365"))
        with self.assertRaisesRegex(ValueError, "complete calendar year"):
            EXPORT.build_export(self.root)

    def test_missing_monthly_stock_prevents_proxy_export(self):
        self.change_csv("monthly_minibus_fleet.csv", lambda rows: rows.pop(), folder="data/processed")
        with self.assertRaisesRegex(ValueError, "132 complete months"):
            EXPORT.build_export(self.root)

    def test_licensed_stock_cannot_inherit_rmb_passenger_estimation(self):
        self.change_csv("monthly_minibus_fleet.csv", lambda rows: next(row for row in rows if row["mode"] == "RMB").update(measurement_basis="estimated"), folder="data/processed")
        with self.assertRaisesRegex(ValueError, "reported administrative stock"):
            EXPORT.build_export(self.root)

    def test_check_rejects_stale_json_without_writing(self):
        destination = self.root / "site/public/data/research.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        stale = b'{"stale":true}\n'
        destination.write_bytes(stale)
        with patch.object(EXPORT, "DESTINATION", destination), patch.object(sys, "argv", ["export_data.py", "--check"]), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(EXPORT.main(), 1)
        self.assertEqual(destination.read_bytes(), stale)

    def test_check_rejects_missing_json_without_creating_a_file(self):
        destination = self.root / "site/public/data/research.json"
        with patch.object(EXPORT, "DESTINATION", destination), patch.object(sys, "argv", ["export_data.py", "--check"]), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(EXPORT.main(), 1)
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
