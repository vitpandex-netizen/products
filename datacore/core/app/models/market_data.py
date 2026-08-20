from typing import Optional
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, Boolean, 
    DateTime, Text, ForeignKey, JSON, Index
)
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ, JSONB
from sqlalchemy.orm import relationship

from app.db import Base


class DataSource(Base):
    __tablename__ = "data_sources"
    __table_args__ = {"schema": "core"}

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    label = Column(String(128), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    config = Column(JSONB)
    created_at = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMPTZ, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    symbols = relationship("Symbol", back_populates="source")


class Symbol(Base):
    __tablename__ = "symbols"
    __table_args__ = {"schema": "core"}

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("core.data_sources.id"))
    symbol = Column(String(64), nullable=False)
    asset_type = Column(String(32), nullable=False)
    meta = Column(JSONB)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False)

    source = relationship("DataSource", back_populates="symbols")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = {"schema": "market_data"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol_id = Column(Integer, ForeignKey("core.symbols.id"), nullable=False)
    source = Column(String(64), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    bid = Column(Numeric(20, 8))
    ask = Column(Numeric(20, 8))
    volume = Column(Numeric(20, 4))
    ts = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False, index=True)


class PredictionMarket(Base):
    __tablename__ = "prediction_markets"
    __table_args__ = {"schema": "market_data"}

    id = Column(Integer, primary_key=True)
    condition_id = Column(String(128), unique=True, nullable=False)
    question = Column(Text, nullable=False)
    event_title = Column(String(256))
    event_slug = Column(String(128))
    category = Column(String(64))
    outcome_yes = Column(Numeric(10, 6), nullable=False)
    outcome_no = Column(Numeric(10, 6), nullable=False)
    volume = Column(Numeric(20, 4))
    liquidity = Column(Numeric(20, 4))
    open_interest = Column(Numeric(20, 4))
    active = Column(Boolean, default=True, nullable=False)
    closed = Column(Boolean, default=False, nullable=False)
    end_date = Column(TIMESTAMPTZ)
    last_updated = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False)
    created_at = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False)


class PredictionHistory(Base):
    __tablename__ = "prediction_history"
    __table_args__ = {"schema": "market_data"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    market_id = Column(Integer, ForeignKey("market_data.prediction_markets.id"), nullable=False)
    outcome_yes = Column(Numeric(10, 6), nullable=False)
    outcome_no = Column(Numeric(10, 6), nullable=False)
    volume = Column(Numeric(20, 4))
    ts = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False, index=True)


class OrderbookSnapshot(Base):
    __tablename__ = "orderbook_snapshots"
    __table_args__ = {"schema": "market_data"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol_id = Column(Integer, ForeignKey("core.symbols.id"), nullable=False)
    source = Column(String(64), nullable=False)
    bids = Column(JSONB)
    asks = Column(JSONB)
    spread = Column(Numeric(10, 6))
    mid_price = Column(Numeric(20, 8))
    ts = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False, index=True)