import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.oha import get_oha_rate, list_oha_locations, resolve_oha_location


class OhaTests(unittest.TestCase):
    def test_germany_grafenwohr_legacy_key_matches_baseline(self):
        result = get_oha_rate("Germany â€” GrafenwÃ¶hr / Vilseck", "E-5", True)

        self.assertEqual(result.rental, 1600.0)
        self.assertEqual(result.utility, 440.0)
        self.assertEqual(result.total, 2040.0)

    def test_germany_grafenwohr_clean_alias_matches_legacy_key(self):
        result = get_oha_rate("Germany - Grafenwohr / Vilseck", "E-5", True)

        self.assertEqual(result.rental, 1600.0)
        self.assertEqual(result.utility, 440.0)
        self.assertEqual(result.total, 2040.0)
        self.assertEqual(result.location_key, "Germany â€” GrafenwÃ¶hr / Vilseck")

    def test_without_dependents_uses_second_rate(self):
        result = get_oha_rate("Germany - Grafenwohr / Vilseck", "E-5", False)

        self.assertEqual(result.rental, 1320.0)
        self.assertEqual(result.utility, 440.0)
        self.assertEqual(result.total, 1760.0)

    def test_unknown_rank_falls_back_to_location_e5_rate(self):
        result = get_oha_rate("Bahrain - NSA Manama", "O-10", True)

        self.assertEqual(result.rental, 1830.0)
        self.assertEqual(result.utility, 200.0)

    def test_unknown_location_uses_legacy_default_pair_and_utility(self):
        result = get_oha_rate("Atlantis", "E-5", True)

        self.assertEqual(result.rental, 1500.0)
        self.assertEqual(result.utility, 400.0)
        self.assertIsNone(result.location_key)

    def test_clean_location_list_is_ui_safe(self):
        locations = list_oha_locations(clean=True)

        self.assertIn("Germany - Grafenwohr / Vilseck", locations)
        self.assertEqual(
            resolve_oha_location("Germany - Grafenwohr / Vilseck"),
            "Germany â€” GrafenwÃ¶hr / Vilseck",
        )


if __name__ == "__main__":
    unittest.main()

