"""GH Scout — модели данных."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    Float, ForeignKey, JSON, Enum as SAEnum, Index
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class Priority(str, enum.Enum):
    P0 = "P0"  # Trading bots
    P1 = "P1"  # DeFi, AI/ML
    P2 = "P2"  # FinTech
    TRENDING = "TRENDING"  # Общие тренды


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class TrackedProject(Base):
    """Отслеживаемый GitHub проект."""
    __tablename__ = "tracked_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # human name
    repo_full_name = Column(String(255), nullable=False, unique=True)  # "owner/repo"
    repo_url = Column(String(512), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), nullable=False)  # trading, defi, ai_ml, fintech, devops, etc.
    subcategory = Column(String(100), default="")
    priority = Column(SAEnum(Priority), nullable=False, default=Priority.P1)
    status = Column(SAEnum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE)
    tags = Column(JSON, default=list)  # ["python", "trading", "binance"]
    our_projects = Column(JSON, default=list)  # ["bitget-bot", "finanalytics"]
    last_release_check = Column(DateTime, nullable=True)
    last_trend_check = Column(DateTime, nullable=True)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    language = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    releases = relationship("Release", back_populates="project", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_project_priority_status", "priority", "status"),
        Index("idx_project_category", "category"),
    )


class Release(Base):
    """Релиз отслеживаемого проекта."""
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("tracked_projects.id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String(255), nullable=False)
    release_name = Column(String(255), default="")
    body = Column(Text, default="")
    html_url = Column(String(512), nullable=False)
    published_at = Column(DateTime, nullable=True)
    prerelease = Column(Boolean, default=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)

    project = relationship("TrackedProject", back_populates="releases")
    features = relationship("ExtractedFeature", back_populates="release", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_release_project_id", "project_id"),
        Index("idx_release_published", "published_at"),
    )


class ExtractedFeature(Base):
    """Извлечённая фича из релиза."""
    __tablename__ = "extracted_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    release_id = Column(Integer, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("tracked_projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="")  # new_feature, improvement, fix, deprecation
    relevance = Column(Float, default=0.0)  # 0.0-1.0 relevance to our projects
    our_projects_tags = Column(JSON, default=list)  # which of our projects this applies to
    created_at = Column(DateTime, default=datetime.utcnow)

    release = relationship("Release", back_populates="features")
    project = relationship("TrackedProject")

    __table_args__ = (
        Index("idx_feature_project", "project_id"),
        Index("idx_feature_relevance", "relevance"),
    )


class Trend(Base):
    """Обнаруженный тренд/быстрорастущий проект."""
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), nullable=False)
    repo_url = Column(String(512), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="")  # самоопределяемая категория
    language = Column(String(50), default="")
    stars = Column(Integer, default=0)
    stars_today = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    trend_date = Column(DateTime, nullable=False)  # когда обнаружен
    trend_source = Column(String(50), default="github_trending")  # github_trending, github_discover
    relevance_score = Column(Float, default=0.0)  # насколько релевантно нашим проектам
    tags = Column(JSON, default=list)
    is_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_trend_date", "trend_date"),
        Index("idx_trend_relevance", "relevance_score"),
        Index("idx_trend_repo_date", "repo_full_name", "trend_date", unique=True),
    )


class Recommendation(Base):
    """Рекомендация по улучшению нашего проекта."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("tracked_projects.id", ondelete="CASCADE"), nullable=False)
    feature_id = Column(Integer, ForeignKey("extracted_features.id", ondelete="SET NULL"), nullable=True)
    target_project = Column(String(100), nullable=False)  # bitget-bot, finanalytics, anyidea, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_repo = Column(String(255), nullable=False)  # откуда подсмотрено
    source_release = Column(String(255), default="")  # тег релиза
    priority = Column(String(20), default="medium")  # critical, high, medium, low
    effort_estimate = Column(String(50), default="")  # hours/days
    status = Column(String(20), default="new")  # new, reviewed, accepted, rejected, implemented
    is_delivered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    project = relationship("TrackedProject", back_populates="recommendations")

    __table_args__ = (
        Index("idx_rec_target_status", "target_project", "status"),
        Index("idx_rec_priority", "priority"),
    )


class DeliveryLog(Base):
    """Лог доставки уведомлений."""
    __tablename__ = "delivery_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50), nullable=False)  # telegram, event_bus, webhook
    message_type = Column(String(50), nullable=False)  # release, trend, recommendation, digest
    content_preview = Column(String(255), default="")
    entity_type = Column(String(50), nullable=True)  # recommendation, trend, release
    entity_id = Column(Integer, nullable=True)
    status = Column(String(20), default="sent")  # sent, failed, pending
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)