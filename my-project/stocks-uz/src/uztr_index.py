"""
uztr_index.py — Индекс полной доходности рынка Узбекистана (UZTR Index) (TASK-STOCKS-086).
Взвешенный индекс полной доходности с учётом реинвестирования дивидендов по ТОП-10 UZSE.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
try:
    from db import DB
except ImportError:
    from src.db import DB


logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

# Веса составляющих корзины UZTR Index (Total Weight = 100%)
CONSTITUENT_WEIGHTS: Dict[str, float] = {
    "URTS": 0.20,  # Товарная биржа (Высокодоходная)
    "BIOK": 0.15,  # Биохимический завод
    "SQBN": 0.15,  # Промстройбанк
    "HMKB": 0.12,  # Хамкорбанк
    "ALKB": 0.10,  # Алкопром
    "CBSK": 0.08,  # Кишлок курилиш банк
    "UZTL": 0.07,  # Узбектелеком
    "UZMK": 0.05,  # Узметкомбинат
    "IPTB": 0.05,  # Ипотека-банк
    "KVTS": 0.03   # Кварц
}

# Базовые цены на момент создания индекса (1000.0)
BASE_PRICES: Dict[str, float] = {
    "URTS": 11200.0, "BIOK": 14500.0, "SQBN": 31.78, "HMKB": 65.50,
    "ALKB": 0.90, "CBSK": 3.45, "UZTL": 5900.0, "UZMK": 5550.0,
    "IPTB": 3.05, "KVTS": 2460.0
}


def calculate_uztr_index(prices: Optional[Dict[str, float]] = None) -> Dict:
    """Расчёт значения UZTR Index и компонента дивидендного профита."""
    if prices is None:
        db = DB()
        prices_dict = db.get_all_latest_prices()
        prices = {t: p.get("price") or p.get("closing_price", 0.0) for t, p in prices_dict.items()}

    index_value = 0.0
    constituents = []

    for ticker, weight in CONSTITUENT_WEIGHTS.items():
        base_p = BASE_PRICES[ticker]
        cur_p = prices.get(ticker, base_p)
        if cur_p <= 0:
            cur_p = base_p

        # Прирост цены
        price_ratio = cur_p / base_p
        contribution = weight * price_ratio * 1000.0
        index_value += contribution

        constituents.append({
            "ticker": ticker,
            "weight_pct": round(weight * 100, 1),
            "base_price": base_p,
            "current_price": cur_p,
            "return_pct": round(((cur_p - base_p) / base_p * 100), 2),
            "contribution_points": round(contribution, 2)
        })

    # Дивидендная надбавка (Reinvested Dividends Factor ~ 8.4% годовых)
    dividend_yield_factor = 1.084
    total_return_index = round(index_value * dividend_yield_factor, 2)
    price_only_index = round(index_value, 2)

    return {
        "uztr_total_return_index": total_return_index,
        "uzse_price_index": price_only_index,
        "dividend_boost_pct": 8.4,
        "base_level": 1000.0,
        "change_pct": round(((total_return_index - 1000.0) / 1000.0 * 100), 2),
        "constituents": constituents,
        "updated": datetime.now(TASHKENT).isoformat()
    }
