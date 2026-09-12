"""Unit-тесты для Stage 3: Auto-Execution Engine & Trailing Stop-Loss."""
import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from auto_execution import AutoExecutionEngine

class TestStage3Trading(unittest.TestCase):
    def setUp(self):
        self.engine = AutoExecutionEngine()

    def test_calculate_rebalance(self):
        res = self.engine.calculate_rebalance(threshold_pct=5.0)
        self.assertIn("total_portfolio_value", res)
        self.assertIn("rebalance_required", res)
        self.assertIsInstance(res["orders"], list)

    def test_trailing_stop_hold(self):
        res = self.engine.update_trailing_stop("URTS", current_price=10500, highest_price=10800, trail_pct=5.0)
        self.assertEqual(res["action"], "HOLD_AND_TRAIL")
        self.assertFalse(res["triggered"])
        self.assertEqual(res["stop_loss_price"], 10260.0)

    def test_trailing_stop_trigger(self):
        # Current price dropped below 5% trail of peak 11000 => stop price is 10450
        res = self.engine.update_trailing_stop("URTS", current_price=10200, highest_price=11000, trail_pct=5.0)
        self.assertEqual(res["action"], "EXECUTE_STOP_LOSS_SELL")
        self.assertTrue(res["triggered"])

if __name__ == "__main__":
    unittest.main()
