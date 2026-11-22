import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from telemetry_capstone import (
    convert_pressure,
    convert_temperature,
    parse_record,
    process_lines,
    summarize_by_well,
    run,
)

class TestConversions(unittest.TestCase):
    def test_pressure_psi_to_kpa(self):
        self.assertAlmostEqual(convert_pressure(100, "psi"), 689.48, places=2)

    def test_pressure_kpa_stays(self):
        self.assertEqual(convert_pressure(500, "kPa"), 500)

    def test_pressure_bar_rejected(self):
        with self.assertRaises(ValueError):
            convert_pressure(1, "bar")

    def test_temperature_f_to_c(self):
        self.assertAlmostEqual(convert_temperature(212, "F"), 100.0)

    def test_temperature_c_stays(self):
        self.assertEqual(convert_temperature(25, "C"), 25)

class TestParseRecord(unittest.TestCase):
    def test_valid_record(self):
        rec = parse_record("2026-01-01T00:00:00|WELL-1|100|psi|212|F|ACTIVE")
        self.assertEqual(rec["pressure_kpa"], 689.48)
        self.assertEqual(rec["temperature_c"], 100.0)

    def test_wrong_field_count(self):
        with self.assertRaises(ValueError):
            parse_record("2026-01-01|WELL-1|100|psi")

    def test_negative_pressure_rejected(self):
        with self.assertRaises(ValueError):
            parse_record("2026-01-01|WELL-1|-5|psi|50|C|ACTIVE")

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            parse_record("2026-01-01|WELL-1|100|psi|50|C|UNKNOWN")

class TestFilteringAndSummary(unittest.TestCase):
    def test_process_lines_keeps_line_numbers(self):
        lines = [
            "2026-01-01|WELL-1|100|psi|50|C|ACTIVE\n",
            "\n",
            "bad line\n",
            "2026-01-01|WELL-1|100|psi|50|C|ACTIVE\n",
        ]
        accepted, rejected = process_lines(lines)
        self.assertEqual(len(accepted), 2)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["line_number"], 3)

    def test_summary_only_active(self):
        records = [
            {"well_id": "WELL-1", "pressure_kpa": 100, "status": "ACTIVE"},
            {"well_id": "WELL-1", "pressure_kpa": 200, "status": "ACTIVE"},
            {"well_id": "WELL-1", "pressure_kpa": 9999, "status": "INACTIVE"},
        ]
        summary = summarize_by_well(records)
        self.assertEqual(summary[0]["active_readings"], 2)
        self.assertEqual(summary[0]["avg_pressure_kpa"], 150.0)

class TestEndToEnd(unittest.TestCase):
    def test_run_creates_three_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "in.txt")
            out_dir = os.path.join(tmp, "outputs")
            with open(input_path, "w") as f:
                f.write("2026-01-01|WELL-1|100|psi|212|F|ACTIVE\n")
                f.write("bad line\n")
            accepted, rejected, summary = run(input_path, out_dir)
            self.assertEqual(len(accepted), 1)
            self.assertEqual(len(rejected), 1)
            self.assertTrue(os.path.exists(os.path.join(out_dir, "cleaned_telemetry.csv")))
            self.assertTrue(os.path.exists(os.path.join(out_dir, "rejected_records.csv")))
            self.assertTrue(os.path.exists(os.path.join(out_dir, "well_summary.csv")))

if __name__ == "__main__":
    unittest.main()       