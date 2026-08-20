# 📊 DataCore

Единая шина данных и ядро аналитики. Сбор, хранение и анализ рыночных данных из множества источников.

**Статус:** 🟢 Production на US Server  
**Версия:** v0.1.0  
**Контейнеров:** 10 (все Up)

---

## Архитектура

```
datacore/
├── core/                    # FastAPI REST API (:8001)
│   └── app/
│       ├── api/             # prices, signals, prediction-markets, analytics
│       ├── models/          # SQLAlchemy модели
│       ├── db.py            # Подключение к БД
│       ├── config.py        # Настройки
│       └── websocket.py     # WebSocket менеджер
├── collectors/              # Сборщики данных
│   ├── base.py              # Базовый класс сборщика
│   ├── runner.py            # Менеджер запуска сборщиков
│   ├── collector_yahoo.py   # Yahoo Finance (42 символа)
│   ├── collector_polymarket.py # Polymarket (555 рынков)
│   ├── collector_bitget.py  # Bitget (баланс/позиции)
│   └── collector_news.py    # RSS новости
├── analytics/               # Аналитический движок
│   └── engine.py            # Сигналы и аномалии
├── admin/                   # Admin-дашборд (:8080)
│   └── main.py              # FastAPI + Jinja2 + HTMX + Chart.js
├── bot/                     # Telegram-бот
│   └── bot.py               # Дайджесты 3 раза/день
├── docker-compose.yml       # 10 контейнеров
└── scripts/                 # Init-скрипты
```

## Стек

| Компонент | Технология |
|-----------|-----------|
| API | Python / FastAPI |
| База данных | PostgreSQL 16 |
| Кэш | Redis 7 |
| Админка | FastAPI + Jinja2 + HTMX + Chart.js |
| Бот | python-telegram-bot |
| Сборщики | asyncpg, httpx, yfinance |
| Контейнеры | Docker / Docker Compose |
| Сервер | US Server (Ubuntu) |

## 10 Docker контейнеров

| Сервис | Порт | Назначение |
|--------|------|-----------|
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 |
| `core-api` | 8001 | REST API (prices, signals, markets) |
| `admin` | 8080 | Admin-дашборд |
| `collector-polymarket` | — | 555 prediction markets |
| `collector-yahoo` | — | 42 символа Yahoo Finance |
| `collector-bitget` | — | Баланс/позиции Bitget |
| `collector-news` | — | RSS мониторинг новостей |
| `analytics-engine` | — | Сигналы и аномалии |
| `telegram-bot` | — | Дайджесты 3 раза/день |

## API Endpoints

| Endpoint | Описание |
|----------|---------|
| `GET /health` | Проверка здоровья |
| `GET /api/v1/prices` | Цены Yahoo символов |
| `GET /api/v1/prediction-markets` | Prediction markets (Polymarket) |
| `GET /api/v1/signals` | Аналитические сигналы |
| `GET /api/v1/analytics` | Аналитические данные |
| WebSocket `/ws` | Real-time подписка |

## Быстрый старт

### 1. Клонировать и настроить

```bash
git clone <repo>
cd datacore
cp .env.example .env  # настроить ключи
```

### 2. Запустить

```bash
docker compose up -d
```

### 3. Проверить

```bash
curl http://localhost:8001/health
# {"status": "ok", "version": "0.1.0"}
```

## Метрики

- **Данных:** 42 символа Yahoo, 555 prediction markets, 183+ сигналов
- **Uptime:** 8+ часов (с момента запуска)
- **Telegram:** 3 дайджеста/день (UZ Stocks, US Stocks, DataCore Signals)
- **API:** :8001 — доступен
- **Админка:** :8080 — доступна

## Управление

```bash
# Статус контейнеров
docker compose ps

# Логи
docker compose logs -f core-api
docker compose logs -f analytics-engine

# Рестарт
docker compose restart core-api
```

## Интеграции

- **FinAnalytics** — потребитель API DataCore
- **Bitget-bot** — синхронизация сделок
- **Telegram** — дайджесты в топики (UZ Stocks, US Stocks, DataCore Signals)
- **Polymarket** — 555 prediction markets
- **Yahoo Finance** — 42 символа
- **RSS** — новостные ленты

## Лицензия

Internal use only.