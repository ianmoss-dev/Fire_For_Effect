import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


class RetirementApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_solve_savings_rate_endpoint(self):
        response = self.client.post(
            "/retirement/solve-savings-rate",
            json={
                "target_nest_egg": 100000,
                "current_tsp": 10000,
                "base_pay_schedule": [],
                "civilian_monthly": 0,
                "mil_months": 0,
                "total_months": 120,
                "allocation": {"C": 0.6, "S": 0.2, "I": 0.2},
                "inflation_rate": 0.025,
                "prebuilt_income_schedule": [5000] * 120,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreater(body["savings_rate"], 0)
        self.assertLess(body["savings_rate"], 1)
        self.assertAlmostEqual(body["final_projected_balance"], 100000, delta=0.01)
        self.assertEqual(len(body["contribution_schedule"]), 120)

    def test_solve_savings_rate_endpoint_validates_total_months(self):
        response = self.client.post(
            "/retirement/solve-savings-rate",
            json={
                "target_nest_egg": 100000,
                "current_tsp": 10000,
                "mil_months": 0,
                "total_months": 0,
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

