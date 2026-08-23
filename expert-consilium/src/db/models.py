from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Request(Base):
    __tablename__ = "requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    question = Column(Text, nullable=False)
    mode = Column(String(20), nullable=False, default="basic")
    complexity_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    responses = relationship("ExpertResponse", back_populates="request", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="request", cascade="all, delete-orphan")


class ExpertResponse(Base):
    __tablename__ = "expert_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    response_text = Column(Text, nullable=False)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    request = relationship("Request", back_populates="responses")


class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=True)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    request = relationship("Request", back_populates="feedback")