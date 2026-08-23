import json, os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import (init_db, SessionLocal, Instrument, Position, PricePoint,
                    Target, Catalyst, Bond, Rule, Alert, AuditEntry, now)
from engine import (consolidate_positions, barbell_balance, concentration,
                    run_signal_engine, bonds_summary)

app = FastAPI(title="HERMES", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve frontend static files (MUST be after API routes)
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_rules_dict(db: Session) -> dict:
    rules = db.query(Rule).filter(Rule.enabled == True).all()
    result = {}
    for r in rules:
        params = json.loads(r.params or "{}")
        result[r.name] = params.get("value", 0)
    return result


def get_prices_dict(db: Session) -> dict[str, float]:
    from sqlalchemy import text
    rows = db.execute(text("""
        SELECT p.ticker, p.price FROM prices p
        WHERE p.id IN (SELECT MAX(id) FROM prices GROUP BY ticker)
    """)).fetchall()
    return {r[0]: r[1] for r in rows}


class PositionCreate(BaseModel):
    ticker: str; broker: str; shares: float; avg_buy_price: float
    account: str = "regular"; source: str = "manual"

class TargetCreate(BaseModel):
    ticker: str; value: float; horizon: str; analyst: str
    as_of: str = None; source: str = None; rationale: str = None

class PriceCreate(BaseModel):
    ticker: str; price: float; source: str = "manual"; as_of: str = None

class BondCreate(BaseModel):
    ticker: str; issuer: str; coupon_rate: float; nominal: float
    buy_price: float; shares: float; maturity: str; insured: bool = False
    insurer: str = None; broker: str; account: str = "IIS"

class CatalystCreate(BaseModel):
    ticker: str = None; date: str; fuzzy_label: str = None
    kind: str; label: str; recurring: bool = False; source: str = None

class RuleUpdate(BaseModel):
    name: str; value: float; enabled: bool = True


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/api/positions")
def list_positions(db: Session = Depends(get_db)):
    positions = db.query(Position).all()
    return {"positions": [{
        "id": p.id, "ticker": p.ticker, "broker": p.broker,
        "account": p.account, "shares": p.shares,
        "avg_buy_price": p.avg_buy_price, "source": p.source,
    } for p in positions]}

@app.post("/api/positions")
def add_position(pc: PositionCreate, db: Session = Depends(get_db)):
    pos = Position(**pc.model_dump(), updated_at=now())
    db.add(pos); db.commit()
    return {"status": "ok", "id": pos.id}

@app.delete("/api/positions/{pos_id}")
def delete_position(pos_id: int, db: Session = Depends(get_db)):
    pos = db.query(Position).filter(Position.id == pos_id).first()
    if not pos: raise HTTPException(404)
    db.delete(pos); db.commit()
    return {"status": "deleted"}

@app.get("/api/portfolio")
def portfolio(db: Session = Depends(get_db)):
    positions = db.query(Position).all()
    prices = get_prices_dict(db)
    pos_list = [{"ticker": p.ticker, "shares": p.shares,
                 "avg_buy_price": p.avg_buy_price, "broker": p.broker,
                 "account": p.account} for p in positions]
    consolidated = consolidate_positions(pos_list, prices)
    barbell = barbell_balance(pos_list, [], prices)
    conc = concentration(pos_list, prices)
    return {**consolidated, "barbell": barbell, "concentration": conc}

@app.get("/api/signals")
def signals(db: Session = Depends(get_db)):
    positions = db.query(Position).all()
    prices = get_prices_dict(db)
    targets = db.query(Target).all()
    rules = get_rules_dict(db)
    pos_list = [{"ticker": p.ticker, "shares": p.shares,
                 "avg_buy_price": p.avg_buy_price, "broker": p.broker} for p in positions]
    target_list = [{"ticker": t.ticker, "value": t.value, "horizon": t.horizon,
                    "analyst": t.analyst, "as_of": t.as_of} for t in targets]
    return run_signal_engine(pos_list, target_list, prices, rules)

@app.get("/api/targets")
def list_targets(db: Session = Depends(get_db)):
    targets = db.query(Target).order_by(Target.ticker).all()
    return {"targets": [{
        "id": t.id, "ticker": t.ticker, "value": t.value,
        "horizon": t.horizon, "analyst": t.analyst, "as_of": t.as_of,
    } for t in targets]}

@app.post("/api/targets")
def add_target(tc: TargetCreate, db: Session = Depends(get_db)):
    target = Target(**tc.model_dump(), as_of=tc.as_of or now(), created_at=now())
    db.add(target); db.commit()
    return {"status": "ok", "id": target.id}

@app.get("/api/prices")
def list_prices(db: Session = Depends(get_db)):
    return {"prices": get_prices_dict(db)}

@app.post("/api/prices")
def add_price(pc: PriceCreate, db: Session = Depends(get_db)):
    pp = PricePoint(ticker=pc.ticker, price=pc.price,
                    as_of=pc.as_of or now(), source=pc.source)
    db.add(pp); db.commit()
    return {"status": "ok"}

@app.get("/api/bonds")
def list_bonds(db: Session = Depends(get_db)):
    bonds = db.query(Bond).all()
    bond_list = [{
        "ticker": b.ticker, "issuer": b.issuer, "coupon_rate": b.coupon_rate,
        "coupon_freq": b.coupon_freq, "nominal": b.nominal,
        "buy_price": b.buy_price, "shares": b.shares,
        "maturity": b.maturity, "insured": b.insured,
        "insurer": b.insurer, "broker": b.broker, "account": b.account,
    } for b in bonds]
    return {"bonds": bond_list, "summary": bonds_summary(bond_list)}

@app.post("/api/bonds")
def add_bond(bc: BondCreate, db: Session = Depends(get_db)):
    bond = Bond(**bc.model_dump(), updated_at=now())
    db.add(bond); db.commit()
    return {"status": "ok", "ticker": bond.ticker}

@app.get("/api/catalysts")
def list_catalysts(db: Session = Depends(get_db)):
    cats = db.query(Catalyst).order_by(Catalyst.date).all()
    return {"catalysts": [{
        "id": c.id, "ticker": c.ticker, "date": c.date,
        "fuzzy_label": c.fuzzy_label, "kind": c.kind,
        "label": c.label, "recurring": c.recurring, "status": c.status,
    } for c in cats]}

@app.post("/api/catalysts")
def add_catalyst(cc: CatalystCreate, db: Session = Depends(get_db)):
    cat = Catalyst(**cc.model_dump(), created_at=now())
    db.add(cat); db.commit()
    return {"status": "ok", "id": cat.id}

@app.get("/api/rules")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(Rule).all()
    return {"rules": [{
        "id": r.id, "name": r.name, "enabled": r.enabled,
        "params": json.loads(r.params or "{}"),
    } for r in rules]}

@app.post("/api/rules")
def update_rule(ru: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.name == ru.name).first()
    if rule:
        rule.params = json.dumps({"value": ru.value})
        rule.enabled = ru.enabled
    else:
        rule = Rule(name=ru.name, enabled=ru.enabled,
                    params=json.dumps({"value": ru.value}))
        db.add(rule)
    db.commit()
    return {"status": "ok"}

@app.get("/api/alerts")
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).filter(Alert.acknowledged == False).all()
    return {"alerts": [{
        "id": a.id, "ticker": a.ticker, "severity": a.severity,
        "message": a.message, "created_at": a.created_at,
    } for a in alerts]}

@app.post("/api/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a: raise HTTPException(404)
    a.acknowledged = True; db.commit()
    return {"status": "ok"}

@app.post("/api/seed")
def seed_data(db: Session = Depends(get_db)):
    if db.query(Position).first():
        return {"status": "already_seeded"}
    from data.seed import seed_all
    seed_all(db)
    return {"status": "seeded"}

@app.on_event("startup")
def startup():
    init_db()