"""
stocks-uz API — кокпит портфеля UZSE.
FastAPI + сигнальный движок + трекер сделок + фронтенд.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

from db import DB
from engine import (consolidate_positions, barbell_balance, concentration,
                    run_signal_engine, bonds_summary, ytm)
from tracker import init_trades, add_limit_order, add_watch, check_pending_orders, get_portfolio_summary

TASHKENT = timezone(timedelta(hours=5))
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="stocks-uz", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Frontend
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


def get_db():
    return DB()


def get_prices_dict(db: DB) -> dict[str, float]:
    prices = db.get_all_latest_prices()
    return {t: p.get("price", 0) or p.get("closing_price", 0) for t, p in prices.items()}


# ===== Pydantic models =====
class PositionInput(BaseModel):
    ticker: str; broker: str; shares: float; avg_buy_price: float

class TargetInput(BaseModel):
    ticker: str; value: float; horizon: str; analyst: str

class PriceInput(BaseModel):
    ticker: str; price: float; source: str = "manual"

class BondInput(BaseModel):
    ticker: str; issuer: str; coupon_rate: float; nominal: float
    buy_price: float; shares: float; maturity: str; insured: bool = False
    broker: str = "EXTURE+G"; account: str = "IIS"

class LimitOrderInput(BaseModel):
    ticker: str; price: float; shares: float; stop_loss: float = None; take_profit: float = None


# ===== API Endpoints =====
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.2.0", "project": "stocks-uz"}

@app.get("/api/portfolio")
def portfolio(db: DB = Depends(get_db)):
    """Текущий портфель из БД + сигналы."""
    positions = db.get_portfolio()  # from portfolio table
    prices = get_prices_dict(db)
    targets = db.conn.execute("SELECT * FROM targets").fetchall()
    target_list = [dict(t) for t in targets]
    
    pos_list = [{"ticker": p["ticker"], "shares": p["shares"],
                 "avg_buy_price": p["avg_price"], "broker": p.get("broker", "manual")} for p in positions]
    
    consolidated = consolidate_positions(pos_list, prices)
    barbell = barbell_balance(pos_list, [], prices)
    conc = concentration(pos_list, prices)
    signals = run_signal_engine(pos_list, target_list, prices, {})
    
    return {**consolidated, "barbell": barbell, "concentration": conc, "signals": signals}

@app.get("/api/signals")
def signals(db: DB = Depends(get_db)):
    positions = db.get_portfolio()
    prices = get_prices_dict(db)
    targets = db.conn.execute("SELECT * FROM targets").fetchall()
    target_list = [dict(t) for t in targets]
    pos_list = [{"ticker": p["ticker"], "shares": p["shares"],
                 "avg_buy_price": p["avg_price"], "broker": p.get("broker", "manual")} for p in positions]
    return run_signal_engine(pos_list, target_list, prices, {})

@app.get("/api/prices")
def prices(db: DB = Depends(get_db)):
    return {"prices": get_prices_dict(db)}

@app.get("/api/targets")
def list_targets(db: DB = Depends(get_db)):
    rows = db.conn.execute("SELECT * FROM targets ORDER BY ticker").fetchall()
    return {"targets": [dict(r) for r in rows]}

@app.post("/api/targets")
def add_target(t: TargetInput, db: DB = Depends(get_db)):
    db.conn.execute(
        "INSERT INTO targets (ticker, value, horizon, analyst, as_of) VALUES (?,?,?,?,?)",
        (t.ticker.upper(), t.value, t.horizon, t.analyst, datetime.now(TASHKENT).isoformat()))
    db.conn.commit()
    return {"status": "ok"}

@app.get("/api/bonds")
def bonds(db: DB = Depends(get_db)):
    # Get bonds from the portfolio table or dedicated bonds table
    bonds_data = db.conn.execute("SELECT * FROM bonds").fetchall()
    bond_list = [dict(b) for b in bonds_data]
    return {"bonds": bond_list, "summary": bonds_summary(bond_list)}

@app.get("/api/orders")
def orders(db: DB = Depends(get_db)):
    """Текущие лимитные заявки."""
    rows = db.conn.execute(
        "SELECT * FROM trades WHERE status IN ('pending','open') ORDER BY created_at DESC"
    ).fetchall()
    return {"orders": [dict(r) for r in rows]}

@app.post("/api/orders")
def create_order(o: LimitOrderInput, db: DB = Depends(get_db)):
    """Создать лимитную заявку."""
    from tracker import Trade
    db.conn.execute(
        "INSERT INTO trades (ticker, direction, status, order_type, limit_price, shares, stop_loss, take_profit, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (o.ticker.upper(), "buy", "pending", "limit", o.price, o.shares, o.stop_loss, o.take_profit,
         datetime.now(TASHKENT).isoformat(), datetime.now(TASHKENT).isoformat()))
    db.conn.commit()
    return {"status": "ok", "message": f"Лимитка {o.ticker} @ {o.price} на {o.shares:,} шт"}

@app.get("/api/catalysts")
def catalysts(db: DB = Depends(get_db)):
    rows = db.conn.execute("SELECT * FROM catalysts ORDER BY date").fetchall()
    return {"catalysts": [dict(r) for r in rows]}

@app.get("/api/latest")
def latest(db: DB = Depends(get_db)):
    """Последние цены с UZSE."""
    from uzse_enhanced import UZSEEnhancedClient
    client = UZSEEnhancedClient()
    prices = client.fetch_all_prices()
    return {"prices": prices, "count": len(prices)}


# ===== Seed data =====
@app.post("/api/seed")
def seed():
    db = DB()
    # Check if already seeded (use portfolio table, not price_history)
    row = db.conn.execute("SELECT COUNT(*) FROM portfolio").fetchone()
    if row and row[0] > 0:
        return {"status": "already_seeded"}

    # Seed portfolio positions (from TZ)
    import json
    now_iso = datetime.now(TASHKENT).isoformat()
    
    # Add portfolio entries
    portfolio_seed = [
        ("SQBN", 162892, 31.78), ("HMKB", 34386, 65.50),
        ("UZTL", 397, 5900), ("CBSK", 41754, 3.05),
        ("ALKB", 99857, 0.85), ("UZMK", 252, 5550),
        ("IPTB", 3005, 3.05), ("KVTS", 73, 2460),
        ("TRSB", 111, 11999), ("UZINP", 30, 1990),
        ("AGMKP", 100, 17000), ("UZNF", 888888, 6.65),
        ("ONETP", 86, 4770), ("UZNGP", 156, 2821),
        ("BNGPP", 6, 120000),
    ]
    for t, s, p in portfolio_seed:
        db.conn.execute("INSERT OR IGNORE INTO portfolio (ticker, shares, avg_price, added_at, updated_at) VALUES (?,?,?,?,?)",
                        (t, s, p, now_iso, now_iso))
    
    # Seed targets
    targets = [
        ("SQBN", 37.00, "1Y", "KAP DEPO"), ("HMKB", 74.68, "1Y", "KAP DEPO"),
        ("UZTL", 7650, "1Y", "KAP DEPO"), ("UZTL", 52603, "internal_fund", "UzNIF"),
        ("CBSK", 4.20, "1Y", "KAP DEPO"), ("ALKB", 1.13, "1Y", "KAP DEPO"),
        ("ALKB", 1.10, "fundamental", "KAP DEPO"), ("UZMK", 6800, "1Y", "KAP DEPO"),
        ("UZMK", 6314, "1Y", "Freedom"), ("IPTB", 3.40, "1Y", "KAP DEPO"),
        ("KVTS", 2000, "1Y", "KAP DEPO"), ("KVTS", 3490, "fundamental", "KAP DEPO"),
        ("TRSB", 8000, "1Y", "KAP DEPO"), ("UZINP", 1850, "1Y", "KAP DEPO"),
    ]
    for t, v, h, a in targets:
        db.conn.execute("INSERT INTO targets (ticker, value, horizon, analyst, as_of, created_at) VALUES (?,?,?,?,?,?)",
                        (t, v, h, a, now_iso, now_iso))
    
    # Seed bonds
    db.conn.execute("INSERT OR IGNORE INTO bonds (ticker, issuer, coupon_rate, nominal, buy_price, shares, maturity, insured, broker, account) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    ("ACMT2B5", "Agat Credit", 25, 100000, 109607, 96, "2028-05-21", 1, "EXTURE+G", "IIS"))
    db.conn.execute("INSERT OR IGNORE INTO bonds (ticker, issuer, coupon_rate, nominal, buy_price, shares, maturity, insured, broker, account) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    ("ACMT2B4", "Agat Credit", 26, 100000, 105000, 93, "2028-01-16", 1, "EXTURE+G", "IIS"))
    
    db.conn.commit()
    return {"status": "seeded"}


@app.on_event("startup")
def startup():
    init_trades()
    # Ensure tables exist
    db = DB()
    db.conn.execute("""CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL,
        value REAL, horizon TEXT, analyst TEXT, as_of TEXT, created_at TEXT
    )""")
    db.conn.execute("""CREATE TABLE IF NOT EXISTS catalysts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, date TEXT,
        fuzzy_label TEXT, kind TEXT, label TEXT, status TEXT DEFAULT 'confirmed',
        created_at TEXT
    )""")
    db.conn.execute("""CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL,
        direction TEXT, status TEXT DEFAULT 'pending', order_type TEXT DEFAULT 'limit',
        limit_price REAL, shares REAL, filled_price REAL, filled_at TEXT,
        commission REAL, stop_loss REAL, take_profit REAL,
        rationale TEXT, created_at TEXT, updated_at TEXT
    )""")
    db.conn.execute("""CREATE TABLE IF NOT EXISTS bonds (
        ticker TEXT PRIMARY KEY, issuer TEXT NOT NULL,
        coupon_rate REAL, nominal REAL, buy_price REAL,
        shares REAL, maturity TEXT, insured INTEGER DEFAULT 0,
        insurer TEXT, broker TEXT, account TEXT DEFAULT 'IIS',
        updated_at TEXT
    )""")
    db.conn.commit()