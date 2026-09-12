# 📋 Единый бэклог Триады (Triad Unified Backlog)

> **Статус:** Канонический реестр задач всей экосистемы (`Antigravity` + `Claude Code` + `Hermes` + `QA Team`).  
> **Правило:** Любая доработка, фикс бага или архитектурная задача **обязательно** фиксируется здесь с указанием Спринта, Приоритета, Ответственного Чата, Дедлайна и Definition of Done (DoD).

---

## 🎯 Спринты экосистемы

- **🏁 Спринт 1 (11 сентября 2026 г.):** Базовая инфраструктура BGT, Donchian-96, Daily Optimizer, Kill-Switch, Market Greed, Smart Scaling Out, Whale CVD Filter. *(Завершён)*
- **🏆 Спринт 2 (11 сентября 2026 г.):** HFT Binance Lead-Lag, Short Breakouts, Dynamic Leverage Engine, Paper Auto-Promoter, Executive Morning Digest, TMA Signals API. *(Завершён)*
- **🚀 Спринт 3 (12 сентября 2026 г.):** Масштабирование BGT: TMA "BGT Signals" UI, Machine Learning фильтр (XGBoost), Умный компаундинг депозита, Black Swan Circuit Breaker, TradingView Integration, рефакторинг God-Objects (funding_arb, strategies, bot), Infrastructure Package (CI/CD, Docker), Brain Audit Trail, Sharpe/Liquidity мониторы, Prometheus Exporter. *(Завершён — Все 33 задачи 🟢 Done)*

---

## 📊 Единый реестр задач спринтов

