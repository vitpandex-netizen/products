from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExpertResponseSchema(BaseModel):
    """Response from a single expert."""
    role: str
    model: str
    response_text: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    latency_ms: int = 0


class SynthesizedResult(BaseModel):
    """Final synthesized result from all experts."""
    consensus: str
    divergences: list[dict[str, str]] = []
    recommendation: str
    confidence: int  # 1-5
    experts_summary: list[dict[str, str]] = []


class RequestCreate(BaseModel):
    """Incoming request schema."""
    question: str
    user_id: int
    username: str | None = None
    mode: str | None = None  # None = auto-detect


class RequestResponse(BaseModel):
    """Response schema for API."""
    id: UUID
    user_id: int
    username: str | None
    question: str
    mode: str
    complexity_score: float | None
    status: str
    created_at: datetime
    completed_at: datetime | None
    responses: list[ExpertResponseSchema] = []


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "consilium"
    version: str = "0.1.0"