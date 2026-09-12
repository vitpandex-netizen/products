"""
test_sprint4.py — Набор unit-тестов для задач Спринта 4 (Stocks UZ).
"""

import os
import sys
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from real_time import RealTimeManager
from cache import InMemoryCache, cache_get, cache_set
from otc_monitor import scan_otc_block_trades, get_otc_summary
from uztr_index import calculate_uztr_index
from tax_calculator import calculate_tax_breakdown
from teaser import generate_investment_teaser
from openinfo_napp import get_disclosures_summary
from altman_zscore import calculate_altman_zscore, get_all_zscores_summary
from tma_push_center import TMAPushCenter
from backtester import run_strategy_backtest
from inline_bot import handle_inline_stock_query


class TestSprint4Features(unittest.TestCase):

    def test_real_time_manager(self):
        rt = RealTimeManager()
        tick = rt.generate_random_tick()
        self.assertIn("ticker", tick)
        self.assertIn("price", tick)
        self.assertIn("change_pct", tick)
        self.assertGreater(tick["price"], 0)

    def test_in_memory_cache(self):
        cache = InMemoryCache()
        cache.set("key1", {"data": 123}, ttl_seconds=10)
        val = cache.get("key1")
        self.assertEqual(val, {"data": 123})

    def test_global_cache_fallback(self):
        cache_set("test_key", "hello_sprint4", ttl_seconds=5)
        res = cache_get("test_key")
        self.assertEqual(res, "hello_sprint4")

    def test_otc_monitor(self):
        summary = get_otc_summary()
        self.assertIn("blocks_count", summary)
        self.assertIn("total_volume_uzs", summary)
        self.assertIsInstance(summary["items"], list)

    def test_uztr_index_calculation(self):
        idx = calculate_uztr_index()
        self.assertIn("uztr_total_return_index", idx)
        self.assertGreater(idx["uztr_total_return_index"], 500.0)
        self.assertIn("constituents", idx)
        self.assertEqual(len(idx["constituents"]), 10)

    def test_tax_calculator_resident(self):
        tax = calculate_tax_breakdown("URTS", shares=100, buy_price=10000, current_price=12000, dividend_per_share=1000, is_resident=True)
        self.assertEqual(tax["dividend_tax_rate_pct"], 5.0)
        self.assertEqual(tax["gross_dividend_uzs"], 100000.0)
        self.assertEqual(tax["dividend_tax_uzs"], 5000.0)
        self.assertEqual(tax["net_dividend_uzs"], 95000.0)

    def test_tax_calculator_non_resident(self):
        tax = calculate_tax_breakdown("URTS", shares=100, buy_price=10000, current_price=12000, dividend_per_share=1000, is_resident=False)
        self.assertEqual(tax["dividend_tax_rate_pct"], 12.0)
        self.assertEqual(tax["dividend_tax_uzs"], 12000.0)

    def test_investment_teaser_generation(self):
        teaser = generate_investment_teaser("URTS")
        self.assertEqual(teaser["ticker"], "URTS")
        self.assertIn("markdown_report", teaser)
        self.assertIn("Инвестиционный Тизер", teaser["markdown_report"])

    def test_openinfo_napp_disclosures(self):
        disc = get_disclosures_summary()
        self.assertGreater(disc["disclosures_count"], 0)
        self.assertGreater(disc["dividend_resolutions_count"], 0)

    def test_altman_zscore(self):
        z = calculate_altman_zscore("URTS")
        self.assertEqual(z["ticker"], "URTS")
        self.assertIn("z_score", z)
        self.assertIn("zone", z)
        all_z = get_all_zscores_summary()
        self.assertGreater(len(all_z), 0)

    def test_tma_push_center(self):
        pc = TMAPushCenter()
        sub = pc.add_subscription(12345, "URTS", 4.5)
        self.assertEqual(sub["status"], "success")
        subs = pc.get_user_subscriptions(12345)
        self.assertEqual(len(subs), 1)

    def test_backtester(self):
        bt = run_strategy_backtest("graham_value", 100000000.0, 5)
        self.assertEqual(bt["strategy"], "graham_value")
        self.assertGreater(bt["cagr_pct"], 0)
        self.assertEqual(len(bt["equity_curve"]), 5)

    def test_inline_bot(self):
        res = handle_inline_stock_query("URTS")
        self.assertGreater(len(res), 0)
        self.assertEqual(res[0]["id"], "URTS")



if __name__ == "__main__":
    unittest.main()
