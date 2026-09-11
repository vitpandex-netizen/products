"""SQLite — хранилище stocks-uz: цены, портфель, идеи, сигналы."""
import sqlite3, os, json, logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

class DB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent.parent / "data" / "stocks-uz.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self):
        c = self.conn
        c.execute("""CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL, price REAL, closing_price REAL,
            day_change_pct REAL, fetched_at TEXT NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ph_ticker ON price_history(ticker)")
        c.execute("""CREATE TABLE IF NOT EXISTS fundamentals (
            ticker TEXT PRIMARY KEY, price REAL, closing_price REAL,
            sector TEXT, updated_at TEXT NOT NULL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS fundamentals_metrics (
            ticker TEXT PRIMARY KEY,
            pe_ratio REAL,
            pb_ratio REAL,
            roe REAL,
            graham_value REAL,
            dividend_yield REAL,
            updated_at TEXT NOT NULL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS portfolio (
            ticker TEXT PRIMARY KEY, shares REAL, avg_price REAL,
            target_pct REAL, stop_loss_pct REAL, notes TEXT,
            added_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL,
            direction TEXT CHECK(direction IN ('buy','sell','hold')),
            price REAL, target_price REAL, stop_price REAL,
            score INTEGER, rationale TEXT, risk_level TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','executed')),
            created_at TEXT NOT NULL, decided_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS dca_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL,
            day_of_week INTEGER CHECK(day_of_week BETWEEN 0 AND 6),
            threshold_pct REAL DEFAULT -2.0, enabled INTEGER DEFAULT 1
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS channel_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL, message_text TEXT,
            message_date TEXT, parsed_data TEXT,
            fetched_at TEXT NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ch_msg_lookup ON channel_messages(channel, fetched_at DESC)")
        c.execute("""CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL, alert_type TEXT NOT NULL,
            price REAL, change_pct REAL, message TEXT,
            sent INTEGER DEFAULT 0, created_at TEXT NOT NULL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS ohlcv_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL, date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            fetched_at TEXT NOT NULL,
            UNIQUE(ticker, date)
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv_ticker ON ohlcv_history(ticker, date)")
        self.conn.commit()

    def save_prices(self, quotes: dict):
        now = datetime.now(TASHKENT).isoformat()
        for ticker, q in quotes.items():
            self.conn.execute(
                "INSERT INTO price_history (ticker,price,closing_price,day_change_pct,fetched_at) VALUES (?,?,?,?,?)",
                (ticker, q.get('last_trade_price'), q.get('closing_price'), q.get('day_change_pct'), now))
        self.conn.commit()

    def get_latest_price(self, ticker: str) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM price_history WHERE ticker=? ORDER BY fetched_at DESC LIMIT 1", (ticker,)).fetchone()
        return dict(row) if row else None

    def get_all_latest_prices(self) -> dict:
        # Цены из price_history (регулярный сбор) + fallback на fundamentals (вручную/Jett live)
        rows = self.conn.execute(
            "SELECT ticker, price, closing_price, day_change_pct, fetched_at FROM price_history WHERE id IN (SELECT MAX(id) FROM price_history GROUP BY ticker)"
        ).fetchall()
        result = {r['ticker']: dict(r) for r in rows}

        # Дополняем тикерами, которых нет в price_history, но есть в fundamentals (Jett live, ручные)
        frows = self.conn.execute(
            "SELECT ticker, price, closing_price, updated_at as fetched_at FROM fundamentals"
        ).fetchall()
        for r in frows:
            if r['ticker'] not in result:
                result[r['ticker']] = {
                    "ticker": r["ticker"],
                    "price": r["price"],
                    "closing_price": r["closing_price"] or r["price"],
                    "day_change_pct": None,
                    "fetched_at": r["fetched_at"],
                }
        return result

    def save_idea(self, ticker: str, direction: str, price: float, target: float = None, stop: float = None, score: int = 0, rationale: str = "", risk: str = "medium") -> int:
        now = datetime.now(TASHKENT).isoformat()
        c = self.conn.execute(
            "INSERT INTO ideas (ticker,direction,price,target_price,stop_price,score,rationale,risk_level,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (ticker, direction, price, target, stop, score, rationale, risk, now))
        self.conn.commit()
        return c.lastrowid

    def get_pending_ideas(self) -> list:
        rows = self.conn.execute("SELECT * FROM ideas WHERE status='pending' ORDER BY score DESC").fetchall()
        return [dict(r) for r in rows]

    def decide_idea(self, idea_id: int, status: str):
        now = datetime.now(TASHKENT).isoformat()
        self.conn.execute("UPDATE ideas SET status=?, decided_at=? WHERE id=?", (status, now, idea_id))
        self.conn.commit()

    def get_idea_history(self, limit: int = 20) -> list:
        rows = self.conn.execute("SELECT * FROM ideas ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_portfolio(self) -> list:
        rows = self.conn.execute("SELECT * FROM portfolio ORDER BY ticker").fetchall()
        return [dict(r) for r in rows]

    def get_portfolio_tradeable(self) -> list:
        """Только позиции с рыночными данными (no_market_data=0)."""
        rows = self.conn.execute(
            "SELECT * FROM portfolio WHERE no_market_data IS NULL OR no_market_data=0 ORDER BY ticker"
        ).fetchall()
        return [dict(r) for r in rows]

    def add_to_portfolio(self, ticker: str, shares: float, price: float):
        now = datetime.now(TASHKENT).isoformat()
        self.conn.execute("INSERT OR REPLACE INTO portfolio (ticker,shares,avg_price,added_at,updated_at) VALUES (?,?,?,?,?)",
                          (ticker, shares, price, now, now))
        self.conn.commit()

    def save_channel_message(self, channel: str, text: str, msg_date: str,
                              parsed: dict = None):
        now = datetime.now(TASHKENT).isoformat()
        parsed_json = json.dumps(parsed, ensure_ascii=False) if parsed else None
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO channel_messages (channel,message_text,message_date,parsed_data,fetched_at) VALUES (?,?,?,?,?)",
                (channel, text[:2000], msg_date, parsed_json, now))
            self.conn.commit()
        except Exception:
            pass

    def get_recent_channel_messages(self, channel: str = None, limit: int = 10) -> list:
        if channel:
            rows = self.conn.execute(
                "SELECT * FROM channel_messages WHERE channel=? ORDER BY fetched_at DESC LIMIT ?",
                (channel, limit)).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM channel_messages ORDER BY fetched_at DESC LIMIT ?",
                (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_latest_channel_msgs_for_report(self, channels: list[str] = None,
                                            per_channel: int = 3) -> list[dict]:
        """Get latest messages per channel for the daily report."""
        result = []
        if channels:
            for ch in channels:
                rows = self.conn.execute(
                    "SELECT * FROM channel_messages WHERE channel=? ORDER BY fetched_at DESC LIMIT ?",
                    (ch, per_channel)).fetchall()
                for r in rows:
                    d = dict(r)
                    # Normalize: DB uses message_text, report expects 'text'
                    d['text'] = d.pop('message_text', '')
                    d['channel'] = d.get('channel', ch)
                    if d.get('parsed_data'):
                        try:
                            d['parsed'] = json.loads(d['parsed_data'])
                        except Exception:
                            pass
                    result.append(d)
        return result

    def save_alert(self, ticker: str, alert_type: str, price: float,
                    change_pct: float, message: str):
        now = datetime.now(TASHKENT).isoformat()
        self.conn.execute(
            "INSERT INTO alerts (ticker,alert_type,price,change_pct,message,created_at) VALUES (?,?,?,?,?,?)",
            (ticker, alert_type, price, change_pct, message, now))
        self.conn.commit()

    def get_unsent_alerts(self) -> list:
        rows = self.conn.execute(
            "SELECT * FROM alerts WHERE sent=0 ORDER BY ABS(change_pct) DESC LIMIT 10"
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_alert_sent(self, alert_id: int):
        self.conn.execute("UPDATE alerts SET sent=1 WHERE id=?", (alert_id,))
        self.conn.commit()

    def save_ohlcv(self, ticker: str, history: list[dict]):
        """Сохранить OHLCV историю (upsert по ticker+date)."""
        now = datetime.now(TASHKENT).isoformat()
        for h in history:
            date = h.get("date", "")[:10]
            if not date:
                continue
            self.conn.execute(
                """INSERT OR REPLACE INTO ohlcv_history
                   (ticker, date, open, high, low, close, volume, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (ticker, date, h.get("open"), h.get("high"), h.get("low"),
                 h.get("close"), h.get("volume"), now))
        self.conn.commit()

    def get_ohlcv(self, ticker: str, days: int = 90) -> list[dict]:
        """Получить OHLCV из кэша."""
        rows = self.conn.execute(
            "SELECT * FROM ohlcv_history WHERE ticker=? ORDER BY date DESC LIMIT ?",
            (ticker, days)).fetchall()
        return [dict(r) for r in rows]

    def ohlcv_ticker_count(self) -> int:
        """Сколько тикеров имеют кэшированные OHLCV."""
        row = self.conn.execute("SELECT COUNT(DISTINCT ticker) FROM ohlcv_history").fetchone()
        return row[0] if row else 0

    def get_latest_insights(self, days=5, limit=8):
        """Последние инсайты из каналов (тикер → событие → влияние)."""
        try:
            rows = self.conn.execute("""
                SELECT ticker, event, impact, channel, message, fetched_at
                FROM insights
                WHERE fetched_at >= datetime('now', ?)
                ORDER BY fetched_at DESC LIMIT ?
            """, (f'-{days} days', limit)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_portfolio_summary(self) -> dict:
        portfolio = self.get_portfolio()
        latest = self.get_all_latest_prices()
        total_cost = 0; total_value = 0; positions = []
        for p in portfolio:
            t = p['ticker']; price_info = latest.get(t)
            if not price_info: continue
            current_price = price_info['price'] or price_info['closing_price'] or 0
            cost = p['shares'] * p['avg_price']; value = p['shares'] * current_price
            pl = value - cost; pl_pct = ((current_price / p['avg_price']) - 1) * 100 if p['avg_price'] else 0
            total_cost += cost; total_value += value
            positions.append({'ticker': t, 'shares': p['shares'], 'avg_price': p['avg_price'], 'current_price': current_price, 'cost': cost, 'value': value, 'pl': pl, 'pl_pct': pl_pct})
        return {'positions': positions, 'total_cost': total_cost, 'total_value': total_value, 'total_pl': total_value - total_cost,
                'total_pl_pct': ((total_value / total_cost) - 1) * 100 if total_cost else 0}
