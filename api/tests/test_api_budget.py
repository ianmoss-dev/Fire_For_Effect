import unittest

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class BudgetApiTests(unittest.TestCase):
    def test_budget_summary_endpoint(self):
        response = client.post(
            "/budget/summary",
            json={
                "income_streams": [
                    {"label": "Mid-month pay", "amount": 2500, "frequency": "mid_month"},
                    {"label": "End-month pay", "amount": 2500, "frequency": "end_month"},
                ],
                "fixed_expenses": [
                    {"label": "Rent", "amount": 1800},
                    {"label": "Groceries", "amount": 650},
                ],
                "investments": [{"label": "TSP", "amount": 500}],
                "flexible_spending": [{"label": "Restaurants", "amount": 350}],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["take_home_monthly"], 5000)
        self.assertEqual(body["fixed_total"], 2450)
        self.assertEqual(body["surplus"], 1700)
        self.assertEqual(body["cash_flow"][-1]["group"], "surplus")

    def test_budget_summary_endpoint_validates_negative_category(self):
        response = client.post(
            "/budget/summary",
            json={
                "take_home_monthly": 5000,
                "fixed_expenses": [{"label": "Rent", "amount": -1}],
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
