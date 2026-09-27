"""Generation guarantees and explicit negative tests for every validation rule."""

import unittest

import pandas as pd

from src.data_quality import EXPECTED_SCHEMA, RANGES, validate_data
from src.generate_data import ROW_COUNT, generate_data


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate_data()

    def assert_rejected_for(self, data, check_name, expected_rows=ROW_COUNT):
        """Confirm invalid data fails for the intended named validation check."""
        with self.assertRaisesRegex(ValueError, check_name):
            validate_data(data, expected_rows=expected_rows)

    def test_reproducibility(self):
        pd.testing.assert_frame_equal(self.data, generate_data())
        self.assertFalse(self.data.equals(generate_data(seed=43)))

    def test_valid_data_passes_exact_schema(self):
        self.assertEqual(list(self.data.columns), EXPECTED_SCHEMA)
        self.assertEqual(len(self.data), ROW_COUNT)
        self.assertTrue(all(validate_data(self.data).values()))

    def test_ranges_unit_balance_and_severe_tail(self):
        for column, (low, high) in RANGES.items():
            self.assertTrue(self.data[column].between(low, high).all(), column)
        totals = self.data[
            ["yield_percent", "defect_rate_percent", "other_loss_percent"]
        ].sum(axis=1)
        self.assertTrue(totals.sub(100).abs().lt(1e-8).all())
        self.assertLess(self.data.defect_rate_percent.max(), 60)
        self.assertGreater(self.data.defect_rate_percent.max(), 35)

    def test_missing_column_is_rejected(self):
        self.assert_rejected_for(self.data.drop(columns="batch_id"), "exact_schema")

    def test_unexpected_column_is_rejected(self):
        self.assert_rejected_for(
            self.data.assign(unexpected_measurement=1), "exact_schema"
        )

    def test_column_order_is_rejected(self):
        reordered = ["timestamp", "batch_id", *EXPECTED_SCHEMA[2:]]
        self.assert_rejected_for(self.data[reordered], "exact_schema")

    def test_nonsequential_batch_ids_are_rejected(self):
        bad = self.data.copy()
        bad.loc[100, "batch_id"] = "B00999"
        self.assert_rejected_for(bad, "sequential_batch_ids")

    def test_wrong_timestamp_start_is_rejected(self):
        bad = self.data.copy()
        bad["timestamp"] = bad.timestamp + pd.Timedelta(minutes=30)
        self.assert_rejected_for(bad, "timestamp_start")

    def test_wrong_timestamp_cadence_is_rejected(self):
        bad = self.data.copy()
        bad.loc[10, "timestamp"] += pd.Timedelta(minutes=5)
        self.assert_rejected_for(bad, "timestamp_cadence")

    def test_nonincreasing_timestamps_are_rejected(self):
        bad = self.data.copy()
        bad.loc[10, "timestamp"] = bad.loc[9, "timestamp"]
        self.assert_rejected_for(bad, "timestamps_strictly_increasing")

    def test_wrong_timestamp_dtype_is_rejected(self):
        bad = self.data.copy()
        bad["timestamp"] = bad.timestamp.astype(str)
        self.assert_rejected_for(bad, "timestamp_dtype")

    def test_wrong_string_dtype_is_rejected(self):
        bad = self.data.copy()
        bad["machine_id"] = bad.machine_id.map({"M1": 1, "M2": 2, "M3": 3})
        self.assert_rejected_for(bad, "string_dtypes")

    def test_wrong_numeric_dtype_is_rejected(self):
        bad = self.data.copy()
        bad["temperature_C"] = bad.temperature_C.astype(str)
        self.assert_rejected_for(bad, "numeric_dtypes")

    def test_missing_values_are_rejected(self):
        bad = self.data.copy()
        bad.loc[0, "pressure_MPa"] = float("nan")
        self.assert_rejected_for(bad, "no_missing_values")

    def test_duplicate_rows_are_rejected(self):
        bad = pd.concat([self.data, self.data.iloc[[0]]], ignore_index=True)
        self.assert_rejected_for(bad, "no_duplicate_rows", expected_rows=ROW_COUNT + 1)

    def test_invalid_ranges_and_categories_are_rejected(self):
        cases = [
            ("energy_kWh", -1, "energy_kWh_range"),
            ("yield_percent", 101, "yield_percent_range"),
            ("material_type", "unknown", "valid_materials"),
            ("machine_id", "unknown", "valid_machines"),
            ("data_origin", "real_data", "synthetic_label"),
        ]
        for column, value, check_name in cases:
            with self.subTest(column=column):
                bad = self.data.copy()
                bad.loc[0, column] = value
                self.assert_rejected_for(bad, check_name)

    def test_broken_unit_balance_is_rejected(self):
        bad = self.data.copy()
        bad.loc[0, "other_loss_percent"] += 0.1
        self.assert_rejected_for(bad, "unit_balance")


if __name__ == "__main__":
    unittest.main()
