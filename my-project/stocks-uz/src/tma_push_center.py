"""
tma_push_center.py — Центр Push-уведомлений и подписок Telegram Mini App (TASK-STOCKS-083).
Управление алертами по акциям (ценовые пороги, дивиденды, OTC сделки, отчеты).
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from db import DB

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))


class TMAPushCenter:
    """Управление подписками на алерты и каналы уведомлений."""

    def __init__(self, db: Optional[DB] = None):
        self.db = db or DB()
        self._init_tables()

    def _init_tables(self):
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_alert_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                price_alert_threshold REAL,
                dividend_alert INTEGER DEFAULT 1,
                otc_alert INTEGER DEFAULT 1,
                created_at TEXT,
                UNIQUE(telegram_user_id, ticker)
            )
        """)
        self.db.conn.commit()

    def add_subscription(self, user_id: int, ticker: str, threshold: float = 5.0) -> Dict:
        ticker = ticker.upper()
        now_str = datetime.now(TASHKENT).isoformat()
        self.db.conn.execute("""
            INSERT OR REPLACE INTO user_alert_subscriptions
            (telegram_user_id, ticker, price_alert_threshold, dividend_alert, otc_alert, created_at)
            VALUES (?, ?, ?, 1, 1, ?)
        """, (user_id, ticker, threshold, now_str))
        self.db.conn.commit()

        return {
            "status": "success",
            "message": f"Подписка на {ticker} с порогом {threshold}% установлена.",
            "user_id": user_id,
            "ticker": ticker
        }

    def remove_subscription(self, user_id: int, ticker: str) -> Dict:
        ticker = ticker.upper()
        self.db.conn.execute("""
            DELETE FROM user_alert_subscriptions
            WHERE telegram_user_id = ? AND ticker = ?
        """, (user_id, ticker))
        self.db.conn.commit()
        return {"status": "success", "message": f"Подписка на {ticker} удалена."}

    def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        rows = self.db.conn.execute("""
            SELECT ticker, price_alert_threshold, dividend_alert, otc_alert, created_at
            FROM user_alert_subscriptions WHERE telegram_user_id = ?
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]
