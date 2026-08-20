"""Базовый класс для всех сборщиков данных."""
import abc
import time
import logging
import json
from datetime import datetime, timezone
from typing import Optional

import httpx


logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    """Абстрактный сборщик данных.

    Наследники реализуют fetch() и store().
    """

    def __init__(self, name: str, api_url: str, db_url: Optional[str] = None):
        self.name = name
        self.api_url = api_url
        self.db_url = db_url
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "DataCore/1.0 (hermes-agent)"},
        )

    @abc.abstractmethod
    def fetch(self) -> list[dict]:
        """Забрать данные из источника."""
        ...

    @abc.abstractmethod
    def store(self, data: list[dict]) -> int:
        """Сохранить данные в БД. Возвращает количество записей."""
        ...

    def run_once(self) -> dict:
        """Один цикл: fetch → store → log."""
        start = time.time()
        try:
            data = self.fetch()
            count = self.store(data) if data else 0
            duration = int((time.time() - start) * 1000)
            logger.info(
                "%s: fetched %d items in %dms",
                self.name, len(data), duration,
            )
            return {"status": "success", "items": count, "duration_ms": duration}
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("%s: error after %dms: %s", self.name, duration, str(e))
            return {"status": "error", "error": str(e), "duration_ms": duration}

    def close(self):
        self.client.close()