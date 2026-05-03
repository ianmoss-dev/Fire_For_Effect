import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.investment import (
    FUND_MONTHLY_PARAMS,
    FUND_NOMINAL_RATES,
    FUND_STATS,
    get_blended_nominal_return,
    get_lifecycle_allocation,
)


class InvestmentTests(unittest.TestCase):
    def test_fund_stats_match_legacy_constants(self):
        self.assertEqual(FUND_STATS["C"]["geo_mean"], 0.107)
        self.assertEqual(FUND_STATS["S"]["sigma"], 0.202)
        self.assertEqual(FUND_NOMINAL_RATES["G"], 0.047)

    def test_monthly_params_are_available_for_each_fund(self):
        self.assertEqual(set(FUND_MONTHLY_PARAMS), {"C", "S", "I", "F", "G"})
        c_mean, c_sigma = FUND_MONTHLY_PARAMS["C"]

        self.assertGreater(c_mean, 0)
        self.assertGreater(c_sigma, 0)

    def test_lifecycle_allocation_bands(self):
        self.assertEqual(get_lifecycle_allocation(25), {"C": 0.50, "S": 0.25, "I": 0.25, "F": 0.0, "G": 0.0})
        self.assertEqual(get_lifecycle_allocation(15), {"C": 0.40, "S": 0.15, "I": 0.15, "F": 0.2, "G": 0.1})
        self.assertEqual(get_lifecycle_allocation(5), {"C": 0.20, "S": 0.05, "I": 0.05, "F": 0.3, "G": 0.4})
        self.assertEqual(get_lifecycle_allocation(0), {"C": 0.0, "S": 0.0, "I": 0.0, "F": 0.3, "G": 0.7})

    def test_blended_return_for_manual_allocation(self):
        result = get_blended_nominal_return({"C": 0.6, "S": 0.2, "I": 0.2}, 30)

        self.assertAlmostEqual(result, 0.0976, places=4)

    def test_blended_return_expands_lifecycle_allocation(self):
        result = get_blended_nominal_return({"L": 1.0}, 25)

        self.assertAlmostEqual(result, 0.09525, places=5)


if __name__ == "__main__":
    unittest.main()

