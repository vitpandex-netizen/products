# 📋 Единый бэклог Триады (Triad Unified Backlog)

> **Статус:** Канонический реестр задач всей экосистемы (`Antigravity` + `Claude Code` + `Hermes` + `QA Team`).  
> **Правило:** Любая доработка, фикс бага или архитектурная задача **обязательно** фиксируется здесь с указанием Спринта, Приоритета, Ответственного Чата, Дедлайна и Definition of Done (DoD).

---

## 🎯 Спринты экосистемы

- **🏁 Спринт 1 (11 сентября 2026 г.):** Базовая инфраструктура BGT, Donchian-96, Daily Optimizer, Kill-Switch, Market Greed, Smart Scaling Out, Whale CVD Filter. *(Завершён)*
- **🏆 Спринт 2 (11 сентября 2026 г.):** HFT Binance Lead-Lag, Short Breakouts, Dynamic Leverage Engine, Paper Auto-Promoter, Executive Morning Digest, TMA Signals API. *(Завершён)*
- **🚀 Спринт 3 (12–20 сентября 2026 г.):** Масштабирование BGT к цели $1000/мес: визуальный TMA "BGT Signals" UI, Machine Learning фильтр (XGBoost), Умный компаундинг депозита $107 → $120 → $200 → $1000, Black Swan Circuit Breaker. *(Текущий активный спринт)*

---

## 📊 Единый реестр задач спринтов

