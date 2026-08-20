"""GH Scout — конфигурация."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Service
    app_name: str = "GH Scout"
    debug: bool = False
    port: int = 8005

    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "ghscout"
    postgres_user: str = "ghscout"
    postgres_password: str = "ghscout_pass"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    # GitHub
    github_token: Optional[str] = None
    github_api_base: str = "https://api.github.com"

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Event Bus
    event_bus_prefix: str = "ghscout"

    # Schedule
    p0_interval_hours: int = 24   # Trading bots — ежедневно
    p1_interval_hours: int = 48   # DeFi/AI/ML — раз в 2 дня
    p2_interval_hours: int = 168  # FinTech — раз в неделю
    trending_interval_hours: int = 24  # Тренды — ежедневно

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()