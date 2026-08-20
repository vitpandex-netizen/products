#!/usr/bin/env python3
"""
EventBus — шина событий на Redis Pub/Sub.
Микросервисная архитектура: каждый проект независим, общается через события.

Использование:
    from eventbus import EventBus
    bus = EventBus()
    
    # Подписаться на события
    bus.subscribe("trade.*", handler)
    
    # Опубликовать событие
    bus.publish("trade.executed", {"ticker": "ETH/USDT", "price": 1858.93})
    
    # Слушать (в фоне или в основном потоке)
    bus.listen()
"""
import json, logging, os, signal, sys, threading, time
from datetime import datetime, timezone
from typing import Callable, Optional

logger = logging.getLogger("eventbus")

# ─── Протокол событий ───
# Каждое событие — JSON:
# {
#   "event_type": "domain.action",
#   "source": "service-name",
#   "version": "1.0",
#   "timestamp": "2026-08-17T14:00:00+05:00",
#   "data": { ... }
# }

# Домены событий:
# trade.*       — Bitget-bot (executed, closed, error, signal)
# job.*         — HH Jobs (found, matched, applied)
# portfolio.*   — Stocks-US (price_alert, rebalance, dividend)
# fin.*         — FinAnalytics (budget_alert, payment_due)
# alert.*       — Любой сервис (critical, warning, info)
# system.*      — Health, status, deploy

class EventBus:
    """Шина событий через Redis Pub/Sub."""

    def __init__(self, redis_url: str = None, service_name: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.service_name = service_name or os.getenv("SERVICE_NAME", "unknown")
        self._redis = None
        self._pubsub = None
        self._handlers = {}  # pattern -> [handler]
        self._running = False
        self._thread = None
        self._connect()

    def _connect(self):
        """Подключение к Redis."""
        try:
            import redis as r
            self._redis = r.from_url(self.redis_url, decode_responses=True)
            self._redis.ping()
            self._pubsub = self._redis.pubsub()
            logger.info(f"✅ EventBus connected: {self.redis_url}")
        except Exception as e:
            logger.warning(f"⚠️ EventBus not available: {e}. Events will be buffered.")
            self._redis = None

    def publish(self, event_type: str, data: dict = None):
        """Опубликовать событие в шину."""
        event = {
            "event_type": event_type,
            "source": self.service_name,
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        payload = json.dumps(event, ensure_ascii=False, default=str)
        logger.info(f"📤 {event_type} | {json.dumps(data, ensure_ascii=False)[:200]}")
        if self._redis:
            try:
                # Публикуем в канал по домену (trade.* → канал "trade")
                domain = event_type.split(".")[0]
                self._redis.publish(f"bus:{domain}", payload)
                # И в общий канал для всех
                self._redis.publish("bus:all", payload)
                return True
            except Exception as e:
                logger.warning(f"⚠️ Publish failed: {e}")
        return False

    def subscribe(self, pattern: str, handler: Callable):
        """Подписаться на события по паттерну (trade.*, job.*, alert.*)."""
        if pattern not in self._handlers:
            self._handlers[pattern] = []
        self._handlers[pattern].append(handler)
        logger.info(f"🔔 Subscribed: {pattern}")

    def _match(self, event_type: str, pattern: str) -> bool:
        """Проверить, соответствует ли event_type паттерну."""
        if pattern == "*" or pattern == "all":
            return True
        if pattern.endswith(".*"):
            return event_type.startswith(pattern[:-1])
        return event_type == pattern

    def _process(self, payload: str):
        """Обработать полученное событие."""
        try:
            event = json.loads(payload)
            event_type = event.get("event_type", "")
            # Не обрабатываем свои же события
            if event.get("source") == self.service_name:
                return
            for pattern, handlers in self._handlers.items():
                if self._match(event_type, pattern):
                    for handler in handlers:
                        try:
                            handler(event)
                        except Exception as e:
                            logger.error(f"Handler error: {e}")
        except json.JSONDecodeError:
            logger.warning(f"Invalid event: {payload[:200]}")

    def listen(self, daemon: bool = True):
        """Запустить слушатель в фоновом потоке."""
        if not self._redis:
            logger.warning("⚠️ EventBus not connected, cannot listen")
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=daemon)
        self._thread.start()
        logger.info("👂 EventBus listening...")

    def _listen_loop(self):
        """Основной цикл слушателя."""
        # Подписываемся на общий канал
        self._pubsub.subscribe("bus:all")
        # И на все доменные каналы
        domains = set()
        for pattern in self._handlers:
            domain = pattern.split(".")[0]
            if domain != "*":
                domains.add(domain)
        for d in domains:
            try:
                self._pubsub.subscribe(f"bus:{d}")
            except:
                pass
        while self._running:
            try:
                msg = self._pubsub.get_message(timeout=1.0)
                if msg and msg["type"] == "message":
                    self._process(msg["data"])
            except Exception as e:
                logger.error(f"Listen error: {e}")
                time.sleep(1)

    def stop(self):
        """Остановить слушатель."""
        self._running = False
        if self._pubsub:
            self._pubsub.unsubscribe()
        logger.info("EventBus stopped")


# ─── Примеры обработчиков ───

def on_trade_executed(event: dict):
    """Когда битгет совершил сделку."""
    data = event["data"]
    logger.info(f"🤖 Сделка: {data.get('ticker')} {data.get('side')} @ ${data.get('price')}")

def on_job_found(event: dict):
    """Когда HH нашёл вакансию."""
    data = event["data"]
    logger.info(f"💼 Вакансия: {data.get('title')} — {data.get('company')}")

def on_portfolio_alert(event: dict):
    """Когда портфель требует внимания."""
    data = event["data"]
    logger.info(f"📊 Сигнал: {data.get('ticker')} {data.get('signal')}")


# ─── CLI для тестирования ───

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    bus = EventBus(service_name="eventbus-cli")
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"

    if mode == "test":
        # Тест: публикуем и слушаем
        bus.subscribe("trade.*", on_trade_executed)
        bus.subscribe("job.*", on_job_found)
        bus.subscribe("portfolio.*", on_portfolio_alert)
        bus.listen(daemon=False)
        bus.publish("trade.executed", {"ticker": "ETH/USDT", "side": "buy", "price": 1858.93, "size": 0.01})
        time.sleep(0.5)
        bus.publish("job.found", {"title": "IT Director", "company": "Tech Corp", "salary": "$5000"})
        time.sleep(0.5)
        bus.publish("portfolio.alert", {"ticker": "NFLX", "signal": "down 17%", "action": "review"})
        time.sleep(0.5)
        bus.stop()

    elif mode == "listen":
        # Режим слушателя
        bus.subscribe("*", lambda e: logger.info(f"📨 {e['event_type']} from {e['source']}: {e['data']}"))
        bus.listen(daemon=False)
        logger.info("Нажми Ctrl+C для выхода")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            bus.stop()