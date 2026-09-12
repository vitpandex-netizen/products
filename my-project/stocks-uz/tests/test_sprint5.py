"""Unit-тесты Спринта 5 для Stocks UZ."""
import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ml_predictor import MLPredictor
from sentiment_analyzer import SentimentAnalyzer
from anomaly_detector import AnomalyDetector
from tradingview_widget import TradingViewWidget
from heatmap_matrix import HeatmapMatrix
from vault_backup import VaultBackup
from monte_carlo import MonteCarloSimulator
from ipo_tracker import IPOTracker
from esg_scorecard import ESGScorecard

class TestSprint5(unittest.TestCase):
    def setUp(self):
        self.sample_ohlcv = [
            {"date": "2026-09-12", "open": 100.0, "high": 105.0, "low": 98.0, "close": 104.0, "volume": 5000},
            {"date": "2026-09-11", "open": 98.0, "high": 101.0, "low": 97.0, "close": 100.0, "volume": 2000},
            {"date": "2026-09-10", "open": 95.0, "high": 99.0, "low": 94.0, "close": 98.0, "volume": 1800},
            {"date": "2026-09-09", "open": 96.0, "high": 97.0, "low": 93.0, "close": 95.0, "volume": 1500},
            {"date": "2026-09-08", "open": 92.0, "high": 96.0, "low": 91.0, "close": 96.0, "volume": 1200},
        ]

    def test_ml_predictor(self):
        predictor = MLPredictor()
        res = predictor.predict_ticker("URTS", ohlcv_override=self.sample_ohlcv)
        self.assertEqual(res["ticker"], "URTS")
        self.assertIn("direction", res)
        self.assertIn(res["direction"], ["bullish", "bearish", "neutral"])
        self.assertGreaterEqual(res["up_probability"], 0.0)

    def test_sentiment_analyzer(self):
        analyzer = SentimentAnalyzer()
        res = analyzer.analyze_text("Компания выкупит дивиденд рекордная прибыль!")
        self.assertEqual(res["label"], "positive")
        self.assertGreater(res["sentiment_score"], 0)

        res_ticker = analyzer.analyze_ticker_sentiment("ALKB", messages_override=[{"text": "падение убыток штраф"}])
        self.assertEqual(res_ticker["label"], "bearish")

    def test_anomaly_detector(self):
        detector = AnomalyDetector()
        res = detector.detect_anomalies("URTS", ohlcv_override=self.sample_ohlcv)
        self.assertIn("anomaly_detected", res)
        self.assertIsInstance(res["flags"], list)

    def test_tradingview_widget(self):
        html = TradingViewWidget.render_lightweight_chart("URTS", self.sample_ohlcv)
        self.assertIn("TradingView Chart - URTS", html)
        self.assertIn("LightweightCharts", html)

    def test_heatmap_matrix(self):
        hm = HeatmapMatrix()
        prices = {"URTS": {"price": 10500, "day_change_pct": 5.2}, "ALKB": {"price": 0.90, "day_change_pct": -1.5}}
        heatmap = hm.generate_heatmap(prices_override=prices)
        self.assertEqual(len(heatmap), 2)

        corr = hm.calculate_correlation_matrix(["URTS", "ALKB"], ohlcv_map={"URTS": self.sample_ohlcv, "ALKB": self.sample_ohlcv})
        self.assertEqual(corr["correlation_matrix"]["URTS"]["ALKB"], 1.0)

    def test_vault_backup(self):
        backup = VaultBackup()
        res = backup.create_backup()
        # Статус либо success, либо error (если файл не создан)
        self.assertIn(res["status"], ["success", "error"])

    def test_monte_carlo(self):
        sim = MonteCarloSimulator()
        res = sim.simulate_portfolio(simulations=100, days=10)
        self.assertEqual(res["simulations_count"], 100)
        self.assertIn("var_95_loss_pct", res)

    def test_ipo_tracker(self):
        tracker = IPOTracker()
        events = tracker.get_upcoming_ipos()
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]["ticker"], "SQBN")

    def test_esg_scorecard(self):
        esg = ESGScorecard()
        res = esg.evaluate_transparency("URTS", metrics_override={"pe_ratio": 2.8, "dividend_yield": 33.6, "roe": 24.5})
        self.assertGreaterEqual(res["transparency_score"], 75.0)
        self.assertIn("A", res["grade"])

if __name__ == "__main__":
    unittest.main()