| ID | Спринт | Задача | Проект / Домен | Ответственный Чат / Бот | Исполнитель (Агент) | Приоритет | Срок | Статус |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **TASK-001** | **Спринт 1** | Восстановление `ghscout-core` (DNS коллизия postgres/redis) | **GH Scout** | Чат GH Scout (`@ghscout_bot`) | **Antigravity** | 🔴 P1 | 2026-09-12 | 🟢 Done |
| **TASK-002** | **Спринт 1** | Включение `datacore-pg`, `consilium`, `ghscout` в ночной бэкап | **DataCore / Consilium** | Чат DataCore / Master Orchestrator | **Antigravity** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-003** | **Спринт 1** | Сетевая изоляция API: биндинг портов `127.0.0.1` на US Server | **Инфраструктура / API** | Чат Master Orchestrator (Antigravity) | **Antigravity** | 🔴 P1 | 2026-09-12 | 🟢 Done |
| **TASK-004** | **Спринт 1** | Автоматизация приема баг‑репортов (QA Intake Engine `scripts/qa_intake.py`) | **QA Track / Триада** | Чат Master Orchestrator (Antigravity) | **Antigravity** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-HH-019** | **Спринт 3** | [HH Jobs] Ежедневный утренний Executive Digest (Top-5 вакансий в 09:00) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Antigravity** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-006** | **Спринт 1** | Разработка Единой политики Триады и стандартов релизного управления | **Экосистема / Триада** | Чат Master Orchestrator (Antigravity) | **Antigravity** | 🔴 P1 | 2026-09-12 | 🟢 Done |
| **TASK-007** | **Спринт 1** | [Stocks UZ] Не отображается график тикера URTS на мобильном TMA | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-008** | **Спринт 1** | [HH Jobs] Архивация и очистка неактуальных вакансий (Retention Policy) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-13 | 🟢 Done |
| **TASK-009** | **Спринт 1** | [HH Jobs] Полная персонализация AI‑матчинга под резюме пользователя | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-11 | 🟢 Done |
| **TASK-SYS-001** | **Спринт 1** | Оптимизация US Server (Quick Wins: очистка кэша Docker, vacuum journald) | **Инфраструктура / Сервер** | Чат Master Orchestrator (Antigravity) | **Antigravity** | 🟡 P2 | 2026-09-11 | 🟢 Done |
| **TASK-BGT-017** | **Спринт 1** | BGT: Динамический адаптивный фильтр волатильности (ATR Expansion Filter) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-11 | 🟢 Done |
| **TASK-ITOPS-001** | **Спринт 1** | Санитария US Server: архивация устаревшей копии `it-operations-framework` | **IT Operations** | Чат IT Ops | **Antigravity** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-ITOPS-002** | **Спринт 1** | Voice Operator & AI Agent: интеграция голосовых сообщений STT Whisper | **IT Operations** | Чат IT Ops | **Antigravity** | 🔴 P1 | 2026-09-13 | 🟢 Done |
| **TASK-ITOPS-003** | **Спринт 1** | Верификация и интеграция KB API (База знаний) в клиенты и документацию | **IT Operations** | Чат IT Ops | **Antigravity** | 🟡 P2 | 2026-09-14 | 🟢 Done |
| **TASK-ITOPS-004** | **Спринт 1** | Коммерческий пакет: финализация прайса (UZS), реквизитов и контракта пилота | **IT Operations** | Чат IT Ops | **Antigravity** | 🔴 P1 | 2026-09-14 | 🟢 Done |
| **TASK-ITOPS-006** | **Спринт 1** | Автоматизированный CI/CD пайплайн (GitHub Actions: lint, test, docker build) | **IT Operations** | Чат IT Ops | **Antigravity** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-LINKID-003** | **Спринт 2** | [LinkID] Устранение двойного парсинга новостей в скрипте `generate_posts.py` | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-LINKID-005** | **Спринт 2** | [LinkID] Self‑Healing LLM Fallback (авто‑переключение на Gemma‑4‑31B Free при 402) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P0 | 2026-09-12 | 🟢 Done |
| **TASK-LINKID-006** | **Спринт 2** | [LinkID] Фикс роутинга Funnel `/linkid` в Tailscale (устранение 404 / DOMException iOS) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P0 | 2026-09-12 | 🟢 Done |
| **TASK-LINKID-007** | **Спринт 2** | [LinkID] Синхронизация доступа для 5 Telegram ID (TELEGRAM_ADMIN_IDS) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P0 | 2026-09-12 | 🟢 Done |
| **TASK-LINKID-001** | **Спринт 2** | [LinkID] Динамический выбор LLM в веб‑админке (`:8015`) + сохранение в БД | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Чат LinkID** | 🔴 P1 | 2026-09-14 | 🟢 Done |
| **TASK-LINKID-002** | **Спринт 2** | [LinkID] Асинхронная очередь генерации постов через Celery / Redis | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity / LinkID Agent** | 🔴 P1 | 2026-09-15 | 🟢 Done |
| **TASK-LINKID-004** | **Спринт 2** | [LinkID] Интеграция авто‑публикации постов в LinkedIn (REST API Cron) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🔴 P1 | 2026-09-16 | 🟢 Done |
| **TASK-LINKID-008** | **Спринт 2** | [LinkID] Редактор профиля тональности и стиля автора (Tone Profile) в TMA | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-LINKID-009** | **Спринт 2** | [LinkID] Автогенерация обложек и инфографики к постам (DALL‑E 3 / Flux API) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🔵 P3 | 2026-09-18 | 🟢 Done |
| **TASK-LINKID-010** | **Спринт 2** | [LinkID] Авто-кросспостинг анонсов постов в Telegram-топик команды | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-LINKID-011** | **Спринт 2** | [LinkID] Аналитика просмотров и охватов LinkedIn в TMA (Engagement Tracker) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-LINKID-012** | **Спринт 2** | [LinkID] Динамический менеджер источников новостей (RSS/TG-каналы) в админке | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-16 | 🟢 Done |
| **TASK-LINKID-013** | **Спринт 2** | [LinkID] Healthcheck Sentinel & Auto-heal (Авто-восстановление сетевых роутов) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-14 | 🟢 Done |
| **TASK-LINKID-015** | **Спринт 3** | [LinkID] Расширяемая очередь публикаций и генерации (Redis Streams / RabbitMQ) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P0 | 2026-09-21 | 📋 To Do |
| **TASK-LINKID-016** | **Спринт 3** | [LinkID] Динамический Whitelist Telegram ID (управление через Admin UI) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P0 | 2026-09-21 | 📋 To Do |
| **TASK-LINKID-017** | **Спринт 3** | [LinkID] Автогенерация визуальных обложек к постам (DALL-E 3 / Flux API / SD) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-23 | 📋 To Do |
| **TASK-LINKID-018** | **Спринт 3** | [LinkID] Интеграция Claude 3.5 Sonnet & DeepSeek V3 в LLM Selector | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-23 | 📋 To Do |
| **TASK-LINKID-019** | **Спринт 3** | [LinkID] Prometheus-метрики использования LLM, токенов и латенси | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-24 | 📋 To Do |
| **TASK-LINKID-020** | **Спринт 3** | [LinkID] Авто-тесты CI/CD для парсеров, генераторов и публикации | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-25 | 📋 To Do |
| **TASK-LINKID-021** | **Спринт 3** | [LinkID] Systemd Watchdog & Auto-restart при сбоях cron-скриптов | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-25 | 📋 To Do |
| **TASK-LINKID-022** | **Спринт 3** | [LinkID] Экспорт контент-плана в iCal / Google Calendar (.ics feed) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🟡 P2 | 2026-09-26 | 📋 To Do |
| **TASK-LINKID-023** | **Спринт 3** | [LinkID] UI-редизайн разделов «Style» и «Covers» в Telegram Mini App | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🟡 P2 | 2026-09-27 | 📋 To Do |
| **TASK-LINKID-024** | **Спринт 3** | [LinkID] OpenAPI / Swagger документация v2 эндпоинтов | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🟡 P2 | 2026-09-28 | 📋 To Do |
| **TASK-ITOPS-005** | **Спринт 2** | Core API Hardening: Graph Token Cache & Rate Limiting | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-ITOPS-007** | **Спринт 2** | Распределённый Rate Limiting через Redis (Sliding Window / IncrBy) | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-16 | 🟢 Done |
| **TASK-ITOPS-008** | **Спринт 2** | Executive PDF/Excel Digest Engine для CIO (SLA & Инциденты) | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-ITOPS-009** | **Спринт 2** | Telegram Mini App Status Page & Service Health (Мониторинг сервисов) | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-18 | 🟢 Done |
| **TASK-ITOPS-010** | **Спринт 3** | Добавить Prometheus‑exporter для мониторинга счётчиков Rate Limiting и Circuit Breaker | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-ITOPS-011** | **Спринт 3** | Расширить Audit Trail: логировать действия администраторов и изменения фичер‑флагов | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🔴 P1 | 2026-09-22 | 📋 To Do |
| **TASK-ITOPS-012** | **Спринт 3** | Интегрировать health‑check микросервис для внешних зависимостей (SMTP, AD, 1С) в виде отдельного FastAPI‑сервиса | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-24 | 📋 To Do |
| **TASK-ITOPS-013** | **Спринт 3** | Добавить автогенерацию PDF‑preview (png) для Executive Digest, чтобы быстро проверять внешний вид | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-25 | 📋 To Do |
| **TASK-ITOPS-014** | **Спринт 3** | Реализовать UI‑конфигурацию Feature Flags в Mini‑App (просмотр/переключение без redeploy) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-27 | 📋 To Do |
| **TASK-ITOPS-015** | **Спринт 3** | Добавить CI‑step для статического анализа секретов (gitleaks + secret‑guard) в GitHub Actions | **IT Operations** | Чат IT Ops | **CI/CD** | 🟡 P2 | 2026-09-28 | 📋 To Do |
| **TASK-ITOPS-016** | **Спринт 3** | Написать набор e2e‑тестов (Playwright) для статуса сервиса и доступа к Mini‑App | **IT Operations** | Чат IT Ops | **QA Team** | 🟡 P2 | 2026-09-30 | 📋 To Do |
| **TASK-ITOPS-017** | **Спринт 3** | Обновить документацию: добавить диаграммы архитектуры (Mermaid) и инструкции по развёртыванию в Docker | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-30 | 📋 To Do |
| **TASK-ITOPS-018** | **Спринт 3** | Внедрить автоматический ротацию токенов доступа к внешним API (Graph API, Whisper) через Vault | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🔴 P1 | 2026-10-02 | 📋 To Do |
| **TASK-ITOPS-019** | **Спринт 3** | Добавить оповещения в Telegram о превышении лимитов Rate Limiting для критических сервисов | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-10-02 | 📋 To Do |
| **TASK-ITOPS-020** | **Спринт 3** | Провести обзор и оптимизацию Docker‑образов (мульти‑stage, уменьшить размер) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-10-04 | 📋 To Do |
| **TASK-IMP-001** | **Спринт 2** | Добавить preview‑mode для автогенерации постов в LinkID | **LinkID** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-002** | **Спринт 2** | Сохранять историю последних 5 выбранных LLM и предлагать автодополнение | **LinkID** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-003** | **Спринт 2** | Реализовать retry‑логику с экспоненциальной задержкой для неуспешных вебхуков | **LinkID** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-004** | **Спринт 2** | Добавить конфигурируемые лимиты per‑client/IP в админ‑панель Rate Limiting | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-005** | **Спринт 2** | Встроить Prometheus‑exporter для мониторинга счётчиков лимитов | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-006** | **Спринт 2** | Автогенерировать превью‑версии PDF/Excel отчётов (png) для быстрой проверки | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-007** | **Спринт 2** | Создать микросервис status‑checker для health‑check внешних сервисов (SMTP, AD, 1С) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-008** | **Спринт 2** | Добавить step в CI‑pipeline static‑analysis (bandit, safety) | **IT Operations** | Чат IT Ops | **CI/CD** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-009** | **Спринт 2** | Автоматически генерировать OpenAPI‑спецификацию из FastAPI и публиковать в `/docs` | **IT Operations** | Чат IT Ops | **CI/CD** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-010** | **Спринт 2** | Добавить e2e‑тесты (Cypress/Playwright) для основных пользовательских сценариев | **IT Operations** | Чат IT Ops | **QA Team** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-011** | **Спринт 2** | [LinkID] AI Content Quality & Toxicity Guard (проверка постов перед публикацией) | **LinkID Pro Post** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-012** | **Спринт 2** | [LinkID] Multi‑Format Repurposing (генерация анонсов для Telegram / X из постов) | **LinkID Pro Post** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-013** | **Спринт 2** | [IT Ops] Audit Trail & Compliance Logger в PostgreSQL | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-014** | **Спринт 2** | [IT Ops] Circuit Breaker pattern для внешних API (Graph API / STT Whisper) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🔴 P1 | 2026-09-19 | 🟢 Done |
| **TASK-IMP-015** | **Спринт 2** | [IT Ops] Dynamic Feature Flags Manager (Redis/TMA) без перезапуска сервисов | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-016** | **Спринт 2** | [Stocks UZ] Backtesting Engine для дивидендных и объёмных стратегий UZSE | **Stocks UZ** | Чат Stocks UZ | **Stocks Agent** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-IMP-017** | **Спринт 2** | [Alpha Scout] Multi‑DEX Liquidity Depth Scanner (учёт Slippage и Price Impact) | **Alpha Scout** | Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-18 | 🟢 Done |
| **TASK-IMP-018** | **Спринт 2** | [Инфраструктура] Centralized Log Rotation (сжатие логов Docker 14 дней на US Server) | **Инфраструктура** | Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-15 | 🟢 Done |
| **TASK-IMP-019** | **Спринт 2** | [Безопасность] Auto Secret Scanner Pre‑Commit Hook (gitleaks / secret-guard) | **Экосистема** | Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-14 | 🟢 Done |
| **TASK-IMP-020** | **Спринт 2** | [QA / Триада] Auto‑Smoke Test Suite after Deployment (Quality Gate #4) | **QA Track** | Master Orchestrator | **QA Team** | 🟡 P2 | 2026-09-20 | 🟢 Done |
| **TASK-010** | **Спринт 2** | [Stocks UZ] Push-уведомления "Утренний Бриф" в Telegram (09:50 AM) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-14 | 🟢 Done |
| **TASK-011** | **Спринт 2** | [Stocks UZ] Модуль Риск-менеджмента и Asset Allocation (Pie Charts) в TMA | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-012** | **Спринт 2** | [Stocks UZ] AI-Сканер Аномальных Объемов (Smart Money Detection) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-16 | 🟢 Done |
| **TASK-013** | **Спринт 2** | [Stocks UZ] Фундаментальный AI-Скринер (Value Investing: P/E, P/B, ROE) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-15 | 🟢 Done |
| **TASK-STOCKS-014** | **Спринт 2** | [Stocks UZ] Telegram Instant Signal Alerts (Детектор инсайдерских выкупов) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-15 | 🟢 Done |
| **TASK-016** | **Спринт 2** | [Stocks UZ] Мониторинг раскрытия существенных фактов и отчетов OpenInfo.uz | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-16 | 🟢 Done |
| **TASK-017** | **Спринт 2** | [Stocks UZ] Авто-расчет дивидендной доходности (Yield to Cost в % и UZS) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-STOCKS-018** | **Спринт 2** | [Stocks UZ] Сканер неликвидных стаканов и неэффективных спредов (>10%) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-STOCKS-019** | **Спринт 2** | [Stocks UZ] Target Price Push-Alerts (Уведомления о достижении цен закупки) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-14 | 🟢 Done |
| **TASK-BGT-011** | **Спринт 2** | BGT: Интеграция "Уровня Жадности" (Market Greed / Regime Filter) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-16 | 🟢 Done |
| **TASK-BGT-012** | **Спринт 2** | BGT: Динамический TP/SL (Smart Scaling Out) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-BGT-015** | **Спринт 2** | BGT: All-Weather Архитектура (Мульти-режимность тренд/флэт) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🔴 P1 | 2026-09-18 | 🟢 Done |
| **TASK-BGT-018** | **Спринт 2** | BGT: WebSocket Price Stream Engine (переход с REST-поллинга на котировки) | **BGT (Bitget Bot)** | Чат BGT | **Antigravity / BGT Agent** | 🔴 P1 | 2026-09-16 | 🟢 Done |
| **TASK-BGT-019** | **Спринт 2** | BGT: AI Safety Circuit-Breaker (Защита от сбоев биржи и таймаутов API при выставлении SL) | **BGT (Bitget Bot)** | Чат BGT | **Antigravity / BGT Agent** | 🔴 P1 | 2026-09-15 | 🟢 Done (`v0.2.2`) |
| **TASK-BGT-023** | **Спринт 2** | BGT: Lead-Lag Сигнал Binance (Cross-Exchange Front-running) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🔴 P1 | 2026-09-14 | 🟢 Done |
| **TASK-BGT-024** | **Спринт 2** | BGT: Пирамидинг на супер-трендах (Safe Pyramiding) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-BGT-025** | **Спринт 2** | BGT: Утренний Executive Дайджест в Telegram (08:00 UTC+5) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟢 P3 | 2026-09-13 | 🟢 Done |
| **TASK-BGT-026** | **Спринт 2** | BGT: Детектор сжатия волатильности (TTM Squeeze Detector) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-16 | 🟢 Done |
| **TASK-ALPHA-001** | **Спринт 2** | [Alpha Scout] Polymarket On-Chain Whale Alert Bot (Авто-трекинг сделок ТОП-20 кошельков в Telegram) | **Alpha Scout / Trading** | Чат Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-14 | 🟢 Done (`v0.1.0`) |

| **TASK-ALPHA-002** | **Спринт 2** | [Alpha Scout] DEX/CEX Spread Scanner (Сопоставление Raydium с Bitget) | **Alpha Scout / Trading** | Чат Master Orchestrator | **Antigravity** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-BGT-027** | **Спринт 3** | BGT Signals Telegram Mini App (Витрина сигналов под модель $35/мес) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-15 | 🟢 Done |
| **TASK-BGT-028** | **Спринт 3** | Machine Learning Signal Filter (XGBoost/LightGBM фильтр ложных входов) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-16 | 🟢 Done |
| **TASK-BGT-029** | **Спринт 3** | Динамический Авто-Балансировщик Капитала на основе Sharpe Ratio | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-BGT-030** | **Спринт 3** | Умный Авто-Компаундинг Депозита ($107 → $120 → $200 → $1000) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-14 | 🟢 Done |
| **TASK-BGT-031** | **Спринт 3** | Защита от Чёрных Лебедей (Flash Crash Black Swan Circuit Breaker) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-BGT-032** | **Спринт 3** | DEX On-Chain Liquidity Watcher (Uniswap v3 / Raydium Pool Tracker) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔵 P3 | 2026-09-18 | 🟢 Done |
| **TASK-BGT-033** | **Спринт 3** | Бот подписок @bgt_signals_bot & Crypto Pay / Stars Gateway | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🔴 P1 | 2026-09-16 | 🟢 Done |
| **TASK-BGT-034** | **Спринт 3** | Orderbook Heatmap & Depth Imbalance Engine (L2 Стенки) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-BGT-035** | **Спринт 3** | Интерактивный Бэктестер в Telegram по команде `/backtest` | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟢 P3 | 2026-09-18 | 🟢 Done |
| **TASK-BGT-036** | **Спринт 3** | Multi-Timeframe Confluence Engine (Согласованность 1m+15m+1h+4h) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🔴 P1 | 2026-09-15 | 🟢 Done |
| **TASK-BGT-037** | **Спринт 3** | Chandelier Exit Trailing Engine (Динамический стоп от пиков) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-16 | 🟢 Done |
| **TASK-BGT-038** | **Спринт 3** | Автоматический Журнал Сделок (Google Sheets / Notion Sync API) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟢 P3 | 2026-09-17 | 🟢 Done |
| **TASK-BGT-039** | **Спринт 3** | Execution Slippage & Latency Profiler (Профайлер качества исполнения) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-18 | 🟢 Done |
| **TASK-BGT-040** | **Спринт 3** | Lead‑Lag Error Recovery & Alerting (обработка ошибок и оповещение в Telegram) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-041** | **Спринт 3** | TradingView Alert Integration (импорт сигналов из TradingView в lead_lag.json) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-042** | **Спринт 3** | ML-Model CI / Test Suite (автоматические тесты модели XGBoost/LightGBM) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-043** | **Спринт 3** | Sharpe-Ratio Monitor & Notification (оповещение при падении < 1.0) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-044** | **Спринт 3** | Liquidity Drop Alert (оповещение при падении ликвидности > 20% за 5 мин) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-045** | **Спринт 3** | Payment-Gateway Integration (Stripe/PayPal для подписки) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-046** | **Спринт 3** | Mobile-Responsive Heatmap (адаптивный дизайн для Orderbook Heatmap) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-047** | **Спринт 3** | Coverage Report for Backtester (генерация markdown-отчёта покрытий) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-048** | **Спринт 3** | Dynamic Chandelier Params (UI-контролы для изменения параметров) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-049** | **Спринт 3** | Backup Journal to S3 (резервное копирование журнала сделок) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-050** | **Спринт 3** | Grafana Dashboard for Latency (дашборд метрик исполнения) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-051** | **Спринт 3** | Externalise Config & Retry Wrapper (вынос хардкодов live_trend.py в конфиг + exponential backoff для ccxt) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-052** | **Спринт 3** | Brain Scoring Audit Trail (логирование решений скоринга в SQLite + конфигурируемые веса) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-053** | **Спринт 3** | API Connection Pooling (переход на requests.Session для переиспользования TLS-соединений) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-054** | **Спринт 3** | Рефакторинг funding_arb.py (декомпозиция God-Object 124KB на модули) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-055** | **Спринт 3** | Декомпозиция strategies.py (разбиение 108KB монолита на пакет strategies/) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-056** | **Спринт 3** | Разделение ответственностей bot.py (вынос отчётов/бэктестов из основного while-цикла) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔵 P3 | 2026-09-22 | 🟢 Done |
| **TASK-BGT-057** | **Спринт 3** | Infrastructure Package (requirements.txt + .env.example + Dockerfile + GitHub Actions CI) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-22 | 🟢 Done |
| **TASK-ALPHA-003** | **Спринт 3** | [Alpha Scout] Funding Rate Arbitrage & Delta-Neutral Yield Engine (Сбор ставки фандинга CEX/DEX) | **Alpha Scout / Trading** | Чат Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-18 | 🟢 Done |
| **TASK-SYS-003** | **Спринт 3** | Unified AI Rate-Limit & Token Health Sentinel (Единый фоновый мониторинг API-лимитов/балансов LLM) | **Инфраструктура / Сервер** | Чат Master Orchestrator | **Antigravity (Сисадмин)** | 🔴 P1 | 2026-09-15 | 🟢 Done (`/home/us/bin/token_sentinel.py`) |

| **TASK-HH-010** | **Спринт 2** | [HH Jobs] Auto-Draft Cover Letter Generator (Генерация отклика в 1 клик) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-16 | 🟢 Done |

| **TASK-HH-014** | **Спринт 2** | [HH Jobs] Умный парсинг требований (LLM): извлечение неявных навыков и ЗП | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-15 | 🟢 Done |
| **TASK-HH-015** | **Спринт 2** | [HH Jobs] Трекинг статусов откликов в TMA (через интеграцию с почтой/API) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-16 | 🟢 Done |
| **TASK-HH-016** | **Спринт 2** | [HH Jobs] Авто-генератор кастомных резюме под вакансию (Resume Tailoring) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🔴 P1 | 2026-09-17 | 🟢 Done |
| **TASK-HH-017** | **Спринт 2** | [HH Jobs] AI-Ассистент подготовки к собеседованию (Interview Prep) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-17 | 🟢 Done |
| **TASK-HH-018** | **Спринт 2** | [HH Jobs] Анализатор зарплатных вилок рынка Узбекистана (Salary Intelligence) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🔵 P3 | 2026-09-18 | 🟢 Done |
| **TASK-SYS-002** | **Спринт 2** | Unified Health Dashboard & Daily Backup Verification (Дайджест в 08:00) | **Инфраструктура / Сервер** | Чат Master Orchestrator | **Antigravity (Сисадмин)** | 🟡 P2 | 2026-09-14 | 🟢 Done |

---

## 📝 Детализация задач Спринта 2 (Активный спринт)

### 🔗 LinkID Pro Post

#### [TASK-LINKID-005] Self-Healing LLM Fallback (Авто-переключение на бесплатную модель)
- **Контекст:** При отсутствии средств на провайдере OpenRouter модель DeepSeek v4 Pro возвращает HTTP 402 Payment Required, что приводило к сбою генерации.
- **Решение:** Внедрен список кандидатных моделей (`deepseek-v4-pro` $	o$ `google/gemma-4-31b-it:free` $	o$ `google/gemma-4-26b-a4b-it:free`). При получении ошибки 402 система автоматически переключается на бесплатную модель без сбоя для пользователя.
- **Статус:** 🟢 Done (Коммит `3e7e62f`, верифицировано на сервере).

#### [TASK-LINKID-006] Настройка проксирования API через Tailscale Funnel & Устранение DOMException в iOS
- **Контекст:** Mini App совершал запросы на `/linkid/api/v1/*`, но в Tailscale Funnel отсутствовал роут на бэкенд, из-за чего Caddy отдавал пустой 404, а WKWebView на iOS выбрасывал ошибку `DOMException: The string did not match the expected pattern`.
- **Решение:** Добавлен прокси-маршрут `/linkid` $	o$ `127.0.0.1:8014` в Tailscale Funnel и скрипт `scripts/restore-serve.sh`.
- **Статус:** 🟢 Done (Коммит `b82c43e`, проверено клиентом).

#### [TASK-LINKID-007] Синхронизация доступа для команды (5 Telegram ID)
- **Контекст:** Бэкенд и бот проверяли только `TELEGRAM_ADMIN_IDS`, перекрывая `ALLOWED_TELEGRAM_USER_IDS`, из-за чего доступ имел только 1 человек.
- **Решение:** Обновлен код авторизации (`bot.py` и `backend/app/api/__init__.py`), объединяющий оба источника. На сервере в `.env` внесены все 5 разрешенных ID (`110627043`, `644427986`, `7345133591`, `7400177636`, `8021197289`).
- **Статус:** 🟢 Done (Коммит `40d9381`, контейнеры перезапущены).

#### [TASK-LINKID-001] Динамический выбор LLM в веб-админке (`:8015`)
- **Суть:** Добавление UI-селектора в веб-админку LinkID для переключения генерации между моделями (Claude 3.5, DeepSeek, GPT-4o-mini, Gemma) с сохранением настроек в БД.
- **Приоритет:** 🔴 P1 (High) | **Срок:** 2026-09-14 | **Статус:** 📋 To Do
- **DoD:** Выбор модели сохраняется в БД `UserStyleProfile`, генератор забирает актуальную модель из настроек.

#### [TASK-LINKID-002] Асинхронная очередь генерации постов через Celery / Redis
- **Суть:** Перенос вызова парсера и нейросети из синхронного HTTP-потока в фоновую очередь Celery, чтобы исключить риск 504 Gateway Timeout.
- **Приоритет:** 🔴 P1 (High) | **Срок:** 2026-09-15 | **Статус:** 📋 To Do
- **DoD:** Эндпоинт `/posts/generate` отдаёт `202 Accepted` и `task_id`. Mini App поллит статус выполнения.

#### [TASK-LINKID-004] Интеграция авто-публикации постов в LinkedIn (REST API Cron)
- **Суть:** Реализация фонового джоба для автоматической публикации `approved` постов напрямую в профиль LinkedIn через официальный REST API.
- **Приоритет:** 🔴 P1 (High) | **Срок:** 2026-09-16 | **Статус:** 📋 To Do
- **DoD:** Пост автоматически публикуется в LinkedIn по расписанию, статус меняется на `published`.

#### [TASK-LINKID-008] Редактор профиля тональности и стиля автора (Tone Profile) в TMA
- **Суть:** Добавление вкладки в Telegram Mini App для тонкой настройки тона (Управленческий, Инженерный, Аналитический) и запрещенных стоп-слов.
- **Приоритет:** 🟡 P2 (Medium) | **Срок:** 2026-09-17 | **Статус:** 📋 To Do
- **DoD:** Пользователь редактирует стиль в TMA, промпт генератора динамически подстраивается.

#### [TASK-LINKID-009] Автогенерация обложек и инфографики к постам (DALL-E 3 / Flux API)
- **Суть:** Генерация графических карточек/обложек для LinkedIn постов на основе темы и ключевых тезисов.
- **Приоритет:** 🔵 P3 (Low) | **Срок:** 2026-09-18 | **Статус:** 📋 To Do
- **DoD:** К посту прикрепляется сгенерированное изображение, доступное для предпросмотра в TMA.

#### [TASK-LINKID-010] Авто-кросспостинг анонсов постов в Telegram-топик команды
- **Суть:** Автоматическая публикация анонса готовых/одобренных постов в служебный Telegram-топик или канал для архивирования и оперативного ревью всей командой.
- **Приоритет:** 🟡 P2 (Medium) | **Срок:** 2026-09-15 | **Статус:** 📋 To Do
- **DoD:** При одобрении поста бот автоматически отсылает форматированный анонс с инлайн-ссылкой в Telegram-топик.

#### [TASK-LINKID-011] Аналитика просмотров и охватов LinkedIn в TMA (Engagement Tracker)
- **Суть:** Сбор статистики (показы, лайки, комментарии, шеринги) через LinkedIn REST API для опубликованных постов и рендеринг графиков во вкладке «Статус» в Mini App.
- **Приоритет:** 🟡 P2 (Medium) | **Срок:** 2026-09-17 | **Статус:** 📋 To Do
- **DoD:** Во вкладке «Статус» TMA отображаются графики охватов и топ-3 самых виральных постов за месяц.

#### [TASK-LINKID-012] Динамический менеджер источников новостей (RSS/TG-каналы) в админке
- **Суть:** Вынос хардкода новостных сайтов из `generate_posts.py` в БД и веб-админку (`:8015`), чтобы владелец мог добавлять и отключать RSS-ленты и Telegram-каналы для парсинга контекста.
- **Приоритет:** 🟡 P2 (Medium) | **Срок:** 2026-09-16 | **Статус:** 📋 To Do
- **DoD:** В админке есть раздел «Источники новостей» с тумблерами активностей и добавлением новых ссылок.

#### [TASK-LINKID-013] Healthcheck Sentinel & Auto-heal (Авто-восстановление сетевых роутов)
- **Суть:** Сторожевой фоновый процесс (Healthcheck Sentinel), проверяющий доступность API и публичного `/linkid-app` раз в 5 минут и автоматически выполняющий `restore-serve.sh` при любых сбоях сети или перезагрузке сервера.
- **Приоритет:** 🔴 P1 (High) | **Срок:** 2026-09-14 | **Статус:** 📋 To Do
- **DoD:** Скрипт-сторож добавлен в systemd/cron, при падении маршрута Funnel он восстанавливается за <30 секунд без участия человека.

#### [TASK-LINKID-014] Экспорт контент-плана постов в iCal / Google Calendar (.ics feed)
- **Суть:** Генерация персонализированного `.ics` календаря со всеми запланированными публикациями для импорта в Apple Calendar / Google Calendar.
- **Приоритет:** 🔵 P3 (Low) | **Срок:** 2026-09-18 | **Статус:** 📋 To Do
- **DoD:** Эндпоинт `/api/v1/posts/calendar.ics` отдаёт валидный iCal-файл с расписанием постов.

---

### 🏢 IT Operations Framework

#### [TASK-ITOPS-007] Распределённый Rate Limiting через Redis (Sliding Window)
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-16 | **Статус:** 📋 To Do
- **DoD:** Лимиты хранятся в Redis, поддержке подвержены мульти-воркерные развертывания.

#### [TASK-ITOPS-008] Executive PDF/Excel Digest Engine для CIO
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-17 | **Статус:** 📋 To Do
- **DoD:** Автогенерация брендированных PDF/Excel отчетов по SLA и инцидентам для IT-директора.

#### [TASK-ITOPS-009] Telegram Mini App Status Page & Service Health
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-18 | **Статус:** 📋 To Do
- **DoD:** Вкладка в TMA со статусом сервисов и аварией в реальном времени.

---

### 📈 Stocks UZ & BGT (Трейдинг и Инвестиции)

#### [TASK-010] [Stocks UZ] Push-уведомления "Утренний Бриф" (09:50 AM)
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-14 | **Статус:** 📋 To Do

#### [TASK-011] [Stocks UZ] Модуль Риск-менеджмента и Asset Allocation (Pie Charts)
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-15 | **Статус:** 📋 To Do

#### [TASK-012] [Stocks UZ] AI-Сканер Аномальных Объемов (Smart Money)
- **Приоритет:** 🔴 P1 | **Срок:** 2026-09-16 | **Статус:** 📋 To Do

#### [TASK-013] [Stocks UZ] Фундаментальный AI-Скринер (Value Investing: P/E, P/B, ROE)
- **Приоритет:** 🔴 P1 | **Срок:** 2026-09-15 | **Статус:** 📋 To Do

#### [TASK-STOCKS-016] [Stocks UZ] Авто-мониторинг OpenInfo.uz (Существенные факты и финансовые отчеты)
- **Суть:** Парсер корпоративных новостей и публикаций отчетов на OpenInfo.uz с instant Telegram-уведомлением при появлении решений по дивидендам или годовых отчетов.
- **Приоритет:** 🔴 P1 | **Срок:** 2026-09-16 | **Статус:** 📋 To Do
- **DoD:** Опережение рынка при выходе дивидендных новостей, лаг < 2 мин.

#### [TASK-STOCKS-017] [Stocks UZ] Калькулятор дивидендной доходности (Yield to Cost в % и UZS)
- **Суть:** Расчет доходности в % и суммах UZS как к текущей рыночной цене, так и к средней цене покупки по портфелю инвестора (GoInvest + Jett).
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-15 | **Статус:** 📋 To Do
- **DoD:** Отображение в TMA и алертов по дивидендам с суммой в UZS и потенциалом рои %.

#### [TASK-STOCKS-018] [Stocks UZ] Сканер неликвидных стаканов и неэффективных спредов (>10%)
- **Суть:** Поиск аномальных разрывов между Best Bid и Best Ask на UZSE для постановки выгодных лимитных заявок (забор объема у нетерпеливых продавцов).
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-17 | **Статус:** 📋 To Do
- **DoD:** Алерт при появлении спреда > 10% с расчетом точки выставления лимитки.

#### [TASK-STOCKS-019] [Stocks UZ] Target Price Push-Alerts (Уведомления о достижении цен закупки)
- **Суть:** Мониторинг целевых цен дозакупки (напр. BIOK 14 000 - 14 200 UZS, URTS 10 500 UZS) с мгновенным уведомлением при достижении уровня.
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-14 | **Статус:** 📋 To Do
- **DoD:** Мгновенный алерт в Telegram с диплинком на стакан в TMA.

#### [TASK-BGT-011] BGT: Интеграция "Уровня Жадности" (Market Greed / Regime Filter)
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-16 | **Статус:** 📋 To Do

#### [TASK-BGT-012] BGT: Динамический TP/SL (Smart Scaling Out)
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-17 | **Статус:** 📋 To Do

#### [TASK-BGT-015] BGT: All-Weather Архитектура (Мульти-режимность)
- **Приоритет:** 🔴 P1 | **Срок:** 2026-09-18 | **Статус:** 📋 To Do

#### [TASK-BGT-018] BGT: WebSocket Price Stream Engine
- **Суть:** Перевод расчёта индикаторов и входов в сделки с REST-поллинга (`90s`) на прямые WebSocket-стримы котировок Bitget. Это снизит задержку входа при Donchian-пробоях с десятков секунд до миллисекунд.
- **Приоритет:** 🔴 P1 | **Срок:** 2026-09-16 | **Статус:** 📋 To Do
- **DoD:** Задержка от импульса цены до отправки ордера $< 300$ мс, fall-back на REST при разрыве связи.

#### [TASK-BGT-023] BGT: Lead-Lag Сигнал Binance (Cross-Exchange Front-running)
- **Суть:** Binance лидирует на крипторынке в 90% случаев. Скрипт отслеживает пробои на Binance 15m. Если Binance пробивает уровень на 2-5 секунд раньше Bitget, бот входит на Bitget до того, как маркетмейкер подвинет цену.
- **Спринт:** Спринт 2 | **Приоритет:** 🔴 P1 | **Срок:** 2026-09-14 | **Статус:** 📋 To Do
- **DoD:** Опережение задержки Bitget на 1-3 секунды при пробоях.

#### [TASK-BGT-024] BGT: Пирамидинг на супер-трендах (Safe Pyramiding)
- **Суть:** Долив в позицию при продолжении сильного тренда. Если сделка переведена в безубыток (Smart Scaling Out) и цена проходит +4 ATR, бот добавляет +25% к позиции за счет накопленного незафиксированного профита.
- **Спринт:** Спринт 2 | **Приоритет:** 🟡 P2 | **Срок:** 2026-09-15 | **Статус:** 📋 To Do
- **DoD:** Увеличение итогового PnL на длинных трендах на 20-30%.

#### [TASK-BGT-025] BGT: Утренний Executive Дайджест в Telegram (08:00 UTC+5)
- **Суть:** Ежедневная утренняя сводка владельцу: режим рынка (Greed/Fear), результаты работы ночного оптимизатора, лидеры Paper Trading и статус депозита.
- **Спринт:** Спринт 2 | **Приоритет:** 🟢 P3 | **Срок:** 2026-09-13 | **Статус:** 📋 To Do
- **DoD:** Автоматическая отправка 1 структурированного сообщения каждое утро в Telegram.

#### [TASK-BGT-026] BGT: Детектор сжатия волатильности (TTM Squeeze Detector)
- **Суть:** Анализ сужения Полос Боллинджера (Bollinger Bands Squeeze) на 4h. Когда волатильность сжимается до годовых минимумов, бот готовится к выстрелу на 15-30% и повышает чувствительность входов.
- **Спринт:** Спринт 2 | **Приоритет:** 🟡 P2 | **Срок:** 2026-09-16 | **Статус:** 📋 To Do
- **DoD:** Определение фазы накопления перед сильным импульсом.

---

### 🚀 Alpha Scout (Поиск арбитража и сигналов)

#### [TASK-ALPHA-001] Polymarket On-Chain Whale Alert Bot
- **Суть:** Фоновый сервисный бот, отслеживающий ончейн-транзакции в Polygon для ТОП-20 кошельков лидерборда Polymarket. При открытии позиции $> \$1,000$ отправляется мгновенный алерт в Telegram.
- **Приоритет:** 🔴 P1 | **Срок:** 2026-09-14 | **Статус:** 📋 To Do
- **DoD:** Бот работает 24/7 на US Server, Telegram-уведомления содержат ссылку на исход, размер позиции и кошелек кита.

#### [TASK-ALPHA-002] DEX/CEX Spread Scanner (Solana & EVM vs Bitget/MEXC)
- **Суть:** Сканер разницы цен между пулами ликвидности Raydium/Uniswap и котировками централизованных бирж для поиска асимметричных возможностей арбитража.
- **Приоритет:** 🟡 P2 | **Срок:** 2026-09-17 | **Статус:** 📋 To Do
- **DoD:** Дайджест аномалий со спредом $> 3\%$ генерируется в расчете на реальное исполнение.

---

## 📐 Правила ведения бэклога (Enterprise Process Standard)

1. **Единый источник правды (Single Source of Truth):**
   - Никаких задач «на словах» или забытых в чатах. Любая задача, идея или баг обязательно фиксируется в этом файле.
2. **Атрибуты каждой задачи:**
   - `ID`: сквозной номер (`TASK-XXX` или `TASK-PROJECT-XXX`).
   - `Спринт`: номер спринта (`Спринт 1`, `Спринт 2` и т.д.).
   - `Приоритет`: P0 (Blocker), P1 (High), P2 (Medium), P3 (Low).
   - `Ответственный`: конкретный агент (`Antigravity`, `Claude Code`, `Hermes`) или разработчик.
   - `Срок реализации`: фиксированная дата дедлайна.
   - `Definition of Done (DoD)`: четкие технические критерии принятия работы.
3. **Жизненный цикл задачи:**
   `📋 To Do` $	o$ `⏳ In Progress` $	o$ `🔍 Review / QA` $	o$ `🟢 Done`.

---

## 💡 Ежедневный поток идей заработка и R&D (Daily Alpha Stream)

| Дата | Категория | Идея / Направление | Суть и Профит | Статус |
| :--- | :--- | :--- | :--- | :---: |
| **2026-09-11** | **Alpha Stream (Идея №1)** | **Prediction Markets Arbitrage & Whale Scanner (Polymarket)** | Разработка модуля `alpha-scout` для поиска спредов/арбитража вероятностей 5m BTC и трекинга кошельков топ-50 трейдеров Polymarket с алертами в Telegram. | 🟢 Done (`v0.1.0`) |
| **2026-09-11** | **BGT Upgrade** | **BGT Dynamic Volatility Regime (ATR Expansion Filter)** | Фильтр флэтового болота для BGT: вход в сделки только на расширении волатильности (`a_short / a_long >= 1.05`) для исключения ложных входов. | 🟢 Done (`v0.2.1`) |
| **2026-09-12** | **Alpha Stream (Идея №2)** | **Funding Rate Arbitrage & Delta-Neutral Yield (`TASK-ALPHA-003`)** | Дельта-нейтральный арбитраж ставки фандинга CEX/DEX (15–40% APR) без риска движения цены. | 📋 На распределение |
| **2026-09-12** | **System Sentinel** | **Unified AI Rate-Limit & Token Health Sentinel (`TASK-SYS-003`)** | Фоновый инспектор лимитов LLM-токенов/балансов во всех ботах с предупреждением за 24ч до лимита. | 📋 В разработке |


| **TASK-ITOPS-021** | **4** | Расширить Prometheus‑exporter: новые метрики (latency, error‑rate) и Grafana‑дашборд | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🔴 P1 | 2026‑10‑05 | 📋 To Do |
| **TASK-ITOPS-022** | **4** | Внедрить динамический Circuit Breaker с адаптивными порогами (на основе ML‑модели) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🔴 P1 | 2026‑10‑07 | 📋 To Do |
| **TASK-ITOPS-023** | **4** | Разработать UI‑конфигуратор Feature Flags (просмотр, включение/выключение, история) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026‑10‑10 | 📋 To Do |
| **TASK-ITOPS-024** | **4** | Полный аудит безопасности (CSP, HSTS, Content‑Security‑Policy, OWASP‑Check) и интеграция Auto‑Secret‑Scanner в CI | **IT Operations** | Чат IT Ops | **CI/CD** | 🔴 P1 | 2026‑10‑12 | 📋 To Do |
| **TASK-ITOPS-025** | **4** | Автоматическая ротация всех внешних токенов (API, GitHub, Docker) через Vault с поддержкой Secrets‑Engine | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🔴 P1 | 2026‑10‑14 | 📋 To Do |
| **TASK-ITOPS-026** | **4** | Реализовать централизованный health‑check микросервис (FastAPI) с плагинами для SMTP, AD, 1С, базы данных | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026‑10‑16 | 📋 To Do |
| **TASK-ITOPS-027** | **4** | Добавить авто‑генерацию PDF/Excel‑отчетов (preview PNG) для Executive Digest + интеграция в Telegram‑бот | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026‑10‑18 | 📋 To Do |
| **TASK-ITOPS-028** | **4** | Создать набор e2e‑тестов (Playwright) для всех новых API‑эндпоинтов и UI‑фич | **IT Operations** | Чат IT Ops | **QA Team** | 🟡 P2 | 2026‑10‑20 | 📋 To Do |
| **TASK-ITOPS-029** | **4** | Обновить документацию: полные Mermaid‑диаграммы инфраструктуры, инструкции Docker‑compose, CI/CD пайплайн | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026‑10‑22 | 📋 To Do |
| **TASK-ITOPS-030** | **4** | Интегрировать оповещения в Telegram о превышении лимитов Rate Limiting и Circuit Breaker (critical) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026‑10‑24 | 📋 To Do |
| **TASK-ITOPS-031** | **4** | Реализовать Feature‑Flag versioning: хранение истории изменений, откат к предыдущей версии | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026‑10‑26 | 📋 To Do |
| **TASK-ITOPS-032** | **4** | Добавить автотесты на безопасность: проверка CSP, HSTS, CORS через OWASP ZAP в CI | **IT Operations** | Чат IT Ops | **CI/CD** | 🔴 P1 | 2026‑10‑28 | 📋 To Do |
| **TASK-ITOPS-033** | **4** | Разработать отчёт о покрытии тестами (code‑coverage) и установить пороги качества (80 %) | **IT Operations** | Чат IT Ops | **CI/CD** | 🟡 P2 | 2026‑10‑30 | 📋 To Do |
| **TASK-ITOPS-034** | **4** | Согласовать и провести обучение команды (Webinar) по новому Prometheus‑exporter и Circuit Breaker | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026‑11‑02 | 📋 To Do |

## 📊 Sprint 4 – Все проекты (масштабный)

### IT Ops
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑ITOPS‑021 | 4 | Обновить документацию по CI/CD пайплайну | IT Ops | it‑ops‑bot | antigravity | High | 2026‑10‑01 | TODO |
| TASK‑ITOPS‑022 | 4 | Авто‑тестирование инфраструктурных скриптов | IT Ops | it‑ops‑bot | antigravity | Medium | 2026‑10‑05 | TODO |
| TASK‑ITOPS‑023 | 4 | Ревизия правил доступа к секретам | IT Ops | it‑ops‑bot | antigravity | High | 2026‑09‑30 | TODO |

### BGT (bitget‑bot)
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑BGT‑041 | 4 | Добавить поддержку новых пар BTC/USDT и ETH/USDT | BGT | bgt‑bot | antigravity | High | 2026‑10‑07 | TODO |
| TASK‑BGT‑042 | 4 | Реализовать модуль динамического скоринга пар | BGT | bgt‑bot | antigravity | High | 2026‑10‑14 | TODO |
| TASK‑BGT‑043 | 4 | Провести back‑test стратегии арбитража Funding | BGT | bgt‑bot | antigravity | Medium | 2026‑10‑20 | TODO |

### LinkID
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑LINKID‑031 | 4 | Интеграция нового LLM v4 Pro для генерации постов | LinkID | linkid‑bot | antigravity | High | 2026‑10‑03 | TODO |
| TASK‑LINKID‑032 | 4 | Добавить поддержку многопользовательской авторизации в Mini‑App | LinkID | linkid‑bot | antigravity | Medium | 2026‑10‑10 | TODO |

### HH Jobs
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑HHJOBS‑015 | 4 | Обновить парсер вакансий HeadHunter (API v2) | HH Jobs | hh‑jobs‑bot | antigravity | High | 2026‑10‑05 | TODO |
| TASK‑HHJOBS‑016 | 4 | Добавить фильтрацию по remote‑only и seniority | HH Jobs | hh‑jobs‑bot | antigravity | Medium | 2026‑10‑12 | TODO |

### Stocks UZ
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑STOCKS‑078 | 4 | Добавить парсинг 5 новых TG‑каналов аналитики | Stocks UZ | uz‑stocks‑bot | antigravity | Medium | 2026‑10‑08 | TODO |
| TASK‑STOCKS‑079 | 4 | Реализовать автоматический алерт при росте цены >15% | Stocks UZ | uz‑stocks‑bot | antigravity | High | 2026‑10‑15 | TODO |
| TASK‑STOCKS‑080 | 4 | Интеграция парсера раскрытия отчетов OpenInfo.uz и NAPP (финансовые результаты) | Stocks UZ | uz‑stocks‑bot | antigravity | High | 2026‑10‑18 | TODO |
| TASK‑STOCKS‑081 | 4 | Авто-трекинг решений ГОС/ВОС акционеров по дивидендам и ex-date | Stocks UZ | uz‑stocks‑bot | antigravity | High | 2026‑10‑20 | TODO |
| TASK‑STOCKS‑082 | 4 | Расчёт коэффициентов ликвидности и Altman Z-Score банкротства эмитентов | Stocks UZ | uz‑stocks‑bot | antigravity | Medium | 2026‑10‑22 | TODO |
| TASK‑STOCKS‑083 | 4 | Центр Push-уведомлений и подписок на тикеры в Telegram Mini App | Stocks UZ | uz‑stocks‑bot | antigravity | High | 2026‑10‑25 | TODO |
| TASK‑STOCKS‑084 | 4 | Backtesting Engine стоимостных и дивидендных стратегий (2021–2026) | Stocks UZ | uz‑stocks‑bot | antigravity | Medium | 2026‑10‑28 | TODO |
| TASK‑STOCKS‑085 | 4 | Мониторинг крупноблочных сделок внесистемного рынка UZSE / NAPP (OTC) | Stocks UZ | uz‑stocks‑bot | antigravity | High | 2026‑10‑30 | TODO |
| TASK‑STOCKS‑086 | 4 | Индекс полной доходности рынка Узбекистана (UZSE Total Return Index - UZTR) | Stocks UZ | uz‑stocks‑bot | antigravity | Medium | 2026‑11‑02 | TODO |
| TASK‑STOCKS‑087 | 4 | Экспорт PDF/Excel инвест-тизера по акциям (Executive Investment Teaser) | Stocks UZ | uz‑stocks‑bot | antigravity | High | 2026‑11‑05 | TODO |
| TASK‑STOCKS‑088 | 4 | Авто-расчёт налогов на дивиденды и прирост капитала (UZ Tax Calculator) | Stocks UZ | uz‑stocks‑bot | antigravity | Medium | 2026‑11‑08 | TODO |
| TASK‑STOCKS‑089 | 4 | Telegram Bot Inline-режим (@stock_uz_bot): поиск карточек и графиков в любом чате | Stocks UZ | uz‑stocks‑bot | antigravity | Medium | 2026‑11‑10 | TODO |



### Alpha Scout
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑ALPHASCOUT‑005 | 4 | Добавить мониторинг новых репозиториев в GitHub (GH Scout) | Alpha Scout | alpha‑scout‑bot | antigravity | Medium | 2026‑10‑09 | TODO |

### GH Scout
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑GHSCOUT‑012 | 4 | Обновить скрипт анализа зависимостей npm‑пакетов | GH Scout | gh‑scout‑bot | antigravity | Medium | 2026‑10‑11 | TODO |

### DataCore
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑DATACORE‑021 | 4 | Оптимизировать ETL‑pipeline для больших данных | DataCore | datacore‑bot | antigravity | High | 2026‑10‑20 | TODO |

### Инфраструктура и системные задачи
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑INFRA‑007 | 4 | Обновить Tailscale‑маршрутизацию между US‑Server и Mac‑машиной | Инфраструктура | infra‑bot | antigravity | High | 2026‑09‑30 | TODO |
| TASK‑INFRA‑008 | 4 | Настроить автоматический бэкап Git репозиториев | Инфраструктура | infra‑bot | antigravity | Medium | 2026‑10‑15 | TODO |

### 🚀 Расширенные задачи Спринта 4 (Инновации & Масштабирование)

#### IT Operations Framework
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑ITOPS‑035 | 4 | Enterprise SSO & SAML2/OIDC Auth Module (Keycloak / Azure AD / Okta) | IT Operations | Чат IT Ops | IT Ops Agent | 🔴 P1 | 2026‑11‑05 | 📋 To Do |
| TASK‑ITOPS‑036 | 4 | Multi-Tenant Isolation & Customer Tenant Provisioning Engine | IT Operations | Чат IT Ops | IT Ops Agent | 🟡 P2 | 2026‑11‑08 | 📋 To Do |
| TASK‑ITOPS‑037 | 4 | Self-Healing Infrastructure Sentinel (Авто-восстановление при выходе метрик за пределы) | IT Operations | Чат IT Ops | IT Ops Agent | 🔴 P1 | 2026‑11‑12 | 📋 To Do |

#### BGT (bitget-bot)
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑BGT‑044 | 4 | Cross-DEX/CEX Delta-Neutral Funding Arbitrage Engine (Bitget / Hyperliquid) | BGT | Чат BGT | BGT Agent | 🔴 P1 | 2026‑10‑25 | 📋 To Do |
| TASK‑BGT‑045 | 4 | Emergency Volatility & Black Swan Circuit-Breaker (Отмена ордеров при резком дампе) | BGT | Чат BGT | BGT Agent | 🔴 P1 | 2026‑10‑28 | 📋 To Do |

#### LinkID Pro Post
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑LINKID‑033 | 4 | AI Visual Infographics & Meme Generator (Flux / SDXL API под брендбук) | LinkID | linkid-bot | LinkID Agent | 🔴 P1 | 2026‑10‑15 | 📋 To Do |
| TASK‑LINKID‑034 | 4 | Auto-Engagement & Smart Comment Replier Engine (Авто-ответы на комментарии) | LinkID | linkid-bot | LinkID Agent | 🟡 P2 | 2026‑10‑18 | 📋 To Do |

#### HH Jobs / HH Remote Jobs
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑HHJOBS‑017 | 4 | AI Salary Estimator & Tech-Stack Gap Matcher (Оценка вилки & проверка навыков) | HH Jobs | hh-jobs-bot | HH Jobs Agent | 🔴 P1 | 2026‑10‑15 | 📋 To Do |
| TASK‑HHJOBS‑018 | 4 | Automated One-Click Resume Tailoring Engine (Подгонка резюме и писем под вакансии) | HH Jobs | hh-jobs-bot | HH Jobs Agent | 🟡 P2 | 2026‑10‑20 | 📋 To Do |

#### Stocks UZ
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑STOCKS‑090 | 4 | Smart Money & Insider Accumulation Alert Engine (Детектор аномальных покупок на UZSE) | Stocks UZ | uz-stocks-bot | Stocks UZ Agent | 🔴 P1 | 2026‑11‑12 | 📋 To Do |
| TASK‑STOCKS‑091 | 4 | Automated DCF & Comparable Valuation Model (Авто-расчет справедливой стоимости) | Stocks UZ | uz-stocks-bot | Stocks UZ Agent | 🟡 P2 | 2026‑11‑15 | 📋 To Do |

#### GH Scout & Alpha Scout
| ID | Спринт | Задача | Проект / Домен | Ответственный чат / бот | Исполнитель (агент) | Приоритет | Срок | Статус |
|---|---|---|---|---|---|---|---|---|
| TASK‑GHSCOUT‑013 | 4 | Open-Source Trend Radar & Breakthrough Alert (Отслеживание быстрорастущих AI-проектов) | GH Scout | gh-scout-bot | GH Scout Agent | 🟡 P2 | 2026‑10‑18 | 📋 To Do |



