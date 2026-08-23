"""System Change Log — SQLAlchemy models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./data/changelog.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class ChangeLogEntry(Base):
    """Единая запись об изменении в экосистеме."""

    __tablename__ = "changelog"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:12])
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    author = Column(String, nullable=False, index=True)        # hermes, sysadmin, gh-scout, etc.
    project = Column(String, nullable=False, index=True)       # datacore, bitget-bot, finanalytics, infra
    change_type = Column(String, nullable=False, index=True)   # feature, fix, config, deploy, infra, decision
    summary = Column(String, nullable=False)
    description = Column(Text, default="")
    reason = Column(Text, default="")                          # WHY this was done
    impact = Column(String, default="service")                 # system, service, user, all
    status = Column(String, default="completed", index=True)   # planned, in_progress, completed, rolled_back, failed
    links = Column(Text, default="")                           # JSON array of links (commits, sessions, tg)
    source = Column(String, default="hermes")                  # api, cli, telegram, cron

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "author": self.author,
            "project": self.project,
            "change_type": self.change_type,
            "summary": self.summary,
            "description": self.description,
            "reason": self.reason,
            "impact": self.impact,
            "status": self.status,
            "links": self.links,
            "source": self.source,
        }


def init_db():
    """Create tables and return session."""
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def get_db():
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()