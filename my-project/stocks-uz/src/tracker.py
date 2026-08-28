"""
Трекер сделок stocks-uz — лимитные заявки, стоп-лоссы, тейк-профиты.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from datetime import datetime, timezone, timedelta
from src.db import DB

TASHKENT = timezone(timedelta(hours=5))

def init_trades():
    """Создать таблицы трекера."""
    db = DB()
    db.conn.execute("""CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL,
        direction TEXT, status TEXT DEFAULT 'pending', order_type TEXT DEFAULT 'limit',
        limit_price REAL, shares REAL, filled_price REAL, filled_at TEXT,
        commission REAL, stop_loss REAL, take_profit REAL,
        rationale TEXT, created_at TEXT, updated_at TEXT
    )""")
    db.conn.execute("""CREATE TABLE IF NOT EXISTS portfolio_watch (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL,
        shares REAL, avg_price REAL, target_price REAL,
        stop_loss REAL, take_profit_pct REAL DEFAULT 0.9,
        notes TEXT, active INTEGER DEFAULT 1,
        created_at TEXT, updated_at TEXT
    )""")
    db.conn.commit()

def add_limit_order(ticker: str, shares: float, limit_price: float,
                    stop_loss: float = None, take_profit: float = None,
                    rationale: str = None) -> int:
    db = DB()
    now = datetime.now(TASHKENT).isoformat()
    c = db.conn.execute(
        "INSERT INTO trades (ticker, direction, status, order_type, limit_price, shares, stop_loss, take_profit, rationale, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (ticker.upper(), "buy", "pending", "limit", limit_price, shares, stop_loss, take_profit, rationale, now, now))
    db.conn.commit()
    return c.lastrowid

def add_watch(ticker: str, shares: float, avg_price: float,
              target_price: float = None, stop_loss: float = None,
              notes: str = None) -> int:
    db = DB()
    now_dt = datetime.now(TASHKENT).isoformat()
    c = db.conn.execute(
        "INSERT INTO portfolio_watch (ticker, shares, avg_price, target_price, stop_loss, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (ticker.upper(), shares, avg_price, target_price, stop_loss, notes, now_dt, now_dt))
    db.conn.commit()
    return c.lastrowid

def check_pending_orders(current_prices: dict[str, float]) -> list[dict]:
    """Проверить, сработали ли лимитки."""
    db = DB()
    rows = db.conn.execute(
        "SELECT * FROM trades WHERE status='pending' AND direction='buy' AND order_type='limit'"
    ).fetchall()
    alerts = []
    for r in rows:
        price = current_prices.get(r["ticker"])
        if price and r["limit_price"] and price <= r["limit_price"]:
            now_dt = datetime.now(TASHKENT).isoformat()
            commission = round(price * r["shares"] * 0.03, 2)
            db.conn.execute(
                "UPDATE trades SET status='open', filled_price=?, filled_at=?, commission=?, updated_at=? WHERE id=?",
                (price, now_dt, commission, now_dt, r["id"]))
            db.conn.commit()
            alerts.append({
                "type": "limit_hit",
                "ticker": r["ticker"],
                "message": f"Лимитка {r['ticker']} сработала! Цена {price:.2f}",
            })
    return alerts

def check_watch_alerts(current_prices: dict[str, float]) -> list[dict]:
    """P&L и алерты по наблюдаемым позициям."""
    db = DB()
    rows = db.conn.execute("SELECT * FROM portfolio_watch WHERE active=1").fetchall()
    alerts = []
    for w in rows:
        price = current_prices.get(w["ticker"])
        if not price: continue
        pl_pct = (price / w["avg_price"] - 1) * 100 if w["avg_price"] else 0
        pl_value = (price - w["avg_price"]) * w["shares"]
        if w["stop_loss"] and price <= w["stop_loss"]:
            alerts.append({"type": "stop_loss", "ticker": w["ticker"],
                "message": f"STOP-LOSS {w['ticker']}: {price:.2f} <= {w['stop_loss']:.2f} ({pl_pct:+.2f}%)"})
        if w["target_price"]:
            tp_level = w["target_price"] * (w["take_profit_pct"] or 0.9)
            if price >= tp_level:
                alerts.append({"type": "near_target", "ticker": w["ticker"],
                    "message": f"{w['ticker']} у цели: {price:.2f} / {w['target_price']:.2f}"})
        alerts.append({"type": "pnl", "ticker": w["ticker"],
            "message": f"{w['ticker']}: {price:.2f} | P&L {pl_pct:+.2f}% ({pl_value:+,.0f})"})
    return alerts

def get_portfolio_summary(current_prices: dict[str, float]) -> dict:
    """Сводка по отслеживаемым позициям."""
    db = DB()
    watches = db.conn.execute("SELECT * FROM portfolio_watch WHERE active=1").fetchall()
    result = {"positions": [], "pending_orders": [], "total_value": 0, "total_cost": 0, "total_pl": 0}
    for w in watches:
        price = current_prices.get(w["ticker"], 0)
        cost = w["shares"] * w["avg_price"]
        value = w["shares"] * price
        result["total_cost"] += cost
        result["total_value"] += value
        result["positions"].append({"ticker": w["ticker"], "shares": w["shares"],
            "avg_price": w["avg_price"], "current_price": price,
            "cost": round(cost, 2), "value": round(value, 2),
            "pl": round(value - cost, 2),
            "pl_pct": round((price / w["avg_price"] - 1) * 100, 2) if w["avg_price"] else 0,
            "target": w["target_price"], "stop_loss": w["stop_loss"]})
    orders = db.conn.execute("SELECT * FROM trades WHERE status IN ('pending','open')").fetchall()
    for o in orders:
        result["pending_orders"].append({"id": o["id"], "ticker": o["ticker"],
            "price": o["limit_price"], "shares": o["shares"], "status": o["status"]})
    result["total_pl"] = round(result["total_value"] - result["total_cost"], 2)
    return result

def setup_cbsk_deal():
    """Настройка отслеживания сделки CBSK."""
    tid = add_limit_order("CBSK", 150000, 3.05, 2.70, 4.20,
        "KD таргет 4.20. Лимитка 3.05 (середина диапазона). Стоп 2.70.")
    wid = add_watch("CBSK", 150000, 3.05, 4.20, 2.70,
        "Таргет KD 4.20. Стоп 2.70 (майский аналитик).")
    return {"trade_id": tid, "watch_id": wid}

if __name__ == "__main__":
    init_trades()
    deal = setup_cbsk_deal()
    print(f"CBSK трекер: trade_id={deal['trade_id']}, watch_id={deal['watch_id']}")
    print(f"150,000 шт x 3.05 = 457,500 UZS | Таргет 4.20 | Стоп 2.70")