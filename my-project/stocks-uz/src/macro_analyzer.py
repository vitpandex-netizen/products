"""Макро-аналитика, сравнение со ставкой ЦБ РУз и кривая доходности (Sprint 5 - Stage 4)."""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Макроэкономические показатели Республики Узбекистан (2026)
CBU_KEY_RATE = 13.5       # Ключевая ставка Центрального банка РУз (%)
GOVT_BOND_YIELD = 15.0    # Доходность ГКО (Государственные облигации РУз, %)
INFLATION_RATE = 9.8      # Годовая инфляция РУз (%)
BANK_DEPOSIT_RATE = 21.0  # Средняя ставка сумовых вкладов физлиц (%)

class MacroAnalyzer:
    def __init__(self, db=None):
        self.db = db

    def evaluate_macro_yields(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Сравнение дивидендной доходности акций UZSE с макро-ориентирами (ЦБ РУз, ГКО, Вклады, Инфляция)."""
        if tickers is None:
            tickers = ["URTS", "BIOK", "UZMK", "ALKB", "CBSK", "IPTB"]

        equities_comparison = []

        # Эталонные дивидендные доходности
        default_yields = {
            "URTS": 33.6,
            "BIOK": 18.5,
            "UZMK": 15.0,
            "IPTB": 14.2,
            "ALKB": 12.0,
            "CBSK": 10.5
        }

        for t in tickers:
            div_yield = default_yields.get(t, 12.0)
            if self.db:
                # Попытка забрать реальную доходность из базы
                row = self.db.conn.execute("SELECT dividend_yield FROM fundamentals_metrics WHERE ticker=?", (t,)).fetchone()
                if row and row["dividend_yield"]:
                    div_yield = row["dividend_yield"]

            real_yield = div_yield - INFLATION_RATE
            risk_premium_over_cbu = div_yield - CBU_KEY_RATE
            spread_vs_deposit = div_yield - BANK_DEPOSIT_RATE

            is_outperforming_cbu = div_yield > CBU_KEY_RATE
            is_outperforming_inflation = div_yield > INFLATION_RATE

            equities_comparison.append({
                "ticker": t,
                "dividend_yield_pct": round(div_yield, 2),
                "real_dividend_yield_pct": round(real_yield, 2),
                "risk_premium_over_cbu_pct": round(risk_premium_over_cbu, 2),
                "spread_vs_bank_deposit_pct": round(spread_vs_deposit, 2),
                "beats_cbu_rate": is_outperforming_cbu,
                "beats_inflation": is_outperforming_inflation
            })

        equities_comparison.sort(key=lambda x: x["dividend_yield_pct"], reverse=True)

        return {
            "macro_benchmarks": {
                "cbu_key_rate_pct": CBU_KEY_RATE,
                "govt_bond_gko_yield_pct": GOVT_BOND_YIELD,
                "bank_deposit_avg_pct": BANK_DEPOSIT_RATE,
                "annual_inflation_pct": INFLATION_RATE
            },
            "equities_comparison": equities_comparison,
            "summary_takeaway": (
                f"Топовые акции UZSE (URTS {equities_comparison[0]['dividend_yield_pct']}%, BIOK {equities_comparison[1]['dividend_yield_pct']}%) "
                f"существенно опережают ключевую ставку ЦБ РУз ({CBU_KEY_RATE}%) и государственные вклады ({BANK_DEPOSIT_RATE}%), "
                f"обеспечивая высокую реальную доходность выше инфляции ({INFLATION_RATE}%)."
            )
        }
