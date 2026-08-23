"""System Change Log — API routes."""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .models import ChangeLogEntry, get_db, init_db
from .schemas import ChangeLogCreate, ChangeLogResponse, ChangeLogUpdate, HealthResponse
from .message_bus import announce_change

logger = logging.getLogger(__name__)

router = APIRouter()


@router.on_event("startup")
def startup():
    init_db()
    logger.info("System Change Log DB initialized")


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    count = db.query(ChangeLogEntry).count()
    return HealthResponse(status="ok", version="1.0.0", entries_count=count)


@router.post("/changes", response_model=ChangeLogResponse, status_code=201)
async def create_change(change: ChangeLogCreate, db: Session = Depends(get_db)):
    """Создать запись об изменении и уведомить всех агентов."""
    entry = ChangeLogEntry(
        author=change.author,
        project=change.project,
        change_type=change.change_type,
        summary=change.summary,
        description=change.description,
        reason=change.reason,
        impact=change.impact,
        status=change.status,
        links=change.links,
        source=change.source,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Уведомить агентов в фоне
    try:
        await announce_change(entry.to_dict())
    except Exception as e:
        logger.warning("Announce failed (non-critical): %s", e)

    return entry.to_dict()


@router.get("/changes", response_model=list[ChangeLogResponse])
def list_changes(
    project: str = Query(None, description="Фильтр по проекту"),
    author: str = Query(None, description="Фильтр по автору"),
    change_type: str = Query(None, description="Фильтр по типу"),
    status: str = Query(None, description="Фильтр по статусу"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Получить историю изменений с фильтрацией."""
    query = db.query(ChangeLogEntry)

    if project:
        query = query.filter(ChangeLogEntry.project == project)
    if author:
        query = query.filter(ChangeLogEntry.author == author)
    if change_type:
        query = query.filter(ChangeLogEntry.change_type == change_type)
    if status:
        query = query.filter(ChangeLogEntry.status == status)

    entries = query.order_by(desc(ChangeLogEntry.timestamp)).offset(offset).limit(limit).all()
    return [e.to_dict() for e in entries]


@router.get("/changes/{change_id}", response_model=ChangeLogResponse)
def get_change(change_id: str, db: Session = Depends(get_db)):
    """Получить конкретную запись об изменении."""
    entry = db.query(ChangeLogEntry).filter(ChangeLogEntry.id == change_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Change not found")
    return entry.to_dict()


@router.patch("/changes/{change_id}", response_model=ChangeLogResponse)
def update_change(change_id: str, update: ChangeLogUpdate, db: Session = Depends(get_db)):
    """Обновить статус/описание изменения."""
    entry = db.query(ChangeLogEntry).filter(ChangeLogEntry.id == change_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Change not found")

    if update.status is not None:
        entry.status = update.status
    if update.description is not None:
        entry.description = update.description
    if update.links is not None:
        entry.links = update.links

    db.commit()
    db.refresh(entry)
    return entry.to_dict()


@router.get("/changes/stats/summary")
def changes_summary(db: Session = Depends(get_db)):
    """Статистика по изменениям."""
    total = db.query(ChangeLogEntry).count()
    by_project = db.query(
        ChangeLogEntry.project,
        ChangeLogEntry.status,
        func.count(ChangeLogEntry.id),
    ).group_by(ChangeLogEntry.project, ChangeLogEntry.status).all()

    by_type = db.query(
        ChangeLogEntry.change_type,
        func.count(ChangeLogEntry.id),
    ).group_by(ChangeLogEntry.change_type).all()

    recent = (
        db.query(ChangeLogEntry)
        .order_by(desc(ChangeLogEntry.timestamp))
        .limit(5)
        .all()
    )

    return {
        "total": total,
        "by_project": {f"{p}/{s}": c for p, s, c in by_project},
        "by_type": {t: c for t, c in by_type},
        "recent": [e.to_dict() for e in recent],
    }