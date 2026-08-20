from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, Text, 
    ForeignKey, JSON, Index
)
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ, JSONB

from app.db import Base


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = {"schema": "analytics"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(64), nullable=False)
    signal_type = Column(String(64), nullable=False)
    symbol = Column(String(64))
    direction = Column(String(8))
    strength = Column(Numeric(5, 2))
    price_at_signal = Column(Numeric(20, 8))
    target_price = Column(Numeric(20, 8))
    reason = Column(Text)
    meta = Column(JSONB)
    ts = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False, index=True)


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = {"schema": "analytics"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_name = Column(String(64), nullable=False)
    symbol = Column(String(64), nullable=False)
    side = Column(String(8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    value_usd = Column(Numeric(20, 4))
    fee = Column(Numeric(20, 8))
    pnl = Column(Numeric(20, 8))
    signal_id = Column(BigInteger, ForeignKey("analytics.signals.id"))
    meta = Column(JSONB)
    ts = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False, index=True)