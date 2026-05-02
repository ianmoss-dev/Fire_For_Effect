import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.loaders import load_military_data
from app.domain.income import calculate_income


class IncomeCalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_military_data()

    def test_conus_income_uses_base_bas_and_bah(self):
        result = calculate_income(
            rank="E-5",
            tis=6,
            has_dependents=True,
            zip_code="28310",
            data=self.data,
        )

        self.assertFalse(result.is_oconus)
        self.assertEqual(result.base_pay, 4110.0)
        self.assertEqual(result.bas, 515.0)
        self.assertEqual(result.bah, 1806.0)
        self.assertEqual(result.housing_total, 1806.0)
        self.assertEqual(result.housing_label, "BAH")
        self.assertEqual(result.taxable_pay, 4110.0)
        self.assertEqual(result.nontaxable_pay, 2321.0)
        self.assertEqual(result.gross_monthly, 6431.0)
        self.assertEqual(result.mha, "NC182")

    def test_oconus_income_uses_oha_utility_and_cola(self):
        result = calculate_income(
            rank="E-5",
            tis=6,
            has_dependents=True,
            is_oconus=True,
            oha_location="Germany - Grafenwohr / Vilseck",
            cola=100,
            special_pay=150,
            data=self.data,
        )

        self.assertTrue(result.is_oconus)
        self.assertEqual(result.base_pay, 4110.0)
        self.assertEqual(result.bas, 515.0)
        self.assertEqual(result.bah, 0.0)
        self.assertEqual(result.oha_rental, 1600.0)
        self.assertEqual(result.oha_utility, 440.0)
        self.assertEqual(result.housing_total, 2040.0)
        self.assertEqual(result.housing_label, "OHA + Utility")
        self.assertEqual(result.taxable_pay, 4260.0)
        self.assertEqual(result.nontaxable_pay, 2655.0)
        self.assertEqual(result.gross_monthly, 6915.0)
        self.assertIsNone(result.mha)

    def test_conus_unknown_zip_keeps_pay_without_bah(self):
        result = calculate_income(
            rank="O-3",
            tis=8,
            has_dependents=True,
            zip_code="00000",
            data=self.data,
        )

        self.assertEqual(result.base_pay, 8125.5)
        self.assertEqual(result.bas, 360.0)
        self.assertEqual(result.bah, 0.0)
        self.assertEqual(result.housing_total, 0.0)
        self.assertEqual(result.gross_monthly, 8485.5)
        self.assertIsNone(result.mha)


if __name__ == "__main__":
    unittest.main()

