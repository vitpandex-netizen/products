from fastapi import WebSocket
from typing import Set
import json
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
        logger.info(f"WebSocket connected: {len(self.connections)} total")

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)
        logger.info(f"WebSocket disconnected: {len(self.connections)} remaining")

    async def broadcast(self, channel: str, data: dict):
        """Рассылка всем подключенным клиентам."""
        message = json.dumps({"channel": channel, "data": data}, default=str)
        stale = set()
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception:
                stale.add(ws)
        for ws in stale:
            self.disconnect(ws)

    async def close(self):
        for ws in self.connections:
            try:
                await ws.close()
            except Exception:
                pass
        self.connections.clear()


ws_manager = WebSocketManager()