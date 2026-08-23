"""System Change Log — Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChangeLogCreate(BaseModel):
    author: str = Field(..., description="Кто сделал (hermes, sysadmin, gh-scout, ...)")
    project: str = Field(..., description="Проект (datacore, bitget-bot, finanalytics, infra, ...)")
    change_type: str = Field(..., description="feature | fix | config | deploy | infra | decision")
    summary: str = Field(..., description="Краткое описание изменения (макс 200 символов)")
    description: str = Field(default="", description="Подробное описание")
    reason: str = Field(default="", description="Почему это сделано")
    impact: str = Field(default="service", description="system | service | user | all")
    status: str = Field(default="completed", description="planned | in_progress | completed | rolled_back | failed")
    links: str = Field(default="[]", description='JSON-массив ссылок [{"type":"session","url":"..."}]')
    source: str = Field(default="api", description="api | cli | telegram | cron")


class ChangeLogUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None
    links: Optional[str] = None


class ChangeLogResponse(BaseModel):
    id: str
    timestamp: str
    author: str
    project: str
    change_type: str
    summary: str
    description: str
    reason: str
    impact: str
    status: str
    links: str
    source: str

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    version: str
    entries_count: int