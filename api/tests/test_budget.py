import unittest

from app.domain.budget import BudgetCategory, IncomeStream, monthlyize_amount, summarize_budget


class BudgetTests(unittest.TestCase):
    def test_monthlyize_amount_supports_actual_deposit_patterns(self):
        self.assertAlmostEqual(monthlyize_amount(2500, "mid_month"), 2500)
        self.assertAlmostEqual(monthlyize_amount(2500, "end_month"), 2500)
        self.assertAlmostEqual(monthlyize_amount(1800, "biweekly"), 3900)
        self.assertAlmostEqual(monthlyize_amount(12000, "annual"), 1000)

    def test_budget_summary_uses_income_streams_when_take_home_not_supplied(self):
        summary = summarize_budget(
            income_streams=[
                IncomeStream("Mid-month pay", 2500, "mid_month"),
                IncomeStream("End-month pay", 2500, "end_month"),
                IncomeStream("Side income", 600, "monthly"),
            ],
            fixed_expenses=[
                BudgetCategory("Rent", 1800),
                BudgetCategory("Groceries", 700),
            ],
            investments=[BudgetCategory("TSP", 500)],
            flexible_spending=[BudgetCategory("Restaurants", 400)],
        )

        self.assertEqual(summary.take_home_monthly, 5600)
        self.assertEqual(summary.fixed_total, 2500)
        self.assertEqual(summary.investments_total, 500)
        self.assertEqual(summary.flexible_total, 400)
        self.assertEqual(summary.surplus, 2200)
        self.assertEqual(summary.status, "surplus")
        self.assertEqual(summary.top_spending_categories[0].label, "Rent")
        self.assertEqual(summary.cash_flow[-1].group, "surplus")

    def test_budget_summary_flags_deficit(self):
        summary = summarize_budget(
            take_home_monthly=5000,
            fixed_expenses=[BudgetCategory("Housing", 3200)],
            investments=[BudgetCategory("TSP", 500)],
            flexible_spending=[BudgetCategory("Travel", 1600)],
        )

        self.assertEqual(summary.surplus, -300)
        self.assertEqual(summary.status, "deficit")
        self.assertEqual(summary.cash_flow[-1].group, "deficit")
        self.assertEqual(summary.cash_flow[-1].monthly_amount, 300)

    def test_budget_summary_ratios_match_take_home(self):
        summary = summarize_budget(
            take_home_monthly=6000,
            fixed_expenses=[BudgetCategory("Housing", 2400), BudgetCategory("Food", 800)],
            investments=[BudgetCategory("TSP", 600)],
            flexible_spending=[BudgetCategory("Fun", 1200)],
        )

        self.assertEqual(summary.fixed_ratio, 0.5333)
        self.assertEqual(summary.investments_ratio, 0.1)
        self.assertEqual(summary.flexible_ratio, 0.2)
        self.assertEqual(summary.surplus_ratio, 0.1667)


if __name__ == "__main__":
    unittest.main()
