"""ML-прогнозирование короткосрочных трендов акций UZSE (Sprint 5).

Использует признаки OHLCV (RSI, MA-Cross, Volatility, Volume Spike) для определения вероятности роста на 5 торговых дней.
"""
import math
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self, db=None):
        self.db = db

    def _calculate_indicators(self, ohlcv: List[Dict[str, Any]]) -> Dict[str, float]:
        """Расчет признаков из исторических данных OHLCV."""
        if not ohlcv or len(ohlcv) < 5:
            return {"rsi": 50.0, "ma_diff": 0.0, "volatility": 0.0, "vol_spike": 1.0, "last_price": 1000.0}

        closes = [x["close"] for x in reversed(ohlcv) if x.get("close")]
        volumes = [x["volume"] for x in reversed(ohlcv) if x.get("volume") is not None]

        if len(closes) < 5:
            return {"rsi": 50.0, "ma_diff": 0.0, "volatility": 0.0, "vol_spike": 1.0, "last_price": closes[-1] if closes else 1000.0}

        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))

        avg_gain = sum(gains[-14:]) / max(len(gains[-14:]), 1)
        avg_loss = sum(losses[-14:]) / max(len(losses[-14:]), 1)

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        ma5 = sum(closes[-5:]) / 5.0
        ma20 = sum(closes[-20:]) / max(len(closes[-20:]), 1)
        ma_diff = (ma5 - ma20) / ma20 if ma20 else 0.0

        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes)) if closes[i-1]]
        mean_ret = sum(returns) / max(len(returns), 1)
        var = sum((r - mean_ret) ** 2 for r in returns) / max(len(returns), 1)
        volatility = math.sqrt(var)

        recent_vol = sum(volumes[-3:]) / 3.0 if len(volumes) >= 3 else 1.0
        avg_vol = sum(volumes) / max(len(volumes), 1)
        vol_spike = recent_vol / avg_vol if avg_vol else 1.0

        return {
            "rsi": rsi,
            "ma_diff": ma_diff,
            "volatility": volatility,
            "vol_spike": vol_spike,
            "last_price": closes[-1]
        }

    def predict_ticker(self, ticker: str, ohlcv_override: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Генерация ML-прогноза направления движения цены на 5 дней."""
        ohlcv = ohlcv_override
        if not ohlcv and self.db:
            ohlcv = self.db.get_ohlcv(ticker, days=60)

        if not ohlcv:
            return {
                "ticker": ticker,
                "direction": "neutral",
                "up_probability": 0.50,
                "confidence_score": 0.30,
                "forecast_5d_pct": 0.0,
                "target_price": 0.0,
                "factors": ["Недостаточно исторических данных OHLCV"]
            }

        indicators = self.calculate_indicators_and_score(ohlcv)
        score = indicators["score"]
        prob = 1.0 / (1.0 + math.exp(-score))  # Sigmoid activation

        if prob > 0.55:
            direction = "bullish"
            forecast_pct = round((prob - 0.5) * 10, 2)
        elif prob < 0.45:
            direction = "bearish"
            forecast_pct = round((prob - 0.5) * 10, 2)
        else:
            direction = "neutral"
            forecast_pct = 0.0

        last_price = indicators["last_price"]
        target_price = round(last_price * (1 + forecast_pct / 100.0), 2)

        return {
            "ticker": ticker,
            "direction": direction,
            "up_probability": round(prob, 4),
            "confidence_score": round(abs(prob - 0.5) * 2, 2),
            "forecast_5d_pct": forecast_pct,
            "target_price": target_price,
            "indicators": {
                "rsi": round(indicators["rsi"], 2),
                "ma_diff_pct": round(indicators["ma_diff"] * 100, 2),
                "volatility_pct": round(indicators["volatility"] * 100, 2),
                "vol_spike_ratio": round(indicators["vol_spike"], 2)
            },
            "factors": indicators["factors"]
        }

    def calculate_indicators_and_score(self, ohlcv: List[Dict[str, Any]]) -> Dict[str, Any]:
        ind = self._calculate_indicators(ohlcv)
        score = 0.0
        factors = []

        if ind["rsi"] < 35:
            score += 0.6
            factors.append("Перепроданность по RSI (<35)")
        elif ind["rsi"] > 65:
            score -= 0.6
            factors.append("Перегретость по RSI (>65)")

        if ind["ma_diff"] > 0.02:
            score += 0.5
            factors.append("Бычий перекресток MA (5d > 20d)")
        elif ind["ma_diff"] < -0.02:
            score -= 0.5
            factors.append("Медвежье расхождение MA (5d < 20d)")

        if ind["vol_spike"] > 1.5:
            score += 0.4
            factors.append(f"Аномальный объем торгового интереса (x{ind['vol_spike']:.1f})")

        ind["score"] = score
        ind["factors"] = factors if factors else ["Стабильный боковой тренд"]
        return ind
