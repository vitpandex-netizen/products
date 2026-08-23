"""
HERMES — Модели данных (SQLAlchemy).
Соответствуют спецификации из ТЗ §6.
"""
from datetime import datetime, timezone
from sqlalchemy import (Column, Integer, String, Float, Boolean, 
                        DateTime, Text, create_engine, JSON)
from sqlalchemy.orm import declarative_base, sessionmaker
import os, json

DB_PATH = os.getenv("HERMES_DB", "/app/data/hermes.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

TASHKENT = timezone.utc  # Will format in TZ for display

def now():
    return datetime.now(timezone.utc).isoformat()


class Instrument(Base):
    """Инструмент (акция, преф, облигация, фонд)"""
    __tablename__ = "instruments"
    ticker = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # equity, pref, bond, fund
    leg = Column(String, default="aggressive")  # aggressive, conservative
    sector = Column(String, nullable=True)
    ipo_thesis = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    updated_at = Column(String, default=now)


class Position(Base):
    """Позиция в портфеле"""
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    broker = Column(String, nullable=False)  # GoInvest, Jett, EXTURE+G
    account = Column(String, default="regular")  # regular, IIS
    shares = Column(Float, nullable=False)
    avg_buy_price = Column(Float, nullable=False)
    updated_at = Column(String, default=now)
    source = Column(String, default="manual")  # manual, import, ocr, playwright


class PricePoint(Base):
    """Цена инструмента"""
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    as_of = Column(String, nullable=False)
    source = Column(String, nullable=False)  # kapdepo:H27, uzse, manual
    created_at = Column(String, default=now)


class Target(Base):
    """Таргет (целевая цена) от аналитика"""
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    horizon = Column(String, nullable=False)  # 1Y, fundamental, internal_fund
    analyst = Column(String, nullable=False)  # KAP DEPO panorama, deep-dive, Freedom, UzNIF
    as_of = Column(String, nullable=False)
    source = Column(String, nullable=True)
    rationale = Column(String, nullable=True)
    created_at = Column(String, default=now)


class Catalyst(Base):
    """Катализатор (событие)"""
    __tablename__ = "catalysts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=True)
    date = Column(String, nullable=False)  # ISO
    fuzzy_label = Column(String, nullable=True)  # "2H 2027", "31 числа"
    kind = Column(String, nullable=False)  # ipo, dividend, coupon, maturity, decree, report, cash, todo
    label = Column(String, nullable=False)
    recurring = Column(Boolean, default=False)
    status = Column(String, default="confirmed")  # confirmed, draft, done
    source = Column(String, nullable=True)
    created_at = Column(String, default=now)


class Bond(Base):
    """Облигация (ИИС)"""
    __tablename__ = "bonds"
    ticker = Column(String, primary_key=True)
    issuer = Column(String, nullable=False)
    coupon_rate = Column(Float, nullable=False)  # % годовых
    coupon_freq = Column(Integer, default=4)  # выплат в год
    nominal = Column(Float, nullable=False)  # UZS
    buy_price = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    maturity = Column(String, nullable=False)  # ISO
    insured = Column(Boolean, default=False)
    insurer = Column(String, nullable=True)
    broker = Column(String, nullable=False)
    account = Column(String, default="IIS")
    updated_at = Column(String, default=now)


class Rule(Base):
    """Правило пользователя"""
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    enabled = Column(Boolean, default=True)
    params = Column(Text, default="{}")  # JSON

    def get_params(self):
        return json.loads(self.params or "{}")


class Alert(Base):
    """Алерт/уведомление"""
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, nullable=True)
    ticker = Column(String, nullable=True)
    severity = Column(String, nullable=False)  # sell, watch, buy, info
    message = Column(String, nullable=False)
    created_at = Column(String, default=now)
    acknowledged = Column(Boolean, default=False)


class AuditEntry(Base):
    """Аудит изменений"""
    __tablename__ = "audit"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(String, default=now)
    entity = Column(String, nullable=False)
    field = Column(String, nullable=False)
    old_val = Column(String, nullable=True)
    new_val = Column(String, nullable=True)
    source = Column(String, nullable=True)


def init_db():
    Base.metadata.create_all(engine)
    # Seed default rules
    session = SessionLocal()
    default_rules = [
        ("SELL_RATIO", {"value": 1.0}),
        ("SELL_HARD", {"value": 1.15}),
        ("NEAR_RATIO", {"value": 0.9}),
        ("CONTRA_PCT", {"value": 0.15}),
        ("SELL_CONFIRMATIONS", {"value": 2}),
        ("BUY_CONFIRMATIONS", {"value": 2}),
        ("CONCENTRATION_MAX", {"value": 0.25}),
        ("BARBELL_BOND_MIN", {"value": 0.35}),
        ("DIV_ALERT_DAYS", {"value": 5}),
    ]
    for name, params in default_rules:
        exists = session.query(Rule).filter(Rule.name == name).first()
        if not exists:
            session.add(Rule(name=name, enabled=True, params=json.dumps(params)))
    session.commit()
    session.close()