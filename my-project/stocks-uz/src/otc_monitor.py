"""
otc_monitor.py — Сканер крупноблочных внесистемных сделок UZSE / NAPP (TASK-STOCKS-085).
Детектор сделок купли-продажи крупных пакетов акций (OTC) и смены собственников >5%.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
try:
    from db import DB
except ImportError:
    from src.db import DB


logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

# Порог крупной сделки (50 млн UZS)
LARGE_TRADE_THRESHOLD_UZS = 50_000_000.0


def scan_otc_block_trades(db: Optional[DB] = None) -> List[Dict]:
    """Сканирование и выявление аномальных крупноблочных сделок."""
    if db is None:
        db = DB()

    db.conn.execute("""
        CREATE TABLE IF NOT EXISTS trade_flow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            amount REAL,
            n INTEGER,
            fetched_at TEXT
        )
    """)

    trade_rows = db.conn.execute("""
        SELECT ticker, amount, n, fetched_at FROM trade_flow
        WHERE amount >= ?
        ORDER BY fetched_at DESC LIMIT 20
    """, (LARGE_TRADE_THRESHOLD_UZS,)).fetchall()


    results = []
    prices = db.get_all_latest_prices()

    for row in trade_rows:
        ticker = row['ticker']
        amount = row['amount']
        mkt_info = prices.get(ticker, {})
        mkt_price = mkt_info.get('price') or mkt_info.get('closing_price') or 0.0

        # Оценка типа блока
        is_whale = amount >= 200_000_000.0
        trade_type = "Крупный инсайдерский блок (Whale OTC)" if is_whale else "Внесистемная пакетная сделка"

        results.append({
            "ticker": ticker,
            "amount_uzs": round(amount, 0),
            "market_price": mkt_price,
            "trade_type": trade_type,
            "is_significant_block": is_whale,
            "detected_at": row['fetched_at'] or datetime.now(TASHKENT).isoformat()
        })

    return results


def get_otc_summary() -> Dict:
    """Сводка по институциональной активности на внебиржевом рынке UZSE."""
    db = DB()
    blocks = scan_otc_block_trades(db)
    total_volume_uzs = sum(b['amount_uzs'] for b in blocks)
    whale_count = sum(1 for b in blocks if b['is_significant_block'])

    return {
        "blocks_count": len(blocks),
        "total_volume_uzs": total_volume_uzs,
        "whale_blocks_count": whale_count,
        "items": blocks,
        "updated": datetime.now(TASHKENT).isoformat()
    }
