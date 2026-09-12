"""Unit-тесты для Stage 4: MacroAnalyzer & CBU Rate Correlation."""
import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from macro_analyzer import MacroAnalyzer

class TestStage4Macro(unittest.TestCase):
    def setUp(self):
        self.analyzer = MacroAnalyzer()

    def test_evaluate_macro_yields(self):
        res = self.analyzer.evaluate_macro_yields()
        self.assertIn("macro_benchmarks", res)
        self.assertEqual(res["macro_benchmarks"]["cbu_key_rate_pct"], 13.5)
        self.assertEqual(res["macro_benchmarks"]["annual_inflation_pct"], 9.8)

        equities = res["equities_comparison"]
        self.assertGreater(len(equities), 0)
        self.assertTrue(equities[0]["beats_cbu_rate"])
        self.assertTrue(equities[0]["beats_inflation"])
        self.assertIn("summary_takeaway", res)

if __name__ == "__main__":
    unittest.main()
