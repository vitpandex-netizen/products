# AGENTS.md — расширенная память

## Архитектура (DataCore ядро)
- PostgreSQL + Redis (Pub/Sub шина) + Core REST API (:8001)
- Collectors — лёгкие скрипты (30-50 строк), только сбор данных → Core API
- Matcher, Notifier, Scheduler — единые сервисы, не дублировать
- Никаких отдельных SQLite/venv/vault-клиентов
- HH, Habr, Remote, Bitget, FinAnalytics — все на эту архитектуру

## Инфраструктура
| Сервер | Адрес | Роль | Характеристики |
|--------|-------|------|----------------|
| US Server | 100.84.223.96 / us.tailc8105c.ts.net | Основной 24/7 | 4 CPU, 8GB RAM, 145GB SSD, Ubuntu 24.04 |
| Mac | 100.89.205.45 | Разработка + AI | M1, 8GB RAM, Ollama qwen3:1.7b |
| Oracle | 100.94.224.89 | Exit node | 2 CPU, 954MB RAM, 45GB SSD |

Вход: http://us.tailc8105c.ts.net (Caddy). Весь трафик через Oracle WireGuard.

## PM-портфель (23 проекта)
**P0 ДЕНЬГИ:**
- bitget-bot: 🟢 $90.82, 0.01 ETH @ $1858.93, DCA Grid 2x. US Server 24/7.
- finanalytics: 🟡 Личные финансы. Нужно: запустить, кредиты, календарь.

**P1 РАБОТА:**
- hh-jobs: 🟢 RSS, 54kw/69sk, 161 match. Топик 15.
- hh-remote-jobs: 🟢 65 позиций, 4x/день. Топик 52.
- habr-jobs: 🟢 8 руководящих. Топик 15.
- remote-jobs: 🟢 8 remote. Топик 15.
- it-ops-framework: 🟢 v0.14.0. Продукт для CIO.

**P2 ИНВЕСТИЦИИ:**
- stocks-uz: 🟡 HMKB, 56 тикеров. Топик 576.
- stocks-us: 🟡 56 тикеров. Топик 577.

**P3 СЕРВИСЫ:**
- meeting-pipeline, hermes-webui, uz-market-bot, admin-panel, datacore, agents-toolkit, multi-agent-chat, project-dashboard, transcribe-bot/service, linkid-pro-post, scheduled-skills, project-notes, artifacts.

**⚫ STOP:** nofx, open-interpreter.

## Telegram
- Группа: AI Assistant -1004297012607
- Топики: 576 (UZ Stocks), 577 (US Stocks), 15 (HH-Jobs), 52 (HH-Remote), 127 (Passive Income), 203 (Мониторинг), 239 (FinAnalytics), 258 (InterP), 397 (DataCore Signals)

## Ключевые решения
- Всё в git → remote vitpandex-netizen
- Все ключи в vault (~/.secure/vault.enc, AES-256-CBC)
- PM стандарт: P0 деньги, P1 работа, P1-P3 инфра
- Экономия: сначала бесплатные модели, платные fallback
- Fallback: OpenRouter → Ollama qwen3:1.7b при отсутствии интернета
- Максимальная автоматизация — решать сам, не спрашивать
- "Action over words" — показывать результат, не объяснять план
- Требует глубины и деталей — production-grade, не MVP