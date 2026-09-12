"""Скоринг корпоративного управления и прозрачности эмитентов UZSE (Sprint 5)."""
from typing import Dict, Any, List

class ESGScorecard:
    def __init__(self, db=None):
        self.db = db

    def evaluate_transparency(self, ticker: str, metrics_override: Dict[str, Any] = None) -> Dict[str, Any]:
        """Оценка индекса прозрачности корпоративного управления эмитента."""
        metrics = metrics_override
        if metrics is None and self.db:
            # Пытаемся забрать показатели из fundamentals
            row = self.db.conn.execute("SELECT * FROM fundamentals_metrics WHERE ticker=?", (ticker,)).fetchone()
            metrics = dict(row) if row else {}

        score = 50.0  # Base rating
        factors = []

        if metrics.get("pe_ratio") and 0 < metrics["pe_ratio"] < 25:
            score += 15.0
            factors.append("Адекватный P/E коэффициент (открытая отчетность)")
        else:
            factors.append("Отсутствует прозрачный P/E")

        if metrics.get("dividend_yield") and metrics["dividend_yield"] > 0:
            score += 20.0
            factors.append("Регулярная выплата дивидендов по устава")

        if metrics.get("roe") and metrics["roe"] > 10.0:
            score += 15.0
            factors.append("Высокая эффективност капитала (ROE > 10%)")

        score = min(max(score, 0.0), 100.0)

        if score >= 75.0:
            grade = "A (Высокая прозрачность)"
        elif score >= 50.0:
            grade = "B (Умеренная прозрачность)"
        else:
            grade = "C (Низкое раскрытие)"

        return {
            "ticker": ticker,
            "transparency_score": round(score, 1),
            "grade": grade,
            "factors": factors
        }
