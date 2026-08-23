from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis as AsyncRedis

from src.config import settings

_redis: AsyncRedis | None = None


async def get_redis() -> AsyncRedis:
    """Get or create Redis connection."""
    global _redis
    if _redis is None:
        _redis = await AsyncRedis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=30.0,
            socket_connect_timeout=5.0,
        )
    return _redis


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


class TaskQueue:
    """Redis Stream-based task queue."""

    def __init__(self, redis: AsyncRedis):
        self.redis = redis
        self.stream_key = settings.redis_stream_key

    async def push_task(self, task: dict[str, Any]) -> str | None:
        """Push a task to the stream."""
        task_id = await self.redis.xadd(
            self.stream_key,
            {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
             for k, v in task.items()},
            maxlen=1000,
        )
        return task_id  # type: ignore[return-value]

    async def consume_tasks(self, group: str = "consilium-workers",
                            consumer: str = "worker-1",
                            batch_size: int = 1):
        """Consume tasks from the stream as a consumer group."""
        try:
            await self.redis.xgroup_create(self.stream_key, group, id="0", mkstream=True)
        except Exception:
            pass  # Group already exists

        results = await self.redis.xreadgroup(
            group, consumer, {self.stream_key: ">"},
            count=batch_size, block=5000,
        )

        messages = []
        if results:
            for stream_name, stream_messages in results:
                for msg_id, msg_data in stream_messages:
                    messages.append((msg_id, msg_data))

        return messages

    async def ack_task(self, msg_id: str, group: str = "consilium-workers") -> None:
        """Acknowledge task completion."""
        await self.redis.xack(self.stream_key, group, msg_id)


class ResultPublisher:
    """Publish expert results via Redis Pub/Sub."""

    def __init__(self, redis: AsyncRedis):
        self.redis = redis

    async def publish_expert_result(self, request_id: str, result: dict[str, Any]) -> None:
        """Publish a single expert's result."""
        channel = f"{settings.redis_result_prefix}{request_id}"
        await self.redis.publish(channel, json.dumps(result, default=str))

    async def publish_final_result(self, request_id: str, result: dict[str, Any]) -> None:
        """Publish the final synthesized result."""
        channel = f"{settings.redis_result_prefix}{request_id}:final"
        await self.redis.publish(channel, json.dumps(result, default=str))

    async def subscribe(self, request_id: str):
        """Subscribe to results for a request."""
        channel = f"{settings.redis_result_prefix}{request_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub