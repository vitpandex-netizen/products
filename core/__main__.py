"""GH Scout — Модуль инициализации.

Позволяет запускать как python -m core.
"""

from core.config import settings
from core.database import init_db, async_engine

import asyncio


async def main():
    print(f"Starting {settings.app_name}...")
    await init_db()
    print("Database initialized.")
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())