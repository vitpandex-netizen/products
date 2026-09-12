"""Unit-тесты для Stage 2: Voice AI Agent & LLM Router."""
import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from voice_agent import VoiceAgent

class TestVoiceAgent(unittest.TestCase):
    def setUp(self):
        self.agent = VoiceAgent()

    def test_transcribe_audio(self):
        res = self.agent.transcribe_audio(b"dummy_audio")
        self.assertEqual(res["status"], "success")
        self.assertIn("text", res)

    def test_ml_forecast_intent(self):
        res = self.agent.process_query("Каков прогноз по акции URTS?")
        self.assertEqual(res["intent"], "ml_forecast")
        self.assertEqual(res["ticker"], "URTS")
        self.assertIn("ИИ-Прогноз по акции URTS", res["response"])


    def test_risk_simulation_intent(self):
        res = self.agent.process_query("Посчитай риски портфеля и Монте Карло просадку")
        self.assertEqual(res["intent"], "risk_simulation")
        self.assertIn("Монте-Карло", res["response"])

    def test_sentiment_intent(self):
        res = self.agent.process_query("Какие новости и сентимент по ALKB?")
        self.assertEqual(res["intent"], "sentiment_analysis")
        self.assertEqual(res["ticker"], "ALKB")

    def test_dividend_intent(self):
        res = self.agent.process_query("Сколько дивидендов я получу?")
        self.assertEqual(res["intent"], "dividend_analysis")
        self.assertIn("Дивидендный анализ", res["response"])

if __name__ == "__main__":
    unittest.main()
