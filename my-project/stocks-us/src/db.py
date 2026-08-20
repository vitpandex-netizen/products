"""SQLite — всё хранилище stocks-us: цены, портфель, идеи, сигналы."""
import sqlite3, os, logging, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

class DB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent.parent / "data" / "stocks-us.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self):
        c = self.conn
        c.execute("""CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL, price REAL, prev_close REAL,
            day_change_pct REAL, volume REAL, fetched_at TEXT NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ph_ticker ON price_history(ticker)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ph_fetched ON price_history(fetched_at)")

        c.execute("""CREATE TABLE IF NOT EXISTS fundamentals (
            ticker TEXT PRIMARY KEY, price REAL, pe_ratio REAL, pb_ratio REAL,
            eps_ttm REAL, div_yield REAL, market_cap REAL, beta REAL,
            fifty_two_week_high REAL, fifty_two_week_low REAL,
            avg_volume REAL, sector TEXT, industry TEXT,
            updated_at TEXT NOT NULL
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS portfolio (
            ticker TEXT PRIMARY KEY, shares REAL, avg_price REAL,
            target_pct REAL, stop_loss_pct REAL, notes TEXT,
            added_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL, direction TEXT CHECK(direction IN ('buy','sell','hold')),
            price REAL, target_price REAL, stop_price REAL,
            score INTEGER, rationale TEXT, risk_level TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','executed')),
            created_at TEXT NOT NULL, decided_at TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER, ticker TEXT NOT NULL, direction TEXT,
            shares REAL, price REAL, total REAL,
            executed_at TEXT NOT NULL, note TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS signals (
            ticker TEXT NOT NULL, signal_type TEXT NOT NULL,
            value REAL, detail TEXT, created_at TEXT NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_signals ON signals(ticker, created_at)")

        c.execute("""CREATE TABLE IF NOT EXISTS dca_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL, day_of_week INTEGER CHECK(day_of_week BETWEEN 0 AND 6),
            time_of_day TEXT DEFAULT '14:30', threshold_pct REAL DEFAULT -2.0,
            enabled INTEGER DEFAULT 1, max_amount REAL
        )""")
        self.conn.commit()

    # ─── Цены ───
    def save_prices(self, quotes: dict):
        now = datetime.now(TASHKENT).isoformat()
        for ticker, q in quotes.items():
            self.conn.execute(
                "INSERT INTO price_history (ticker,price,prev_close,day_change_pct,volume,fetched_at) VALUES (?,?,?,?,?,?)",
                (ticker, q.get('price'), q.get('prev_close'), q.get('day_change_pct'), q.get('volume'), now)
            )
        self.conn.commit()

    def get_latest_price(self, ticker: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM price_history WHERE ticker=? ORDER BY fetched_at DESC LIMIT 1", (ticker,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_latest_prices(self) -> dict:
        rows = self.conn.execute(
            "SELECT ticker, price, day_change_pct, fetched_at FROM price_history WHERE id IN (SELECT MAX(id) FROM price_history GROUP BY ticker)"
        ).fetchall()
        return {r['ticker']: dict(r) for r in rows}

    def get_price_history(self, ticker: str, days: int = 30) -> list:
        rows = self.conn.execute(
            "SELECT * FROM price_history WHERE ticker=? AND fetched_at >= date('now', ?) ORDER BY fetched_at",
            (ticker, f'-{days} days')
        ).fetchall()
        return [dict(r) for r in rows]

    # ─── Фундаментал ───
    def save_fundamentals(self, ticker: str, data: dict):
        now = datetime.now(TASHKENT).isoformat()
        self.conn.execute("""INSERT OR REPLACE INTO fundamentals 
            (ticker,price,pe_ratio,pb_ratio,eps_ttm,div_yield,market_cap,beta,
             fifty_two_week_high,fifty_two_week_low,avg_volume,sector,industry,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ticker, data.get('price'), data.get('pe_ratio'), data.get('pb_ratio'),
             data.get('eps_ttm'), data.get('div_yield'), data.get('market_cap'),
             data.get('beta'), data.get('fifty_two_week_high'), data.get('fifty_two_week_low'),
             data.get('avg_volume'), data.get('sector'), data.get('industry'), now))
        self.conn.commit()

    def get_fundamentals(self, ticker: str) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM fundamentals WHERE ticker=?", (ticker,)).fetchone()
        return dict(row) if row else None

    def get_all_fundamentals(self) -> list:
        rows = self.conn.execute("SELECT * FROM fundamentals").fetchall()
        return [dict(r) for r in rows]

    # ─── Портфель ───
    def get_portfolio(self) -> list:
        rows = self.conn.execute("SELECT * FROM portfolio ORDER BY ticker").fetchall()
        return [dict(r) for r in rows]

    def add_to_portfolio(self, ticker: str, shares: float, price: float, target_pct: float = None, stop_loss_pct: float = None):
        now = datetime.now(TASHKENT).isoformat()
        self.conn.execute("""INSERT OR REPLACE INTO portfolio 
            (ticker,shares,avg_price,target_pct,stop_loss_pct,added_at,updated_at)
            VALUES (?,?,?,?,?,?,?)""",
            (ticker, shares, price, target_pct, stop_loss_pct, now, now))
        self.conn.commit()

    # ─── Идеи ───
    def save_idea(self, ticker: str, direction: str, price: float, target: float = None,
                  stop: float = None, score: int = 0, rationale: str = "", risk: str = "medium") -> int:
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

    # ─── Сигналы ───
    def save_signal(self, ticker: str, signal_type: str, value: float, detail: str = ""):
        now = datetime.now(TASHKENT).isoformat()
        self.conn.execute("INSERT INTO signals (ticker,signal_type,value,detail,created_at) VALUES (?,?,?,?,?)",
                          (ticker, signal_type, value, detail, now))
        self.conn.commit()

    # ─── DCA ───
    def get_dca_schedule(self) -> list:
        rows = self.conn.execute("SELECT * FROM dca_calendar WHERE enabled=1").fetchall()
        return [dict(r) for r in rows]

    def get_portfolio_summary(self) -> dict:
        """Возвращает сводку портфеля: стоимость, P&L, распределение."""
        portfolio = self.get_portfolio()
        latest = self.get_all_latest_prices()
        total_cost = 0
        total_value = 0
        positions = []
        for p in portfolio:
            t = p['ticker']
            price_info = latest.get(t)
            if not price_info:
                continue
            current_price = price_info['price']
            cost = p['shares'] * p['avg_price']
            value = p['shares'] * current_price
            pl = value - cost
            pl_pct = ((current_price / p['avg_price']) - 1) * 100 if p['avg_price'] else 0
            total_cost += cost
            total_value += value
            positions.append({
                'ticker': t, 'shares': p['shares'], 'avg_price': p['avg_price'],
                'current_price': current_price, 'cost': cost, 'value': value,
                'pl': pl, 'pl_pct': pl_pct, 'target_pct': p['target_pct'],
                'stop_loss_pct': p['stop_loss_pct'],
            })
        return {
            'positions': positions,
            'total_cost': total_cost,
            'total_value': total_value,
            'total_pl': total_value - total_cost,
            'total_pl_pct': ((total_value / total_cost) - 1) * 100 if total_cost else 0,
        }
