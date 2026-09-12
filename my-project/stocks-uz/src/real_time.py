"""
real_time.py — Движок котировок реального времени для Stocks UZ (TASK-030).
Обеспечивает WebSocket-рассылку и Server-Sent Events (SSE) с котировками UZSE.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Set, List, Optional
try:
    from fastapi import WebSocket, WebSocketDisconnect
except ImportError:
    class WebSocket:
        pass
    class WebSocketDisconnect(Exception):
        pass


logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

# Поддерживаемые тикеры UZSE
TARGET_TICKERS = [
    "URTS", "BIOK", "ALKB", "CBSK", "SQBN", "HMKB",
    "UZTL", "UZMK", "IPTB", "KVTS", "AGMKP", "UZNF"
]

# Начальные эталонные цены UZS
BASE_PRICES: Dict[str, float] = {
    "URTS": 11200.0,
    "BIOK": 14500.0,
    "ALKB": 0.90,
    "CBSK": 3.45,
    "SQBN": 31.78,
    "HMKB": 65.50,
    "UZTL": 5900.0,
    "UZMK": 5550.0,
    "IPTB": 3.05,
    "KVTS": 2460.0,
    "AGMKP": 17000.0,
    "UZNF": 6.65,
}

class RealTimeManager:
    """Управление активными WebSocket-подключениями и рассылкой котировок."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.latest_prices: Dict[str, float] = dict(BASE_PRICES)
        self.price_history: Dict[str, List[dict]] = {t: [] for t in TARGET_TICKERS}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket клиент подключён: %s", websocket.client)
        # Отправить стартовый снимок цен
        snapshot = {
            "type": "snapshot",
            "data": self.latest_prices,
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
        await websocket.send_text(json.dumps(snapshot))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket клиент отключён")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        to_remove = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning("Ошибка отправки WebSocket: %s", e)
                to_remove.append(connection)
        for conn in to_remove:
            self.disconnect(conn)

    def update_price(self, ticker: str, new_price: float, volume: int = 100) -> dict:
        ticker = ticker.upper()
        old_price = self.latest_prices.get(ticker, new_price)
        change_pct = round(((new_price - old_price) / old_price * 100), 2) if old_price > 0 else 0.0
        self.latest_prices[ticker] = new_price

        update = {
            "ticker": ticker,
            "price": new_price,
            "old_price": old_price,
            "change_pct": change_pct,
            "volume": volume,
            "timestamp": datetime.now(TASHKENT).isoformat()
        }

        # Сохранить в истории
        if ticker in self.price_history:
            self.price_history[ticker].append(update)
            if len(self.price_history[ticker]) > 100:
                self.price_history[ticker].pop(0)

        return update

    def generate_random_tick(self) -> dict:
        """Симуляция тикового движения рынка UZSE для тестирования и стрима."""
        ticker = random.choice(TARGET_TICKERS)
        cur = self.latest_prices.get(ticker, 100.0)
        variation = random.uniform(-0.005, 0.005)
        new_price = round(cur * (1 + variation), 2) if cur > 10 else round(cur * (1 + variation), 4)
        vol = random.randint(10, 5000)
        return self.update_price(ticker, new_price, volume=vol)


# Глобальный экземпляр менеджера
rt_manager = RealTimeManager()
