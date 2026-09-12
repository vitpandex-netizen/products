"""Детектор аномальных манипуляций и фиктивных сделок на UZSE (Sprint 5)."""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, db=None):
        self.db = db

    def detect_anomalies(self, ticker: str, ohlcv_override: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Анализ аномальных всплесков объемов и цен (Pump & Dump / Wash Trading)."""
        ohlcv = ohlcv_override
        if ohlcv is None and self.db:
            ohlcv = self.db.get_ohlcv(ticker, days=30)

        if not ohlcv or len(ohlcv) < 3:
            return {
                "ticker": ticker,
                "anomaly_detected": False,
                "risk_score": 0.0,
                "flags": []
            }

        latest = ohlcv[0]
        history = ohlcv[1:]

        avg_volume = sum(h.get("volume", 0) or 0 for h in history) / max(len(history), 1)
        avg_close = sum(h.get("close", 0) or 0 for h in history) / max(len(history), 1)

        curr_vol = latest.get("volume", 0) or 0
        curr_close = latest.get("close", 0) or 0
        curr_open = latest.get("open", curr_close) or curr_close

        flags = []
        risk_score = 0.0

        # Volume spike flag
        if avg_volume > 0 and curr_vol > avg_volume * 3.0:
            vol_ratio = curr_vol / avg_volume
            flags.append(f"Аномальный всплеск объема (x{vol_ratio:.1f} от среднего)")
            risk_score += 0.4

        # Price pump flag
        if curr_open > 0:
            pct_change = abs(curr_close - curr_open) / curr_open * 100
            if pct_change > 12.0:
                flags.append(f"Аномальный скачок цены ({pct_change:.1f}%)")
                risk_score += 0.4

        # Wash trading suspect flag (High volume, 0 price change)
        if avg_volume > 0 and curr_vol > avg_volume * 2.5 and curr_close == curr_open:
            flags.append("Подозрение на фиктивный прокрут (Wash Trading: высокий объем при 0% изменении цены)")
            risk_score += 0.5

        return {
            "ticker": ticker,
            "anomaly_detected": risk_score >= 0.4,
            "risk_score": round(min(risk_score, 1.0), 2),
            "flags": flags
        }
