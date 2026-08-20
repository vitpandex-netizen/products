"""GH Scout — Redis/Event Bus."""

import json
import logging
from typing import Optional, Dict, Any
from redis.asyncio import Redis as AsyncRedis
from core.config import settings

logger = logging.getLogger(__name__)

# Глобальный клиент
_redis: Optional[AsyncRedis] = None


async def get_redis() -> AsyncRedis:
    """Получить Redis клиент (singleton)."""
    global _redis
    if _redis is None:
        _redis = AsyncRedis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )
    return _redis


async def close_redis():
    """Закрыть Redis при shutdown."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def publish(channel: str, data: Dict[str, Any]):
    """Опубликовать событие в Redis Pub/Sub."""
    try:
        redis = await get_redis()
        full_channel = f"{settings.event_bus_prefix}:{channel}"
        await redis.publish(full_channel, json.dumps(data, default=str))
        logger.info(f"Published to {full_channel}: {data.get('type', 'unknown')}")
    except Exception as e:
        logger.error(f"Failed to publish to {channel}: {e}")


# ─── Каналы Event Bus ───

EVENT_CHANNELS = {
    "release": "ghscout:release",
    "trend": "ghscout:trend",
    "recommendation": "ghscout:recommendation",
    "digest": "ghscout:digest",
}


async def publish_release(project_name: str, release_tag: str, release_url: str, features: list):
    """Новый релиз отслеживаемого проекта."""
    await publish("release", {
        "type": "release",
        "project": project_name,
        "tag": release_tag,
        "url": release_url,
        "features": features,
        "timestamp": str(datetime.utcnow()),
    })


async def publish_trend(trend_name: str, repo_url: str, category: str, stars: int, relevance: float):
    """Новый тренд/быстрорастущий проект."""
    await publish("trend", {
        "type": "trend",
        "name": trend_name,
        "url": repo_url,
        "category": category,
        "stars": stars,
        "relevance": relevance,
        "timestamp": str(datetime.utcnow()),
    })


async def publish_recommendation(
    target_project: str, title: str, description: str,
    source_repo: str, priority: str
):
    """Новая рекомендация по улучшению."""
    await publish("recommendation", {
        "type": "recommendation",
        "target": target_project,
        "title": title,
        "description": description,
        "source": source_repo,
        "priority": priority,
        "timestamp": str(datetime.utcnow()),
    })


from datetime import datetime