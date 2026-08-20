# DataCore Event Bus — Архитектура

## 🎯 Концепция

```
┌──────────────────────────────────────────────────────────────────┐
│                     Шина данных (Redis Pub/Sub)                   │
│                          bus:all, bus:trade,                      │
│                     bus:job, bus:portfolio, bus:fin               │
└──────┬────────────┬────────────┬────────────┬────────────────────┘
       │            │            │            │
  ┌────▼───┐  ┌────▼───┐  ┌────▼───┐  ┌────▼────────┐
  │ Bitget │  │ HH     │  │ Stocks │  │ FinAnalytics │
  │ -bot   │  │ Jobs   │  │ -US    │  │              │
  └────────┘  └────────┘  └────────┘  └──────────────┘
  Своя БД     Своя БД     Своя БД     Своя БД
  (JSON)      (SQLite)    (SQLite)    (SQLite)
```

**Каждый сервис:**
- Имеет свою независимую БД
- Может работать автономно (без шины)
- Публикует события через шину
- Подписывается на события других сервисов

## 📡 Протокол событий

```json
{
  "event_type": "domain.action",
  "source": "bitget-bot",
  "version": "1.0",
  "timestamp": "2026-08-17T14:00:00+05:00",
  "data": { ... }
}
```

### Домены и события

| Домен | События | Источник | Потребители |
|-------|---------|----------|-------------|
| `trade` | executed, closed, error, signal | Bitget-bot | Stocks-US, FinAnalytics |
| `job` | found, matched, applied | HH Jobs | FinAnalytics |
| `portfolio` | summary, price_alert, rebalance | Stocks-US | FinAnalytics |
| `fin` | budget_alert, payment_due, expense | FinAnalytics | Все |
| `alert` | critical, warning, info | Любой | Telegram-bot |
| `system` | health, status, deploy | US Server | Все |

### Каналы Redis

| Канал | Назначение |
|-------|-----------|
| `bus:all` | Все события (для мониторинга) |
| `bus:trade` | Только торговые события |
| `bus:job` | Только события работы |
| `bus:portfolio` | Только события портфеля |
| `bus:fin` | Только финансовые события |

## 🏗️ Компоненты

### 1. EventBus (ядро)
- `/Users/vitaliyr/dev/datacore/eventbus.py`
- Клиентская библиотека для всех сервисов
- Подключается к Redis (локально или на US Server)

### 2. Интеграции
- `bitget-bot/eventbus_integration.py` — публикует сделки
- `stocks-us/eventbus_integration.py` — публикует портфель
- `hh-jobs/eventbus_integration.py` — публикует вакансии (TODO)
- `finanalytics/eventbus_integration.py` — публикует бюджет (TODO)

### 3. Event Viewer (дашборд)
- Веб-интерфейс для просмотра событий в реальном времени
- Слушает `bus:all` и показывает ленту

## 🚀 Как использовать

### Для разработчика нового сервиса:
```python
from eventbus import EventBus

bus = EventBus(service_name="my-service")
bus.listen(daemon=True)

# Опубликовать событие
bus.publish("alert.info", {"message": "Сервис запущен"})

# Подписаться на события
def on_trade(event):
    print(f"Сделка: {event['data']}")

bus.subscribe("trade.*", on_trade)
```

### Запуск Event Viewer:
```bash
cd /Users/vitaliyr/dev/datacore
python eventbus.py listen
```

## 🔒 Безопасность
- Redis только через Tailscale (не в публичном интернете)
- Каждый сервис имеет свой `service_name`
- События не содержат секретов (ключи, пароли)
- При падении Redis — сервисы продолжают работать