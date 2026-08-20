from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, Index
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ

from app.db import Base


class CollectorLog(Base):
    __tablename__ = "collector_logs"
    __table_args__ = {"schema": "core"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    collector = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False)
    duration_ms = Column(Integer)
    items_count = Column(Integer)
    error_msg = Column(Text)
    ts = Column(TIMESTAMPTZ, default=datetime.utcnow, nullable=False, index=True)