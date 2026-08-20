# Changelog: DataCore

## [0.1.0] — 2026-08-13

### Добавлено
- Первая стабильная версия DataCore
- 10 Docker контейнеров: postgres, redis, core-api, admin, 4 сборщика, analytics-engine, telegram-bot
- PostgreSQL 16 + Redis 7 инфраструктура
- FastAPI REST API: prices, signals, prediction-markets, analytics
- WebSocket менеджер для real-time подписки
- 4 сборщика данных:
  - **Polymarket** — 555 prediction markets
  - **Yahoo Finance** — 42 символа
  - **Bitget** — баланс/позиции
  - **RSS** — новостной мониторинг
- Analytics Engine — генерация сигналов и аномалий
- Admin-дашборд на FastAPI + Jinja2 + HTMX + Chart.js
- Telegram-бот с дайджестами 3 раза/день
- Telegram топики: UZ Stocks, US Stocks, DataCore Signals
- 183+ аналитических сигналов
- Project Management skill для проектов экосистемы