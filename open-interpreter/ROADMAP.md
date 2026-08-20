# Roadmap — Open Interpreter

> **Статус**: v1.0.0 — Production-ready 24/7 monitoring system
> **Обновлено**: Август 2026

---

## Q3 2026 (текущий)

### 🔴 P0 — Критическое
- [ ] Graceful shutdown оркестратора (Signal handling)
- [ ] Валидация данных из внешних API (Yahoo Finance, HH.ru, UZSE)
- [ ] Настройка алертинга при падении сервисов

### 🟡 P1 — Важное
- [ ] **Dashboard** — веб-дашборд состояния всех сервисов
- [ ] **Multi-currency finance** — поддержка USD, UZS, RUB в finance-analytics
- [ ] **Auto-deploy** — GitHub Actions + cron deploy
- [ ] **Log rotation** — ротация логов оркестратора

### 🟢 P2 — Улучшения
- [ ] **Sentiment analysis** — анализ настроений рынка через LLM
- [ ] **Portfolio tracker** — отслеживание инвестиционного портфеля
- [ ] **Backup** — автоматический backup SQLite базы
- [ ] **Export** — экспорт данных в CSV/JSON
- [ ] **Тесты** — unit-тесты для shared модулей

---

## Q4 2026

- [ ] **Trading signals** — генерация торговых сигналов на основе LLM-анализа
- [ ] **Multi-user** — поддержка нескольких пользователей
- [ ] **Notification channels** — Email, SMS, Telegram
- [ ] **Webhook API** — внешние вызовы для CI/CD
- [ ] **Education Center** — мониторинг курсов и обучения
- [ ] **Passive Income Tracker** — отслеживание пассивного дохода

## Q1 2027

- [ ] **ML Pipeline** — обучение моделей прогнозирования на исторических данных
- [ ] **Portfolio optimization** — Markowitz efficient frontier
- [ ] **Risk assessment** — VaR, CVaR, stress testing
- [ ] **API Gateway** — единый API Gateway для всех сервисов
- [ ] **Kubernetes** — миграция на K8s для масштабирования

## Q2 2027+

- [ ] **Auto-trading** — автоматическая торговля через брокерские API
- [ ] **NLP parsing** — извлечение финансовых данных из новостей
- [ ] **Anomaly detection** — ML-детекция аномалий на рынках
- [ ] **Mobile app** — Flutter приложение для мониторинга
- [ ] **Open source** — публикация как open-source решения