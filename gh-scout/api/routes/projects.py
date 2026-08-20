"""GH Scout — API проектов."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.models import TrackedProject, Release, ExtractedFeature, Recommendation, Trend
from core.schemas import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    ReleaseOut, FeatureOut, RecommendationOut, TrendOut,
    IntegrationDigest, IntegrationQuery,
)

router = APIRouter()


# ─── Проекты ───

@router.get("/projects", response_model=List[ProjectOut])
async def list_projects(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = "active",
    db: AsyncSession = Depends(get_db),
):
    """Список отслеживаемых проектов."""
    query = select(TrackedProject)
    if category:
        query = query.where(TrackedProject.category == category)
    if priority:
        query = query.where(TrackedProject.priority == priority)
    if status:
        query = query.where(TrackedProject.status == status)
    query = query.order_by(TrackedProject.priority, TrackedProject.stars.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Добавить проект для отслеживания."""
    existing = await db.execute(
        select(TrackedProject).where(TrackedProject.repo_full_name == data.repo_full_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Project already tracked")

    project = TrackedProject(**data.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Детали проекта."""
    result = await db.execute(
        select(TrackedProject).where(TrackedProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int, data: ProjectUpdate, db: AsyncSession = Depends(get_db)
):
    """Обновить проект."""
    result = await db.execute(
        select(TrackedProject).where(TrackedProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)

    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить проект."""
    await db.execute(
        delete(TrackedProject).where(TrackedProject.id == project_id)
    )


# ─── Релизы ───

@router.get("/projects/{project_id}/releases", response_model=List[ReleaseOut])
async def list_releases(
    project_id: int,
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Релизы проекта."""
    result = await db.execute(
        select(Release)
        .where(Release.project_id == project_id)
        .order_by(Release.published_at.desc().nullslast())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/releases", response_model=List[ReleaseOut])
async def all_releases(
    since: Optional[datetime] = None,
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Все недавние релизы."""
    query = select(Release).order_by(Release.published_at.desc().nullslast())
    if since:
        query = query.where(Release.published_at >= since)
    result = await db.execute(query.limit(limit))
    return result.scalars().all()


# ─── Фичи ───

@router.get("/releases/{release_id}/features", response_model=List[FeatureOut])
async def list_features(
    release_id: int,
    relevance_min: float = Query(0.0, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """Извлечённые фичи из релиза."""
    query = select(ExtractedFeature).where(
        ExtractedFeature.release_id == release_id,
        ExtractedFeature.relevance >= relevance_min,
    )
    result = await db.execute(query)
    return result.scalars().all()


# ─── Рекомендации ───

@router.get("/recommendations", response_model=List[RecommendationOut])
async def list_recommendations(
    target_project: Optional[str] = None,
    status: Optional[str] = "new",
    priority: Optional[str] = None,
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Рекомендации для наших проектов."""
    query = select(Recommendation).order_by(
        Recommendation.priority.desc(),
        Recommendation.created_at.desc(),
    )
    if target_project:
        query = query.where(Recommendation.target_project == target_project)
    if status:
        query = query.where(Recommendation.status == status)
    if priority:
        query = query.where(Recommendation.priority == priority)

    result = await db.execute(query.limit(limit))
    return result.scalars().all()


@router.patch("/recommendations/{rec_id}/status", response_model=RecommendationOut)
async def update_recommendation_status(
    rec_id: int, status: str, db: AsyncSession = Depends(get_db)
):
    """Обновить статус рекомендации."""
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == rec_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Recommendation not found")
    rec.status = status
    await db.flush()
    await db.refresh(rec)
    return rec


# ─── Тренды ───

@router.get("/trends", response_model=List[TrendOut])
async def list_trends(
    category: Optional[str] = None,
    since: Optional[datetime] = None,
    min_relevance: float = Query(0.0, ge=0.0),
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Трендовые проекты."""
    query = select(Trend).order_by(Trend.relevance_score.desc(), Trend.stars.desc())
    if category:
        query = query.where(Trend.category == category)
    if since:
        query = query.where(Trend.trend_date >= since)
    if min_relevance:
        query = query.where(Trend.relevance_score >= min_relevance)

    result = await db.execute(query.limit(limit))
    return result.scalars().all()


# ─── Интеграции (для других ботов) ───

@router.post("/digest", response_model=IntegrationDigest)
async def get_digest(
    query: IntegrationQuery, db: AsyncSession = Depends(get_db)
):
    """Получить дайджест для внешнего сервиса."""
    since = query.since or datetime.utcnow()

    # Новые релизы по категориям
    releases_query = (
        select(Release)
        .join(TrackedProject)
        .where(Release.published_at >= since)
        .order_by(Release.published_at.desc())
        .limit(query.limit)
    )
    if query.categories:
        releases_query = releases_query.where(
            TrackedProject.category.in_(query.categories)
        )

    # Рекомендации для сервиса
    recs_query = (
        select(Recommendation)
        .where(
            Recommendation.target_project == query.service,
            Recommendation.status == "new",
        )
        .order_by(Recommendation.priority.desc())
        .limit(query.limit)
    )

    # Тренды
    trends_query = (
        select(Trend)
        .where(Trend.trend_date >= since)
        .order_by(Trend.relevance_score.desc())
        .limit(query.limit)
    )

    releases_result = await db.execute(releases_query)
    recs_result = await db.execute(recs_query)
    trends_result = await db.execute(trends_query)

    releases = releases_result.scalars().all()
    recs = recs_result.scalars().all()
    trends = trends_result.scalars().all()

    summary_parts = []
    if releases:
        summary_parts.append(f"{len(releases)} новых релизов")
    if recs:
        summary_parts.append(f"{len(recs)} новых рекомендаций")
    if trends:
        summary_parts.append(f"{len(trends)} новых трендов")

    return IntegrationDigest(
        new_releases=[r.__dict__ for r in releases],
        recommendations=[r.__dict__ for r in recs],
        new_trends=[t.__dict__ for t in trends],
        summary=", ".join(summary_parts) if summary_parts else "Нет новых данных",
    )


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "gh-scout", "version": "1.0.0"}