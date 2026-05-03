import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.loaders import load_military_data
from app.domain.pension import calc_high3_pension, calc_pension_apv


class PensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_military_data()

    def test_enlisted_legacy_high3_pension_at_20_years(self):
        pension = calc_high3_pension("E-7", 20, 0.025, self.data)

        self.assertAlmostEqual(pension, 2965.5, places=2)

    def test_officer_brs_high3_pension_at_20_years(self):
        pension = calc_high3_pension("O-5", 20, 0.02, self.data)

        self.assertAlmostEqual(pension, 4642.52, places=2)

    def test_warrant_high3_pension_at_22_years(self):
        pension = calc_high3_pension("W-4", 22, 0.025, self.data)

        self.assertGreater(pension, 0)

    def test_pension_apv_is_higher_for_female_life_table(self):
        male_apv = calc_pension_apv(60000, 45, sex="male")
        female_apv = calc_pension_apv(60000, 45, sex="female")

        self.assertGreater(male_apv, 1_000_000)
        self.assertGreater(female_apv, male_apv)

    def test_pension_apv_decreases_with_later_start_age(self):
        early_apv = calc_pension_apv(60000, 45, sex="male")
        later_apv = calc_pension_apv(60000, 65, sex="male")

        self.assertGreater(early_apv, later_apv)


if __name__ == "__main__":
    unittest.main()