| ID | Спринт | Задача | Проект / Домен | Ответственный Чат / Бот | Исполнитель (Агент) | Приоритет | Срок | Статус |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **TASK-001** | **Спринт 1** | Восстановление `ghscout-core` (DNS коллизия postgres/redis) | **GH Scout** | Чат GH Scout (`@ghscout_bot`) | **Antigravity** | 🔴 P1 | 2026-09-12 | 🟢 Done |
| **TASK-002** | **Спринт 1** | Включение `datacore-pg`, `consilium`, `ghscout` в ночной бэкап | **DataCore / Consilium** | Чат DataCore / Master Orchestrator | **Antigravity** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-003** | **Спринт 1** | Сетевая изоляция API: биндинг портов `127.0.0.1` на US Server | **Инфраструктура / API** | Чат Master Orchestrator (Antigravity) | **Antigravity** | 🔴 P1 | 2026-09-12 | 🟢 Done |
| **TASK-004** | **Спринт 1** | Автоматизация приема баг‑репортов (QA Intake Engine `scripts/qa_intake.py`) | **QA Track / Триада** | Чат Master Orchestrator (Antigravity) | **Antigravity** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-005** | **Спринт 1** | [HH Jobs] Ошибка выборки: `no such column: published_at` в боте | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-12 | 🟢 Done |
| **TASK-006** | **Спринт 1** | Разработка Единой политики Триады и стандартов релизного управления | **Экосистема / Триада** | Чат Master Orchestrator (Antigravity) | **Antigravity** | 🔴 P1 | 2026-09-12 | 🟢 Done |
| **TASK-007** | **Спринт 1** | [Stocks UZ] Не отображается график тикера URTS на мобильном TMA | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-12 | 🟢 Done |
| **TASK-008** | **Спринт 1** | [HH Jobs] Архивация и очистка неактуальных вакансий (Retention Policy) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-13 | 🟢 Done |
| **TASK-009** | **Спринт 1** | [HH Jobs] Полная персонализация AI‑матчинга под резюме пользователя | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🔴 P1 | 2026-09-11 | 🟢 Done |
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
| **TASK-LINKID-001** | **Спринт 2** | [LinkID] Динамический выбор LLM в веб‑админке (`:8015`) + сохранение в БД | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Чат LinkID** | 🔴 P1 | 2026-09-14 | 📋 To Do |
| **TASK-LINKID-002** | **Спринт 2** | [LinkID] Асинхронная очередь генерации постов через Celery / Redis | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity / LinkID Agent** | 🔴 P1 | 2026-09-15 | 📋 To Do |
| **TASK-LINKID-004** | **Спринт 2** | [LinkID] Интеграция авто‑публикации постов в LinkedIn (REST API Cron) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🔴 P1 | 2026-09-16 | 📋 To Do |
| **TASK-LINKID-008** | **Спринт 2** | [LinkID] Редактор профиля тональности и стиля автора (Tone Profile) в TMA | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-LINKID-009** | **Спринт 2** | [LinkID] Автогенерация обложек и инфографики к постам (DALL‑E 3 / Flux API) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🔵 P3 | 2026-09-18 | 📋 To Do |
| **TASK-LINKID-010** | **Спринт 2** | [LinkID] Авто-кросспостинг анонсов постов в Telegram-топик команды | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-15 | 📋 To Do |
| **TASK-LINKID-011** | **Спринт 2** | [LinkID] Аналитика просмотров и охватов LinkedIn в TMA (Engagement Tracker) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-LINKID-012** | **Спринт 2** | [LinkID] Динамический менеджер источников новостей (RSS/TG-каналы) в админке | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🟡 P2 | 2026-09-16 | 📋 To Do |
| **TASK-LINKID-013** | **Спринт 2** | [LinkID] Healthcheck Sentinel & Auto-heal (Авто-восстановление сетевых роутов) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **Antigravity** | 🔴 P1 | 2026-09-14 | 📋 To Do |
| **TASK-LINKID-014** | **Спринт 2** | [LinkID] Экспорт контент-плана постов в iCal / Google Calendar (.ics feed) | **LinkID Pro Post** | Чат LinkID (`@linkid_ai_bot`) | **LinkID Agent** | 🔵 P3 | 2026-09-18 | 📋 To Do |
| **TASK-ITOPS-005** | **Спринт 2** | Core API Hardening: Graph Token Cache & Rate Limiting | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-15 | 📋 To Do |
| **TASK-ITOPS-007** | **Спринт 2** | Распределённый Rate Limiting через Redis (Sliding Window / IncrBy) | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-16 | 📋 To Do |
| **TASK-ITOPS-008** | **Спринт 2** | Executive PDF/Excel Digest Engine для CIO (SLA & Инциденты) | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-ITOPS-009** | **Спринт 2** | Telegram Mini App Status Page & Service Health (Мониторинг сервисов) | **IT Operations** | Чат IT Ops | **Чат IT Ops** | 🟡 P2 | 2026-09-18 | 📋 To Do |
| **TASK-IMP-001** | **Спринт 2** | Добавить preview‑mode для автогенерации постов в LinkID | **LinkID** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-002** | **Спринт 2** | Сохранять историю последних 5 выбранных LLM и предлагать автодополнение | **LinkID** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-003** | **Спринт 2** | Реализовать retry‑логику с экспоненциальной задержкой для неуспешных вебхуков | **LinkID** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-004** | **Спринт 2** | Добавить конфигурируемые лимиты per‑client/IP в админ‑панель Rate Limiting | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-005** | **Спринт 2** | Встроить Prometheus‑exporter для мониторинга счётчиков лимитов | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-006** | **Спринт 2** | Автогенерировать превью‑версии PDF/Excel отчётов (png) для быстрой проверки | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-007** | **Спринт 2** | Создать микросервис status‑checker для health‑check внешних сервисов (SMTP, AD, 1С) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-008** | **Спринт 2** | Добавить step в CI‑pipeline static‑analysis (bandit, safety) | **IT Operations** | Чат IT Ops | **CI/CD** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-009** | **Спринт 2** | Автоматически генерировать OpenAPI‑спецификацию из FastAPI и публиковать в `/docs` | **IT Operations** | Чат IT Ops | **CI/CD** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-010** | **Спринт 2** | Добавить e2e‑тесты (Cypress/Playwright) для основных пользовательских сценариев | **IT Operations** | Чат IT Ops | **QA Team** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-011** | **Спринт 2** | [LinkID] AI Content Quality & Toxicity Guard (проверка постов перед публикацией) | **LinkID Pro Post** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-012** | **Спринт 2** | [LinkID] Multi‑Format Repurposing (генерация анонсов для Telegram / X из постов) | **LinkID Pro Post** | Чат LinkID | **LinkID Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-013** | **Спринт 2** | [IT Ops] Audit Trail & Compliance Logger в PostgreSQL | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-014** | **Спринт 2** | [IT Ops] Circuit Breaker pattern для внешних API (Graph API / STT Whisper) | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🔴 P1 | 2026-09-19 | 📋 To Do |
| **TASK-IMP-015** | **Спринт 2** | [IT Ops] Dynamic Feature Flags Manager (Redis/TMA) без перезапуска сервисов | **IT Operations** | Чат IT Ops | **IT Ops Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-016** | **Спринт 2** | [Stocks UZ] Backtesting Engine для дивидендных и объёмных стратегий UZSE | **Stocks UZ** | Чат Stocks UZ | **Stocks Agent** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-IMP-017** | **Спринт 2** | [Alpha Scout] Multi‑DEX Liquidity Depth Scanner (учёт Slippage и Price Impact) | **Alpha Scout** | Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-18 | 📋 To Do |
| **TASK-IMP-018** | **Спринт 2** | [Инфраструктура] Centralized Log Rotation (сжатие логов Docker 14 дней на US Server) | **Инфраструктура** | Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-15 | 📋 To Do |
| **TASK-IMP-019** | **Спринт 2** | [Безопасность] Auto Secret Scanner Pre‑Commit Hook (gitleaks / secret-guard) | **Экосистема** | Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-14 | 📋 To Do |
| **TASK-IMP-020** | **Спринт 2** | [QA / Триада] Auto‑Smoke Test Suite after Deployment (Quality Gate #4) | **QA Track** | Master Orchestrator | **QA Team** | 🟡 P2 | 2026-09-20 | 📋 To Do |
| **TASK-010** | **Спринт 2** | [Stocks UZ] Push‑уведомления "Утренний Бриф" в Telegram (09:50 AM) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-14 | 📋 To Do |
| **TASK-011** | **Спринт 2** | [Stocks UZ] Модуль Risk‑Management и Asset Allocation (Pie Charts) в TMA | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-15 | 📋 To Do |
| **TASK-012** | **Спринт 2** | [Stocks UZ] AI‑Сканер Аномальных Объёмов (Smart Money Detection) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-16 | 📋 To Do |
| **TASK-013** | **Спринт 2** | [Stocks UZ] Фундаментальный AI‑Скринер (Value Investing: P/E, P/B, ROE) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-15 | 📋 To Do |
| **TASK-STOCKS-014** | **Спринт 2** | [Stocks UZ] Telegram Instant Signal Alerts (Детектор инсайдерских выкупов) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-15 | 📋 To Do |
| **TASK-STOCKS-016** | **Спринт 2** | [Stocks UZ] Авто-мониторинг OpenInfo.uz (Существенные факты и отчеты) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🔴 P1 | 2026-09-16 | 📋 To Do |
| **TASK-STOCKS-017** | **Спринт 2** | [Stocks UZ] Калькулятор дивидендной доходности (Yield to Cost в UZS) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-15 | 📋 To Do |
| **TASK-STOCKS-018** | **Спринт 2** | [Stocks UZ] Сканер неликвидных стаканов и неэффективных спредов (>10%) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-STOCKS-019** | **Спринт 2** | [Stocks UZ] Target Price Push-Alerts (Уведомления о достижении цен закупки) | **Stocks UZ** | Чат Stocks UZ (`@stock_uz_bot`) | **Чат Stocks UZ** | 🟡 P2 | 2026-09-14 | 📋 To Do |
| **TASK-BGT-011** | **Спринт 2** | BGT: Интеграция "Уровня Жадности" (Market Greed / Regime Filter) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-16 | 📋 To Do |
| **TASK-BGT-012** | **Спринт 2** | BGT: Динамический TP/SL (Smart Scaling Out) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-BGT-015** | **Спринт 2** | BGT: All-Weather Архитектура (Мульти-режимность тренд/флэт) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🔴 P1 | 2026-09-18 | 📋 To Do |
| **TASK-BGT-018** | **Спринт 2** | BGT: WebSocket Price Stream Engine (переход с REST-поллинга на котировки) | **BGT (Bitget Bot)** | Чат BGT | **Antigravity / BGT Agent** | 🔴 P1 | 2026-09-16 | 📋 To Do |
| **TASK-BGT-019** | **Спринт 2** | BGT: AI Safety Circuit-Breaker (Защита от сбоев биржи при SL) | **BGT (Bitget Bot)** | Чат BGT | **Antigravity / BGT Agent** | 🔴 P1 | 2026-09-15 | 📋 To Do |
| **TASK-BGT-023** | **Спринт 2** | BGT: Lead-Lag Сигнал Binance (Cross-Exchange Front-running) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🔴 P1 | 2026-09-14 | 📋 To Do |
| **TASK-BGT-024** | **Спринт 2** | BGT: Пирамидинг на супер-трендах (Safe Pyramiding) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-15 | 📋 To Do |
| **TASK-BGT-025** | **Спринт 2** | BGT: Утренний Executive Дайджест в Telegram (08:00 UTC+5) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟢 P3 | 2026-09-13 | 📋 To Do |
| **TASK-BGT-026** | **Спринт 2** | BGT: Детектор сжатия волатильности (TTM Squeeze Detector) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent** | 🟡 P2 | 2026-09-16 | 📋 To Do |
| **TASK-ALPHA-001** | **Спринт 2** | [Alpha Scout] Polymarket On-Chain Whale Alert Bot (Авто-трекинг кошельков) | **Alpha Scout / Trading** | Чат Master Orchestrator | **Antigravity** | 🔴 P1 | 2026-09-14 | 📋 To Do |
| **TASK-ALPHA-002** | **Спринт 2** | [Alpha Scout] DEX/CEX Spread Scanner (Сопоставление Raydium с Bitget) | **Alpha Scout / Trading** | Чат Master Orchestrator | **Antigravity** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-BGT-027** | **Спринт 3** | BGT Signals Telegram Mini App (Витрина сигналов под модель $35/мес) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-15 | 📋 To Do |
| **TASK-BGT-028** | **Спринт 3** | Machine Learning Signal Filter (XGBoost/LightGBM фильтр ложных входов) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-16 | 📋 To Do |
| **TASK-BGT-029** | **Спринт 3** | Динамический Авто-Балансировщик Капитала на основе Sharpe Ratio | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-BGT-030** | **Спринт 3** | Умный Авто-Компаундинг Депозита ($107 → $120 → $200 → $1000) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔴 P1 | 2026-09-14 | 📋 To Do |
| **TASK-BGT-031** | **Спринт 3** | Защита от Чёрных Лебедей (Flash Crash Black Swan Circuit Breaker) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🟡 P2 | 2026-09-15 | 📋 To Do |
| **TASK-BGT-032** | **Спринт 3** | DEX On-Chain Liquidity Watcher (Uniswap v3 / Raydium Pool Tracker) | **BGT (Bitget Bot)** | Чат BGT | **BGT Agent / Antigravity** | 🔵 P3 | 2026-09-18 | 📋 To Do |
| **TASK-HH-010** | **Спринт 2** | [HH Jobs] Auto-Draft Cover Letter Generator (Генерация отклика в 1 клик) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-16 | 📋 To Do |
| **TASK-HH-014** | **Спринт 2** | [HH Jobs] Умный парсинг требований (LLM): извлечение неявных навыков и ЗП | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-15 | 📋 To Do |
| **TASK-HH-015** | **Спринт 2** | [HH Jobs] Трекинг статусов откликов в TMA (через интеграцию с почтой/API) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-16 | 📋 To Do |
| **TASK-HH-016** | **Спринт 2** | [HH Jobs] Авто-генератор кастомных резюме под вакансию (Resume Tailoring) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🔴 P1 | 2026-09-17 | 📋 To Do |
| **TASK-HH-017** | **Спринт 2** | [HH Jobs] AI-Ассистент подготовки к собеседованию (Interview Prep) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🟡 P2 | 2026-09-17 | 📋 To Do |
| **TASK-HH-018** | **Спринт 2** | [HH Jobs] Анализатор зарплатных вилок рынка Узбекистана (Salary Intelligence) | **HH Jobs** | Чат HH Jobs (`@hhjob_ai_bot`) | **Чат HH Jobs** | 🔵 P3 | 2026-09-18 | 📋 To Do |
| **TASK-SYS-002** | **Спринт 2** | Unified Health Dashboard & Daily Backup Verification (Дайджест в 08:00) | **Инфраструктура / Сервер** | Чат Master Orchestrator | **Antigravity (Сисадмин)** | 🟡 P2 | 2026-09-14 | 📋 To Do |

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
| **2026-09-11** | **Alpha Stream (Идея №1)** | **Prediction Markets Arbitrage & Whale Scanner (Polymarket)** | Разработка модуля `alpha-scout` для поиска спредов/арбитража вероятностей 5m BTC и трекинга кошельков топ-50 трейдеров Polymarket с алертами в Telegram. | ⏳ In Progress (`scratch/`) |
| **2026-09-11** | **BGT Upgrade** | **BGT Dynamic Volatility Regime (ATR Expansion Filter)** | Фильтр флэтового болота для BGT: вход в сделки только на расширении волатильности (`a_short / a_long >= 1.05`) для исключения ложных входов. | 🟢 Done (`v0.2.1`) |
