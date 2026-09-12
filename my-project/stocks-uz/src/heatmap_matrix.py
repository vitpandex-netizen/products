"""Тепловая карта рынка UZSE и Матрица корреляции активов (Sprint 5)."""
import math
from typing import Dict, Any, List

class HeatmapMatrix:
    def __init__(self, db=None):
        self.db = db

    def generate_heatmap(self, prices_override: Dict[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Генерация данных для визуализации тепловой карты рынка UZSE."""
        prices = prices_override
        if prices is None and self.db:
            prices = self.db.get_all_latest_prices()

        if not prices:
            return []

        heatmap = []
        for ticker, data in prices.items():
            price = data.get("price") or data.get("closing_price") or 0.0
            change = data.get("day_change_pct") or 0.0

            if change > 2.0:
                color = "#26a69a"  # Strong Green
            elif change > 0:
                color = "#80cbc4"  # Light Green
            elif change < -2.0:
                color = "#ef5350"  # Strong Red
            elif change < 0:
                color = "#e57373"  # Light Red
            else:
                color = "#b0bec5"  # Grey

            heatmap.append({
                "ticker": ticker,
                "price": price,
                "day_change_pct": change,
                "color_code": color
            })

        return sorted(heatmap, key=lambda x: abs(x["day_change_pct"]), reverse=True)

    def calculate_correlation_matrix(self, tickers: List[str], ohlcv_map: Dict[str, List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Расчет матрицы корреляции Пирсона между тикерами UZSE."""
        if ohlcv_map is None and self.db:
            ohlcv_map = {t: self.db.get_ohlcv(t, days=30) for t in tickers}

        returns_map = {}
        for t in tickers:
            series = ohlcv_map.get(t, [])
            closes = [x["close"] for x in reversed(series) if x.get("close")]
            rets = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes)) if closes[i-1]]
            returns_map[t] = rets

        matrix = {}
        for t1 in tickers:
            matrix[t1] = {}
            for t2 in tickers:
                r1 = returns_map.get(t1, [])
                r2 = returns_map.get(t2, [])

                min_len = min(len(r1), len(r2))
                if min_len < 3:
                    matrix[t1][t2] = 1.0 if t1 == t2 else 0.0
                    continue

                x = r1[:min_len]
                y = r2[:min_len]

                mean_x = sum(x) / min_len
                mean_y = sum(y) / min_len

                num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(min_len))
                den_x = sum((x[i] - mean_x) ** 2 for i in range(min_len))
                den_y = sum((y[i] - mean_y) ** 2 for i in range(min_len))

                if den_x > 0 and den_y > 0:
                    corr = num / math.sqrt(den_x * den_y)
                else:
                    corr = 1.0 if t1 == t2 else 0.0

                matrix[t1][t2] = round(corr, 2)

        return {
            "tickers": tickers,
            "correlation_matrix": matrix
        }
