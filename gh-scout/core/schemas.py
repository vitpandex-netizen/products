"""GH Scout — Pydantic схемы."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ─── Проекты ───

class ProjectCreate(BaseModel):
    name: str
    repo_full_name: str
    repo_url: str
    description: str = ""
    category: str = "trading"
    subcategory: str = ""
    priority: str = "P1"
    tags: List[str] = []
    our_projects: List[str] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    our_projects: Optional[List[str]] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    repo_full_name: str
    repo_url: str
    description: str
    category: str
    subcategory: str
    priority: str
    status: str
    tags: List[str]
    our_projects: List[str]
    stars: int
    forks: int
    open_issues: int
    language: str
    last_release_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Релизы ───

class ReleaseOut(BaseModel):
    id: int
    project_id: int
    tag_name: str
    release_name: str
    body: str
    html_url: str
    published_at: Optional[datetime]
    prerelease: bool
    discovered_at: datetime
    is_processed: bool

    class Config:
        from_attributes = True


# ─── Фичи ───

class FeatureOut(BaseModel):
    id: int
    release_id: int
    project_id: int
    title: str
    description: str
    category: str
    relevance: float
    our_projects_tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Тренды ───

class TrendOut(BaseModel):
    id: int
    repo_full_name: str
    repo_url: str
    name: str
    description: str
    category: str
    language: str
    stars: int
    stars_today: int
    forks: int
    trend_date: datetime
    trend_source: str
    relevance_score: float
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Рекомендации ───

class RecommendationOut(BaseModel):
    id: int
    project_id: int
    feature_id: Optional[int]
    target_project: str
    title: str
    description: str
    source_repo: str
    source_release: str
    priority: str
    effort_estimate: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Интеграции ───

class IntegrationDigest(BaseModel):
    """Дайджест для внешних сервисов."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    new_releases: List[dict] = []
    new_trends: List[dict] = []
    recommendations: List[dict] = []
    summary: str = ""


class IntegrationQuery(BaseModel):
    """Запрос от внешнего сервиса."""
    service: str  # bitget-bot, finanalytics, anyidea
    since: Optional[datetime] = None
    categories: List[str] = []
    limit: int = 10