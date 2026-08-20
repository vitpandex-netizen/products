# Roadmap — NOFX

> **Статус**: MVP / Песочница (экспериментальная стадия)
> **Обновлено**: Август 2026

---

## Q3 2026 (текущий)

### 🔴 P0 — Критическое
- [ ] Настроить CORS для production (`CORS_ALLOWED_ORIGINS`)
- [ ] Добавить healthcheck для всех сервисов в docker-compose
- [ ] Реализовать обработку ошибок CoinAnk API (retry + fallback)

### 🟡 P1 — Важное
- [ ] Разработать локальный конфигуратор трейдеров (web UI)
- [ ] Добавить базовую стратегию AI-трейдера (simple MA crossover)
- [ ] Создать .env.example с документацией всех параметров
- [ ] Интегрировать Telegram-уведомления о сделках

### 🟢 P2 — Улучшения
- [ ] Написать тесты для API endpoints
- [ ] Добавить Prometheus-метрики для мониторинга
- [ ] Логирование через структурированный JSON (logfmt)
- [ ] Поддержка нескольких бирж через единый интерфейс

---

## Q4 2026

- [ ] **Multi-strategy engine** — параллельный запуск нескольких стратегий
- [ ] **Backtesting module** — тестирование стратегий на исторических данных
- [ ] **Risk management** — stop-loss, take-profit, позиционирование
- [ ] **Portfolio view** — агрегированная статистика по всем трейдерам
- [ ] **Telegram Bot** — управление трейдерами через Telegram

## Q1 2027

- [ ] **Competition mode** — публичный лидерборд между AI-трейдерами
- [ ] **Paper trading** — симуляция торговли без реальных средств
- [ ] **Model marketplace** — выбор и загрузка AI-моделей
- [ ] **Multi-user support** — разделение аккаунтов с ролями

## Q2 2027+

- [ ] **Real broker integration** — подключение к брокерам (Alpaca, Interactive Brokers)
- [ ] **ML pipeline** — обучение моделей на исторических данных
- [ ] **Mobile app** — React Native / Flutter клиент
- [ ] **Community plugins** — API для сторонних стратегий