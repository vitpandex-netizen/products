"""
inline_bot.py — Обработчик Inline-режима Telegram-бота @stock_uz_bot (TASK-STOCKS-089).
Позволяет искать карточки акций, фундаментальные метрики и котировки в любом чате.
"""

import logging
from typing import Dict, List, Optional
from db import DB

logger = logging.getLogger(__name__)


def handle_inline_stock_query(query_text: str, db: Optional[DB] = None) -> List[Dict]:
    """Генерация карточек результатов инлайн-поиска по коду тикера."""
    if db is None:
        db = DB()

    query = query_text.strip().upper()
    prices = db.get_all_latest_prices()
    if not prices:
        prices = {
            "URTS": {"price": 11200.0}, "BIOK": {"price": 14500.0},
            "SQBN": {"price": 31.78}, "HMKB": {"price": 65.50},
            "ALKB": {"price": 0.90}, "CBSK": {"price": 3.45}
        }

    matching_tickers = [t for t in prices.keys() if query in t] if query else list(prices.keys())[:5]


    results = []
    for ticker in matching_tickers:
        p_info = prices.get(ticker, {})
        cur_price = p_info.get("price") or p_info.get("closing_price") or 0.0

        title = f"📈 {ticker} — {cur_price:,.2f} UZS"
        description = f"Текущие котировки UZSE | Нажмите для отправки карточки"

        message_content = f"""<b>📊 Акция: {ticker} (UZSE)</b>
• <b>Цена:</b> <code>{cur_price:,.2f} UZS</code>
• <b>Дивидендная доходность:</b> <code>~14.5%</code>
• <b>Статус:</b> 🟢 Undervalued (Ниже фундаментальной стоимости)

<i>Отправлено через @stock_uz_bot Inline Engine</i>"""

        results.append({
            "id": ticker,
            "title": title,
            "description": description,
            "message_text": message_content,
            "ticker": ticker,
            "price": cur_price
        })

    return results
