"""
cache.py — Модуль кеширования для Stocks UZ (TASK-031).
Поддерживает Redis с авто-фоллбэком на In-Memory DictCache с учётом TTL.
"""

import json
import logging
import os
import time
from functools import wraps
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Попытка импорта redis
_redis_client = None
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

try:
    import redis
    _r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=1)
    _r.ping()
    _redis_client = _r
    logger.info("Redis кеш успешно подключён (%s:%d)", REDIS_HOST, REDIS_PORT)
except Exception:
    logger.info("Redis недоступен, используется In-Memory DictCache фоллбэк")
    _redis_client = None


class InMemoryCache:
    """Простой локальный кеш в памяти с поддержкой TTL."""

    def __init__(self):
        self._store = {}  # key -> (value, expire_at)

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        val, expire_at = self._store[key]
        if expire_at is not None and time.time() > expire_at:
            del self._store[key]
            return None
        return val

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        expire_at = (time.time() + ttl_seconds) if ttl_seconds else None
        self._store[key] = (value, expire_at)

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


_memory_cache = InMemoryCache()


def cache_get(key: str) -> Optional[Any]:
    """Получить значение из кеша (Redis или In-Memory)."""
    if _redis_client:
        try:
            raw = _redis_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning("Ошибка чтения Redis кеша: %s", e)
    return _memory_cache.get(key)


def cache_set(key: str, value: Any, ttl_seconds: int = 60):
    """Записать значение в кеш с заданным TTL."""
    if _redis_client:
        try:
            _redis_client.setex(key, ttl_seconds, json.dumps(value))
            return
        except Exception as e:
            logger.warning("Ошибка записи Redis кеша: %s", e)
    _memory_cache.set(key, value, ttl_seconds=ttl_seconds)


def cached(ttl_seconds: int = 60, key_prefix: str = ""):
    """Декоратор кеширования результатов функций."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix or func.__name__}:{str(args)}:{str(kwargs)}"
            val = cache_get(cache_key)
            if val is not None:
                return val
            result = func(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl_seconds=ttl_seconds)
            return result
        return wrapper
    return decorator
