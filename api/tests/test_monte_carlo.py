import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.monte_carlo import run_monte_carlo, summarize_monte_carlo


class MonteCarloTests(unittest.TestCase):
    def test_monte_carlo_returns_expected_shape(self):
        results = run_monte_carlo(
            current_age=30,
            retire_age=35,
            initial_balance=10000,
            monthly_contribution=500,
            l_fund_weight=0,
            manual_allocation={"C": 0.6, "S": 0.2, "I": 0.2},
            trials=25,
            seed=123,
        )

        self.assertEqual(results.shape, (25, 61))
        self.assertTrue((results[:, 0] == 10000).all())

    def test_monte_carlo_seed_is_reproducible(self):
        first = run_monte_carlo(30, 31, 10000, 500, manual_allocation={"C": 1.0}, trials=5, seed=42)
        second = run_monte_carlo(30, 31, 10000, 500, manual_allocation={"C": 1.0}, trials=5, seed=42)

        self.assertTrue((first == second).all())

    def test_summary_returns_success_rate_and_yearly_points(self):
        results = run_monte_carlo(
            current_age=30,
            retire_age=35,
            initial_balance=10000,
            monthly_contribution=500,
            l_fund_weight=1.0,
            manual_allocation={},
            trials=100,
            seed=123,
        )
        summary = summarize_monte_carlo(results, target_balance=25000)

        self.assertEqual(summary.months, 60)
        self.assertEqual(summary.trials, 100)
        self.assertGreaterEqual(summary.success_rate, 0)
        self.assertLessEqual(summary.success_rate, 1)
        self.assertEqual(len(summary.yearly_points), 5)
        self.assertIn("p50", summary.yearly_points[0])


if __name__ == "__main__":
    unittest.main()

