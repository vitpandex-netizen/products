from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ExpertResponse, Feedback, Request


class RequestRepository:
    """Repository for requests table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, question: str, mode: str = "basic",
                     username: str | None = None, complexity_score: float | None = None) -> Request:
        request = Request(
            user_id=user_id,
            username=username,
            question=question,
            mode=mode,
            complexity_score=complexity_score,
            status="pending",
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def get(self, request_id: UUID) -> Request | None:
        result = await self.session.execute(
            select(Request).where(Request.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_with_responses(self, request_id: UUID) -> Request | None:
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(Request)
            .options(selectinload(Request.responses))
            .where(Request.id == request_id)
        )
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20, offset: int = 0) -> list[Request]:
        result = await self.session.execute(
            select(Request)
            .order_by(Request.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self, request_id: UUID, status: str) -> None:
        await self.session.execute(
            update(Request)
            .where(Request.id == request_id)
            .values(status=status)
        )
        await self.session.flush()

    async def mark_completed(self, request_id: UUID) -> None:
        await self.session.execute(
            update(Request)
            .where(Request.id == request_id)
            .values(status="completed", completed_at=datetime.utcnow())
        )
        await self.session.flush()


class ExpertResponseRepository:
    """Repository for expert_responses table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request_id: UUID, role: str, model: str,
                     response_text: str, tokens_in: int = 0,
                     tokens_out: int = 0, cost: float = 0.0,
                     latency_ms: int = 0) -> ExpertResponse:
        resp = ExpertResponse(
            request_id=request_id,
            role=role,
            model=model,
            response_text=response_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            latency_ms=latency_ms,
        )
        self.session.add(resp)
        await self.session.flush()
        return resp


class FeedbackRepository:
    """Repository for feedback table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request_id: UUID, user_id: int,
                     rating: int, comment: str | None = None) -> Feedback:
        fb = Feedback(
            request_id=request_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )
        self.session.add(fb)
        await self.session.flush()
        return fb