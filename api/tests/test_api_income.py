import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


class IncomeApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_conus_income_endpoint(self):
        response = self.client.post(
            "/income/calculate",
            json={
                "rank": "E-5",
                "tis": 6,
                "has_dependents": True,
                "zip_code": "28310",
                "is_oconus": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["base_pay"], 4110.0)
        self.assertEqual(body["bas"], 515.0)
        self.assertEqual(body["bah"], 1806.0)
        self.assertEqual(body["housing_total"], 1806.0)
        self.assertEqual(body["housing_label"], "BAH")
        self.assertEqual(body["gross_monthly"], 6431.0)
        self.assertEqual(body["mha"], "NC182")

    def test_oconus_income_endpoint(self):
        response = self.client.post(
            "/income/calculate",
            json={
                "rank": "E-5",
                "tis": 6,
                "has_dependents": True,
                "is_oconus": True,
                "oha_location": "Germany - Grafenwohr / Vilseck",
                "cola": 100,
                "special_pay": 150,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["base_pay"], 4110.0)
        self.assertEqual(body["bas"], 515.0)
        self.assertEqual(body["oha_rental"], 1600.0)
        self.assertEqual(body["oha_utility"], 440.0)
        self.assertEqual(body["housing_total"], 2040.0)
        self.assertEqual(body["housing_label"], "OHA + Utility")
        self.assertEqual(body["taxable_pay"], 4260.0)
        self.assertEqual(body["nontaxable_pay"], 2655.0)
        self.assertEqual(body["gross_monthly"], 6915.0)

    def test_income_endpoint_validates_negative_tis(self):
        response = self.client.post(
            "/income/calculate",
            json={
                "rank": "E-5",
                "tis": -1,
                "has_dependents": True,
                "zip_code": "28310",
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

