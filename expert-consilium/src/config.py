from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Service
    service_name: str = "consilium"
    log_level: str = "INFO"
    api_port: int = 8007
    debug: bool = False
    
    # PostgreSQL
    pg_user: str = "consilium"
    pg_password: str = "change_me"
    pg_db: str = "consilium"
    pg_host: str = "postgres"
    pg_port: int = 5432
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    @property
    def redis_stream_key(self) -> str:
        return "consilium:tasks"
    
    @property
    def redis_result_prefix(self) -> str:
        return "consilium:results:"
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: int = -1004297012607
    telegram_topic_id: int = 7941
    
    @property
    def telegram_webhook_url(self) -> str | None:
        url = os.getenv("TELEGRAM_WEBHOOK_URL")
        return url or None
    
    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    site_url: str = "http://100.84.223.96"
    site_name: str = "ExpertConsilium"
    
    # Models - basic
    model_strategist_basic: str = "deepseek/deepseek-v4-flash"
    model_analyst_basic: str = "google/gemini-2.5-flash"
    model_critic_basic: str = "anthropic/claude-4-haiku"
    model_creative_basic: str = "openai/gpt-4o-mini"
    model_synthesizer_basic: str = "grok/grok-3-mini"
    
    # Models - premium
    model_strategist_premium: str = "deepseek/deepseek-v4"
    model_analyst_premium: str = "google/gemini-2.5-pro"
    model_critic_premium: str = "anthropic/claude-sonnet-4"
    model_creative_premium: str = "openai/gpt-4o"
    model_synthesizer_premium: str = "grok/grok-3"
    
    # Limits
    cost_daily_limit: float = 0.50
    rate_limit_per_user: int = 10
    max_question_length: int = 5000
    default_mode: str = "basic"
    
    # Paths
    @property
    def templates_dir(self) -> Path:
        return Path(__file__).parent / "web" / "templates"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()