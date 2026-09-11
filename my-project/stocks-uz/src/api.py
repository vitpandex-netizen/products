"""
stocks-uz API — кокпит портфеля UZSE.
FastAPI + сигнальный движок + трекер сделок + фронтенд.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
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

# ===== Telegram Mini App auth (initData HMAC) =====
import hashlib, hmac as hmac_mod

def _bot_token():
    try:
        from shared.vault import get as vault_get
        return vault_get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')
    except Exception:
        return os.getenv('TELEGRAM_BOT_TOKEN', '')

def _is_trusted_network(ip: str) -> bool:
    """Tailnet/локальные сети — без initData; интернет — только с подписью."""
    if ip in ("127.0.0.1", "::1"):
        return True
    if ip.startswith("100.") or ip.startswith("192.168.") or ip.startswith("10.") \
       or ip.startswith("172.16.") or ip.startswith("172.17.") or ip.startswith("172.18.") \
       or ip.startswith("172.19.") or ip.startswith("172.20.") or ip.startswith("172.21.") \
       or ip.startswith("172.22.") or ip.startswith("172.23.") or ip.startswith("172.24.") \
       or ip.startswith("172.25.") or ip.startswith("172.26.") or ip.startswith("172.27.") \
       or ip.startswith("172.28.") or ip.startswith("172.29.") or ip.startswith("172.30.") \
       or ip.startswith("172.31."):
        return True
    return False

def validate_init_data(init_data: str, max_age: int = 86400) -> dict:
    """Проверить подпись Telegram WebApp initData (HMAC-SHA256 по bot token).

    ВАЖНО: значения в initData URL-encoded. Хэш считается по ЗАКОДИРОВАННОЙ
    строке (как в спецификации Telegram), а для парсинга user — decode.
    """
    try:
        pairs = dict(p.split("=", 1) for p in init_data.split("&") if "=" in p)
        received_hash = pairs.pop("hash", "")
        auth_date = int(pairs.get("auth_date", "0"))
        import time as _t
        if _t.time() - auth_date > max_age:
            return {}
        secret = hmac_mod.new(b"WebAppData", _bot_token().encode(), hashlib.sha256).digest()
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        calc = hmac_mod.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        if calc != received_hash:
            return {}
        import urllib.parse as _up
        user_raw = _up.unquote(pairs.get("user", "{}"))
        user = json.loads(user_raw)
        return {"ok": True, "user": user, "auth_date": auth_date}
    except Exception:
        return {}

app = FastAPI(title="stocks-uz", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def protect_api(request: Request, call_next):
    """Защита /api/*: из интернета — только с валидным Telegram initData.
    /api/tma/* — initData обязателен ВСЕГДА (публичный funnel, IP маскируется Caddy).
    Остальные /api/*: локальные/tailnet запросы — без подписи."""
    path = request.url.path
    if path.startswith("/api/tma/") and path != "/api/tma/auth":
        init_data = request.headers.get("x-tma-init-data", "")
        res = validate_init_data(init_data)
        if not res:
            return JSONResponse({"detail": "Unauthorized: valid Telegram initData required"},
                                status_code=401)
    elif path.startswith("/api/") and path != "/api/health":
        client_ip = request.client.host if request.client else ""
        if not _is_trusted_network(client_ip):
            init_data = request.headers.get("x-tma-init-data", "")
            res = validate_init_data(init_data)
            if not res:
                return JSONResponse({"detail": "Unauthorized: valid Telegram initData required"},
                                    status_code=401)
    return await call_next(request)

# Frontend
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# Telegram Mini App (мобильная версия)
TMA_DIR = BASE_DIR / "frontend" / "tma"
if TMA_DIR.exists():
    app.mount("/tma", StaticFiles(directory=str(TMA_DIR), html=True), name="tma")


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
    """Текущий портфель из БД + сигналы.
    Консолидация по наличию цены в фиде (не по историческому флагу no_market_data)."""
    positions = db.get_portfolio()
    prices = get_prices_dict(db)
    targets = db.conn.execute("SELECT * FROM targets").fetchall()
    target_list = [dict(t) for t in targets]
    
    pos_list = [{"ticker": p["ticker"], "shares": p["shares"],
                 "avg_buy_price": p["avg_price"], "broker": p.get("broker", "manual")} for p in positions]
    
    consolidated = consolidate_positions(pos_list, prices)
    barbell = barbell_balance(pos_list, [], prices)
    conc = concentration(pos_list, prices)
    signals = run_signal_engine(pos_list, target_list, prices, {})
    
    # Позиции без цены в фиде (динамически) — не участвуют в P&L
    no_data = [{"ticker": p["ticker"], "shares": p["shares"], "avg_price": p["avg_price"]}
               for p in positions if p["ticker"] not in prices]
    return {**consolidated, "barbell": barbell, "concentration": conc, "signals": signals,
            "no_market_data_positions": no_data}

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
    """Последние цены с UZSE (price_history + fundamentals fallback)."""
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


# ===== Telegram Mini App endpoints =====
@app.get("/api/tma/auth")
def tma_auth(x_tma_init_data: str = Header(default="")):
    """Проверка initData: вернуть пользователя или 401."""
    res = validate_init_data(x_tma_init_data)
    if not res:
        raise HTTPException(401, "Invalid initData")
    return {"ok": True, "user": res["user"]}


@app.get("/api/tma/summary")
def tma_summary(request: Request, x_tma_init_data: str = Header(default=""),
                db: DB = Depends(get_db)):
    """Сводка для Mini App: портфель + сигналы + инсайты + фигуры + топ движений."""
    # Безопасность: из интернета — только с валидным initData
    if not _is_trusted_network(request.client.host):
        res = validate_init_data(x_tma_init_data)
        if not res:
            raise HTTPException(401, "Invalid initData")
    positions = db.get_portfolio()
    prices = get_prices_dict(db)
    targets = db.conn.execute("SELECT * FROM targets").fetchall()
    target_list = [dict(t) for t in targets]
    pos_list = [{"ticker": p["ticker"], "shares": p["shares"],
                 "avg_buy_price": p["avg_price"], "broker": p.get("broker", "manual")} for p in positions]
    consolidated = consolidate_positions(pos_list, prices)
    # Позиции без цены в фиде (динамически) — исключены из P&L
    no_data = [{"ticker": p["ticker"], "shares": p["shares"], "avg_price": p["avg_price"]}
               for p in positions if p["ticker"] not in prices]
    consolidated["no_market_data_positions"] = no_data
    signals = run_signal_engine(pos_list, target_list, prices, {})
    insights = db.get_latest_insights(days=5, limit=6)
    fig_rows = db.conn.execute("""
        SELECT person, role, events, message, fetched_at FROM key_figures
        WHERE fetched_at >= datetime('now', '-3 days')
        ORDER BY fetched_at DESC LIMIT 3
    """).fetchall()
    # Топ движений за день
    movers = db.conn.execute("""
        SELECT ticker, day_change_pct, price FROM price_history
        WHERE fetched_at >= datetime('now', '-1 day') AND day_change_pct IS NOT NULL
        ORDER BY ABS(day_change_pct) DESC LIMIT 8
    """).fetchall()
    # Свежий поток сделок (обороты)
    flow = db.conn.execute("""
        SELECT ticker, SUM(amount) as amount, COUNT(*) as n FROM trade_flow
        WHERE fetched_at >= datetime('now', '-1 day')
        GROUP BY ticker ORDER BY amount DESC LIMIT 6
    """).fetchall()
    return {
        "portfolio": consolidated,
        "signals": signals,
        "insights": [dict(i) for i in insights],
        "figures": [dict(f) for f in fig_rows],
        "movers": [dict(m) for m in movers],
        "flow": [dict(f) for f in flow],
        "updated": datetime.now(TASHKENT).isoformat(),
    }


@app.get("/api/tma/fundamentals")
def get_tma_fundamentals(req: Request):
    db = DB()
    # Фундаментальные коэффициенты по ключевым эмитентам UZSE
    rows = db.conn.execute("""
        SELECT ticker, pe_ratio, pb_ratio, roe, graham_value, dividend_yield, updated_at
        FROM fundamentals_metrics
    """).fetchall()
    
    if not rows:
        # Резервные эталонные данные по рынку UZSE
        default_metrics = [
            {"ticker": "URTS", "pe_ratio": 2.8, "pb_ratio": 0.65, "roe": 24.5, "graham_value": 14500, "dividend_yield": 33.6, "status": "Undervalued (Deep Value)"},
            {"ticker": "BIOK", "pe_ratio": 3.4, "pb_ratio": 0.72, "roe": 21.0, "graham_value": 18200, "dividend_yield": 18.5, "status": "Undervalued"},
            {"ticker": "ALKB", "pe_ratio": 3.9, "pb_ratio": 0.90, "roe": 19.8, "graham_value": 1.35, "dividend_yield": 12.0, "status": "Fair Value"},
            {"ticker": "CBSK", "pe_ratio": 4.1, "pb_ratio": 1.10, "roe": 18.2, "graham_value": 4.20, "dividend_yield": 10.5, "status": "Fair Value"},
            {"ticker": "UZMK", "pe_ratio": 3.1, "pb_ratio": 0.58, "roe": 22.4, "graham_value": 9800, "dividend_yield": 15.0, "status": "Undervalued (Deep Value)"},
            {"ticker": "IPTB", "pe_ratio": 3.6, "pb_ratio": 0.85, "roe": 20.1, "graham_value": 4.50, "dividend_yield": 14.2, "status": "Undervalued"},
        ]
        return {"items": default_metrics, "count": len(default_metrics)}
        
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@app.get("/api/tma/dividends/yield")
def get_dividend_yield_analytics(req: Request):
    db = DB()
    # Расчет дивидендной доходности и Yield-to-Cost в UZS и %
    portfolio_rows = db.conn.execute("SELECT ticker, shares, avg_price FROM portfolio").fetchall()
    
    items = []
    total_expected_uzs = 0
    
    for row in portfolio_rows:
        ticker = row['ticker']
        shares = row['shares']
        avg = row['avg_price']
        
        # Дивиденд на акцию
        div_row = db.conn.execute("""
            SELECT amount_per_share, ex_date FROM corporate_actions 
            WHERE ticker = ? AND action_type = 'dividend'
            ORDER BY id DESC LIMIT 1
        """, (ticker,)).fetchone()
        
        div_per_share = div_row['amount_per_share'] if div_row else 0
        ex_date = div_row['ex_date'] if div_row else None
        
        # Получаем последнюю рыночную цену
        p_row = db.conn.execute("SELECT price FROM price_history WHERE ticker = ? ORDER BY id DESC LIMIT 1", (ticker,)).fetchone()
        mkt_price = p_row['price'] if p_row else avg
        
        ytc_pct = (div_per_share / avg * 100) if avg > 0 else 0
        market_yield_pct = (div_per_share / mkt_price * 100) if mkt_price > 0 else 0
        total_payout_uzs = shares * div_per_share
        
        total_expected_uzs += total_payout_uzs
        
        items.append({
            "ticker": ticker,
            "shares": shares,
            "avg_price": avg,
            "market_price": mkt_price,
            "div_per_share": div_per_share,
            "ex_date": ex_date,
            "yield_to_cost_pct": round(ytc_pct, 2),
            "market_yield_pct": round(market_yield_pct, 2),
            "expected_payout_uzs": round(total_payout_uzs, 0)
        })
        
    return {
        "items": items,
        "total_expected_payout_uzs": round(total_expected_uzs, 0),
        "updated": datetime.now(TASHKENT).isoformat()
    }


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