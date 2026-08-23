from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.repository import RequestRepository
from src.db.session import get_session

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, session: AsyncSession = Depends(get_session)):
    """Dashboard home page."""
    repo = RequestRepository(session)
    requests = await repo.list_recent(limit=20)
    return templates.TemplateResponse(
        request,
        "index.html",
        {"requests": requests},
    )


@router.get("/request/{request_id}", response_class=HTMLResponse)
async def detail(request: Request, request_id: str, session: AsyncSession = Depends(get_session)):
    """Request detail page."""
    from uuid import UUID
    repo = RequestRepository(session)
    req = await repo.get_with_responses(UUID(request_id))
    if not req:
        return HTMLResponse("Request not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"req": req},
    )


# API endpoints for dashboard data
@router.get("/api/requests")
async def api_requests(session: AsyncSession = Depends(get_session)):
    """API: list recent requests."""
    repo = RequestRepository(session)
    requests = await repo.list_recent(limit=50)
    return [
        {
            "id": str(r.id),
            "user_id": r.user_id,
            "question": r.question[:100],
            "mode": r.mode,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in requests
    ]


@router.get("/api/requests/{request_id}")
async def api_request_detail(request_id: str, session: AsyncSession = Depends(get_session)):
    """API: request detail with responses."""
    from uuid import UUID
    repo = RequestRepository(session)
    req = await repo.get_with_responses(UUID(request_id))
    if not req:
        return {"error": "not found"}
    
    return {
        "id": str(req.id),
        "user_id": req.user_id,
        "question": req.question,
        "mode": req.mode,
        "status": req.status,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "completed_at": req.completed_at.isoformat() if req.completed_at else None,
        "responses": [
            {
                "role": r.role,
                "model": r.model,
                "response_text": r.response_text,
                "tokens_in": r.tokens_in,
                "tokens_out": r.tokens_out,
                "cost": r.cost,
                "latency_ms": r.latency_ms,
            }
            for r in req.responses
        ],
    }