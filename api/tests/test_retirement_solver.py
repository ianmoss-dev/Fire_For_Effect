import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.retirement_solver import build_monthly_real_rates, project_balance, solve_savings_rate


class RetirementSolverTests(unittest.TestCase):
    def test_monthly_real_rates_are_generated_for_full_horizon(self):
        rates = build_monthly_real_rates(120, {"C": 0.6, "S": 0.2, "I": 0.2}, 0.025)

        self.assertEqual(len(rates), 120)
        self.assertTrue(all(rate > 0 for rate in rates))

    def test_solve_savings_rate_reaches_target(self):
        total_months = 120
        income_schedule = [5000] * total_months
        target = 100000
        current_tsp = 10000
        allocation = {"C": 0.6, "S": 0.2, "I": 0.2}

        percent, contribution_schedule = solve_savings_rate(
            target_nest_egg=target,
            current_tsp=current_tsp,
            base_pay_schedule=[],
            civilian_monthly=0,
            mil_months=0,
            total_months=total_months,
            allocation=allocation,
            inflation_rate=0.025,
            prebuilt_income_schedule=income_schedule,
        )
        final_balance = project_balance(
            current_tsp,
            contribution_schedule,
            build_monthly_real_rates(total_months, allocation, 0.025),
        )

        self.assertGreater(percent, 0)
        self.assertLess(percent, 1)
        self.assertAlmostEqual(final_balance, target, delta=0.01)

    def test_lifecycle_allocation_solver_returns_schedule(self):
        percent, contribution_schedule = solve_savings_rate(
            target_nest_egg=250000,
            current_tsp=20000,
            base_pay_schedule=[4500] * 120,
            civilian_monthly=6000,
            mil_months=120,
            total_months=240,
            allocation={"L": 1.0},
            inflation_rate=0.025,
        )

        self.assertEqual(len(contribution_schedule), 240)
        self.assertGreater(percent, 0)
        self.assertGreater(contribution_schedule[0], 0)


if __name__ == "__main__":
    unittest.main()

