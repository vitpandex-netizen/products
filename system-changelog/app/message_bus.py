"""System Change Log — Message Bus integration.

Async, fire-and-forget notifications to all agents.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

MESSAGE_BUS_URL = os.getenv("MESSAGE_BUS_URL", "http://100.84.223.96:8200")
SELF_NAME = "changelog"
AGENTS = [
    "sysadmin", "gh-scout", "finanalytics", "bgt", "datacore",
    "monitoring", "infra-status", "hermes", "anyidea", "consilium",
]


async def notify_agents(entry: dict) -> None:
    """Notify all agents via Message Bus in parallel (async fire & forget)."""
    text = (
        f"\U0001f4cb **Изменение:** {entry['summary']}\n"
        f"\u2514 Проект: `{entry['project']}` | Тип: `{entry['change_type']}`\n"
        f"\u2514 Автор: `{entry['author']}` | Статус: `{entry['status']}`\n"
        f"\u2514 Причина: {entry['reason'][:200]}\n"
        f"\u2514 ID: `{entry['id']}`"
    )

    async def _notify_one(agent: str):
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                await c.post(
                    f"{MESSAGE_BUS_URL}/messages",
                    json={
                        "from": SELF_NAME,
                        "to": agent,
                        "text": text,
                        "type": "changelog",
                        "entry_id": entry["id"],
                    },
                )
        except Exception as e:
            logger.warning("Failed to notify %s: %s", agent, e)

    import asyncio
    await asyncio.gather(*[_notify_one(a) for a in AGENTS], return_exceptions=True)


async def announce_change(entry: dict) -> None:
    """Full publication: Message Bus."""
    await notify_agents(entry)
    logger.info("Change announced: %s (%s)", entry["summary"], entry["id"])