import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_datasets import age_band, br_number, cache_fingerprint, nullable_boolean, survey_salary_bounds
from validate_package import exported_parquets


class PreparationRulesTests(unittest.TestCase):
    def test_nullable_boolean_preserves_false_and_missing(self):
        actual = nullable_boolean(pd.Series([True, False, "True", "False", "Sim", "Não", None]))
        self.assertEqual(actual.iloc[:6].tolist(), [True, False, True, False, True, False])
        self.assertTrue(pd.isna(actual.iloc[6]))
        self.assertEqual(str(actual.dtype), "boolean")
        with self.assertRaises(ValueError):
            nullable_boolean(pd.Series(["talvez"]))

    def test_brazilian_numbers_keep_zero_and_flag_invalid(self):
        result = br_number(pd.Series(["1.234,56", "1234.56", "0", "", "nao numerico"]))
        self.assertEqual(result.iloc[:3].tolist(), [1234.56, 1234.56, 0.0])
        self.assertTrue(result.iloc[3:].isna().all())

    def test_age_thresholds_do_not_relabel_invalid_ages(self):
        result = age_band(pd.Series([13, 14, 17, 18, 24, 25, 90, 91]))
        self.assertEqual(result.iloc[1:6].tolist(), ["14-17", "14-17", "18-24", "18-24", "25-34"])
        self.assertEqual(result.iloc[0], "Nao informado ou invalido")
        self.assertEqual(result.iloc[-1], "Nao informado ou invalido")

    def test_open_salary_interval_remains_open(self):
        lower, upper, exclusive = survey_salary_bounds("Acima de R$ 40.001/mês")
        self.assertEqual(lower, 40001)
        self.assertTrue(pd.isna(upper))
        self.assertFalse(exclusive)

    def test_cache_fingerprint_changes_with_source(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "source.bin"
            file.write_bytes(b"before")
            before = cache_fingerprint([file])
            file.write_bytes(b"after")
            self.assertNotEqual(before, cache_fingerprint([file]))

    def test_validation_does_not_treat_cache_as_final_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".cache").mkdir()
            (root / "tratados").mkdir()
            pd.DataFrame({"x": [1]}).to_parquet(root / ".cache/temporary.parquet")
            pd.DataFrame({"x": [1]}).to_parquet(root / "tratados/final.parquet")
            self.assertEqual(exported_parquets(root), [root / "tratados/final.parquet"])


if __name__ == "__main__":
    unittest.main()
