from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://datacore:datacore_secret@localhost:5432/datacore"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change_me_in_prod"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()