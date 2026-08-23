from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, Update
from redis.asyncio import Redis as AsyncRedis

from src.config import settings
from src.telegram.handlers import router as handlers_router
from src.telegram.keyboards import bot

logger = logging.getLogger(__name__)


async def on_startup(dispatcher: Dispatcher) -> None:
    """Setup on bot startup."""
    # Set commands
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="deep", description="Премиум-режим"),
        BotCommand(command="panel", description="Состав экспертов"),
        BotCommand(command="mode", description="Текущий режим"),
        BotCommand(command="history", description="История запросов"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot commands set")


async def on_shutdown(dispatcher: Dispatcher) -> None:
    """Cleanup on bot shutdown."""
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()


async def run_bot() -> None:
    """Run the Telegram bot."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.setLevel(logging.DEBUG)
    logging.getLogger("aiogram").setLevel(logging.DEBUG)
    logging.getLogger("src").setLevel(logging.DEBUG)

    # Redis storage for FSM
    redis = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
    storage = RedisStorage(redis)

    # Setup dispatcher
    dp = Dispatcher(storage=storage)
    dp.include_router(handlers_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting Telegram bot...")

    # Use webhook if configured, otherwise long polling
    if settings.telegram_webhook_url:
        webhook_url = f"{settings.telegram_webhook_url}/webhook"
        await bot.set_webhook(webhook_url, allowed_updates=dp.resolve_used_update_types())
        logger.info(f"Webhook set to {webhook_url}")
        # Run webhook polling (via FastAPI, not here)
        # For standalone bot, use polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "chat_member"],
        )


if __name__ == "__main__":
    asyncio.run(run_bot())