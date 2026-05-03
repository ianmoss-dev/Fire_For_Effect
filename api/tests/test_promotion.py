import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.loaders import load_military_data
from app.domain.promotion import (
    build_monthly_base_pay_schedule,
    get_progression_chain,
    get_projection_terminal_rank,
    project_rank_by_tis,
)


class PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_military_data()

    def test_progression_chain_by_rank_family(self):
        self.assertEqual(get_progression_chain("E-5")[0], "E-1")
        self.assertEqual(get_progression_chain("W-2")[0], "W-1")
        self.assertEqual(get_progression_chain("O-3")[0], "O-1")
        self.assertEqual(get_progression_chain("O-2E")[0], "O-1E")

    def test_terminal_rank_projection_caps(self):
        self.assertEqual(get_projection_terminal_rank("E-5"), "E-7")
        self.assertEqual(get_projection_terminal_rank("W-2"), "W-5")
        self.assertEqual(get_projection_terminal_rank("O-3"), "O-5")
        self.assertEqual(get_projection_terminal_rank("O-2E"), "O-4")

    def test_project_rank_by_tis_uses_terminal_cap(self):
        self.assertEqual(project_rank_by_tis("E-5", 7.9), "E-5")
        self.assertEqual(project_rank_by_tis("E-5", 8), "E-6")
        self.assertEqual(project_rank_by_tis("E-5", 14), "E-7")
        self.assertEqual(project_rank_by_tis("E-5", 24), "E-7")

    def test_monthly_base_pay_schedule_promotes_at_timeline(self):
        schedule = build_monthly_base_pay_schedule("E-5", 6, 25, self.data)

        self.assertEqual(len(schedule), 25)
        self.assertEqual(schedule[0], 4110.0)
        self.assertEqual(schedule[23], 4110.0)
        self.assertEqual(schedule[24], 4489.2)

    def test_officer_schedule_promotes_to_o4_at_tis_11(self):
        schedule = build_monthly_base_pay_schedule("O-3", 8, 37, self.data)

        self.assertEqual(schedule[0], 8125.5)
        self.assertEqual(schedule[35], 8375.7)
        self.assertEqual(schedule[36], 9420.0)


if __name__ == "__main__":
    unittest.main()
