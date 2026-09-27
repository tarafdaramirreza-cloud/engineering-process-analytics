"""Basic generation guarantees and validation failure cases."""

import unittest
import pandas as pd
from src.generate_data import generate_data, ROW_COUNT
from src.data_quality import validate_data, REQUIRED, RANGES


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate_data()

    def test_reproducibility(self):
        pd.testing.assert_frame_equal(self.data, generate_data())
        self.assertFalse(self.data.equals(generate_data(seed=43)))

    def test_schema_and_count(self):
        self.assertEqual(len(self.data), ROW_COUNT)
        self.assertTrue(set(REQUIRED).issubset(self.data.columns))
        self.assertTrue(all(validate_data(self.data).values()))

    def test_ranges_and_balance(self):
        for column, (low, high) in RANGES.items():
            self.assertTrue(self.data[column].between(low, high).all(), column)
            self.assertTrue(self.data[column].ge(0).all(), column)
        totals = self.data[["yield_percent", "defect_rate_percent", "other_loss_percent"]].sum(axis=1)
        self.assertTrue(totals.sub(100).abs().lt(1e-8).all())

    def test_bad_data_rejected(self):
        for column, value in [("energy_kWh", -1), ("pressure_MPa", float("nan")),
                              ("material_type", "unknown"), ("yield_percent", 101)]:
            with self.subTest(column=column):
                bad = self.data.copy()
                bad.loc[0, column] = value
                with self.assertRaises(ValueError):
                    validate_data(bad)
        with self.assertRaises(ValueError):
            validate_data(self.data.drop(columns="batch_id"))
        with self.assertRaises(ValueError):
            validate_data(pd.concat([self.data, self.data.iloc[[0]]]), ROW_COUNT + 1)


if __name__ == "__main__":
    unittest.main()
