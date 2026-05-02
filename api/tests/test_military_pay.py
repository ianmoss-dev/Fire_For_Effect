import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.loaders import load_military_data
from app.domain.military_pay import calculate_military_pay, get_base_pay, get_bah, get_bas


class MilitaryPayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_military_data()

    def test_enlisted_conus_with_dependents(self):
        result = calculate_military_pay("E-5", 6, "28310", True, self.data)

        self.assertEqual(result.base_pay, 4110.0)
        self.assertEqual(result.bas, 515.0)
        self.assertEqual(result.bah, 1806.0)
        self.assertEqual(result.mha, "NC182")
        self.assertEqual(result.location_name, "FORT BRAGG/POPE, NC")

    def test_officer_conus_with_dependents(self):
        result = calculate_military_pay("O-3", 8, "92135", True, self.data)

        self.assertEqual(result.base_pay, 8125.5)
        self.assertEqual(result.bas, 360.0)
        self.assertEqual(result.bah, 4518.0)
        self.assertEqual(result.mha, "CA038")
        self.assertEqual(result.location_name, "SAN DIEGO, CA")

    def test_enlisted_conus_without_dependents(self):
        result = calculate_military_pay("E-7", 14, "98433", False, self.data)

        self.assertEqual(result.base_pay, 5657.4)
        self.assertEqual(result.bas, 515.0)
        self.assertEqual(result.bah, 2376.0)
        self.assertEqual(result.mha, "WA311")

    def test_base_pay_snaps_down_to_available_tis_bracket(self):
        self.assertEqual(get_base_pay("E-5", 7, self.data), 4110.0)
        self.assertEqual(get_base_pay("E-5", 8, self.data), 4299.9)

    def test_bah_returns_zero_for_unknown_zip(self):
        bah, mha, location_name = get_bah("E-5", "00000", True, self.data)

        self.assertEqual(bah, 0.0)
        self.assertIsNone(mha)
        self.assertIsNone(location_name)

    def test_bas_uses_officer_rate_for_warrants(self):
        self.assertEqual(get_bas("W-2"), 360.0)
        self.assertEqual(get_bas("O-2"), 360.0)
        self.assertEqual(get_bas("E-6"), 515.0)


if __name__ == "__main__":
    unittest.main()

