# 📊 Экосистема проектов — Master PM

> **Единый центр управления всеми проектами.**
> Для новых чатов: начинай с этого файла.
> Статус: 🟡 Active | Обновлено: 2026-09-01

---

## 🔷 Архитектура экосистемы

```
                    ┌──────────────────────────────┐
                    │     🤖 HERMES AGENT (Я)       │
                    │  Оркестратор, PM, DevOps       │
                    │  Mac + US Server + Oracle VM  │
                    └──────────┬───────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────────┐     ┌──────────┐
   │  🖥️ US   │        │    🍎 Mac    │     │ ☁️ Oracle │
   │  Server  │◄──────►│  (dev/код)   │◄───►│  VM      │
   │  24/7    │   ТS   │  RAG API     │  TS │  exit    │
   └────┬─────┘        └──────────────┘     └──────────┘
        │
   ┌────┴──────────────────────────────────────────────┐
   │  🌐 Data Bus (Tailscale)                         │
   │  Mac :3004 (RAG) ↔ US Server :3003 (Dashboard)   │
   │  Все сервисы доступны через единую точку входа    │
   └───────────────────────────────────────────────────┘
```

---

## 📋 Полный каталог проектов

### Легенда
- **P0** — Критично (деньги, доход)
- **P1** — Важно (работа, инфраструктура)
- **P2** — Планово (развитие)
- **P3** — Спящие (по необходимости)

---

### 🔴 P0: Деньги

#### 1. Bitget-bot — Трейдинг
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active 24/7 на **US Server** (`live-trend.service`) |
| **Суть** | Трендовый импульсный трейдинг (Momentum Breakout + ATR Trailing) |
| **Баланс** | **$107.97 USDT** чистый кэш (цели: **$120 до 13.09** → **$200** → **$1000 к концу сентября**) |
| **Стратегия** | Dynamic Compounding (до 85% депо в позиции, плечо 2x, риск 5% = ~$5.40 по ATR-стопу, трейлинг 3.5×ATR) |
| **Пул пар** | Топ-6 по бэктесту: ENA, SOL, ETH, XRP, UNI, BTC |
| **API** | Bitget Futures API v3 (ccxt + BitgetAPIClient), Telegram алерты |
| **Сервер** | US Server (`/home/us/bitget-bot/`), systemd (`live-trend.service`) |
| **Связи** | Trading Dashboard (:3002), Telegram Mini App (:8090) |
| **Изоляция** | 🟢 Изолирован — только API наружу |
| **Следующий шаг** | Взять цель $120 на первом же пробое (ETH/BTC/SOL) |

#### 2. Trading Dashboard
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active на **US Server** :3002 |
| **Суть** | Единый дашборд: Bitget + Hyperliquid баланс, позиции, P&L, история |
| **API** | `http://100.84.223.96:3002/api/portfolio` |
| **Связи** | Bitget-bot, Hyperliquid Grid Bot, Agent Dashboard |
| **Изоляция** | 🟢 Изолирован — read-only API |

#### 3. Hyperliquid Grid Bot
| Поле | Значение |
|------|----------|
| **Статус** | 📦 Skill на Mac, не запущен |
| **Суть** | Grid-трейдинг на Hyperliquid DEX |
| **API** | Hyperliquid public API |
| **Связи** | Trading Dashboard |
| **Изоляция** | 🟢 Изолирован |

#### 4. HH Jobs Suite — Мониторинг вакансий
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active 24/7 на **US Server** (`crontab` + `systemd`) |
| **Коллекторы** | 1. `hh-jobs` (Ташкент, 54kw/69sk, RSS)<br>2. `hh-remote` (СНГ-удалёнка, RSS)<br>3. `habr-jobs` (Хабр Карьера, REST API)<br>4. `remote-jobs` (RemoteOK + WeWorkRemotely) |
| **Telegram Mini App** | 🇺🇿 **«UZ IT Jobs»** (`https://us.tailc8105c.ts.net/uzjobs`) — FastAPI + SQLite (`:8095`), Tailscale Funnel HTTPS |
| **Сервер** | US Server `services/{hh-jobs,hh-remote,habr-jobs,remote-jobs}` |
| **Расписание** | HH Ташкент (каждые 2 ч 08:00–20:00), HH Remote (09,13,17,21), Habr (14,20), Remote (09:30,21:30) |
| **Telegram** | Топик 15 (HH Jobs, Habr, Remote), Топик 52 (HH-Remote), Menu Button у бота |
| **Изоляция** | 🟢 Изолирован |

---

### 🟡 P1: Инфраструктура и работа

#### 6. US Server (основной)
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active |
| **Характеристики** | Ubuntu 24.04, 4CPU/8GB RAM/145GB |
| **IP** | 100.84.223.96 (Tailscale) |
| **Сервисы** | Docker, Caddy, Uptime Kuma, Node Exporter, Bitget-bot, Trading Dashboard, Agent Dashboard, Health Check, Datacore, HH-jobs, HH-remote, FinAnalytics |
| **Доступ** | SSH: us@100.84.223.96 |
| **Роль** | 24/7 продакшен сервер |

#### 7. Oracle VM (exit node)
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active |
| **Характеристики** | 2CPU/954MB RAM/45GB |
| **IP** | 100.94.224.89 (Tailscale) |
| **Роль** | Exit node для интернет-трафика |

#### 8. Mac (разработка)
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active |
| **Характеристики** | M1, 8GB RAM, 256GB SSD |
| **IP** | 100.89.205.45 (Tailscale) |
| **Сервисы** | RAG API (:3004), ChromaDB, всё dev-окружение |
| **Роль** | Разработка, AI, RAG поиск |

#### 9. Agent Dashboard
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active на **US Server** :3003 |
| **Суть** | Мониторинг состояния агента, шина данных, RAG поиск |
| **API** | `http://100.84.223.96:3003/api/status` |
| **Связи** | Все сервисы, RAG на Mac через Tailscale |
| **Ядро экосистемы** | ✅ **ДА — единая точка входа** |

#### 10. Health Check
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active на **US Server** :8081 |
| **Суть** | Мониторинг всех сервисов |
| **API** | `http://100.84.223.96:8081/health` |
| **Проверяет** | Caddy, Docker, Bitget-bot, Node Exporter, Uptime Kuma, Tailscale, Trading Dashboard, Disk, Memory |

#### 11. Datacore (v2)
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active (Docker на US Server) |
| **Суть** | Сбор и анализ данных: Polymarket, Yahoo Finance |
| **Стек** | PostgreSQL 16, Redis 7, FastAPI (:8001), HTMX admin (:8080), Caddy gateway (:8083) |
| **API** | 100.84.223.96:8001 (core-api), 100.84.223.96:8083 (gateway) |
| **Структура** | 12 контейнеров, Redis Pub/Sub шина, единый .env |
| **Изоляция** | 🟢 Изолирован — своя БД, свои коллекторы |

#### 12. FinAnalytics
| Поле | Значение |
|------|----------|
| **Статус** | 🟡 Active на **US Server** |
| **Суть** | Управление долгами, бюджетирование, платёжный календарь |
| **Сервер** | US Server services/finanalytics |
| **Связи** | Telegram (topic 239 — FinAnalytics) |
| **Изоляция** | 🟢 Изолирован |

#### 13. AnyIdea
| Поле | Значение |
|------|----------|
| **Статус** | 🟡 Active на **US Server** |
| **Суть** | Сбор и проработка бизнес-идей. Интеграция с DataCore шиной |
| **Архитектура** | Core API (:8002), Gateway (:8083/anyidea/*), Telegram бот @anyidea_ai_bot, cron scout |
| **Стек** | PostgreSQL + Redis + FastAPI, EventBus anyidea:* каналы |
| **Связи** | Telegram (topic 7607 — AnyIdea), DataCore |
| **Изоляция** | 🟡 В экосистеме (через DataCore шину) |

#### 14. Expert Consilium (Консилиум Экспертов)
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active на US Server |
| **Суть** | Telegram бот + веб-дашборд: вопрос → 5 ИИ-экспертов → консолидированный ответ |
| **Роли** | Стратег (DeepSeek), Аналитик (Gemini), Критик (Claude), Креативщик (GPT-4o), Синтезатор (Grok) |
| **Режимы** | Smart Mode: базовый (бюджетный) / премиум (для сложных вопросов) |
| **Бот** | @Expert_consilium_bot, топик 7941 |
| **Сервер** | US Server services/expert-consilium, Docker Compose |
| **Стек** | PostgreSQL + Redis + FastAPI + OpenRouter + Caddy gateway |
| **Связи** | Web Dashboard, Caddy (:8083/consilium/*) |
| **Изоляция** | 🟡 В экосистеме (через Caddy gateway) |

#### 15. Multi-Agent Chat
| Поле | Значение |
|------|----------|
| **Статус** | 🟡 Active (Orbstack) |
| **Суть** | Multi-agent чат с несколькими AI |

---

### 🟢 GH Scout & Память (ядро мониторинга, 2026-08)

#### GH Scout — GitHub Project Monitor
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active на **US Server** :8005 |
| **Суть** | Мониторинг топовых GitHub проектов, трендов, генерация рекомендаций |
| **API** | `:8005`, gateway `/ghscout/*`, Telegram @ghscout_bot |
| **Проекты** | 17 конкурентов (Freqtrade, CCXT, AutoGPT, LangChain, CrewAI...) |
| **Cron** | Дайджест 11:00, Auto-Improver 10:00, Weekly Пн 10:00 |
| **Связи** | Context DB, Message Bus, все агенты |
| **Репозиторий** | `vitpandex-netizen/products` (в монорепо) |

#### Context DB — единая память
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active на **US Server** :8006 |
| **Суть** | Единое информационное поле для всех агентов (OpenViking-inspired) |
| **API** | `:8006`, gateway `/context/*`, CLI `ctx`, MCP для Claude/Codex |
| **Интеграции** | CLI + MCP + Message Bus + REST |
| **Репозиторий** | `vitpandex-netizen/context-db` |

#### Workspace — Unified Workspace
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active на **US Server** :8008 |
| **Суть** | Единое пространство: чат, дашборд, задачи, доки, нотификации (Macro-inspired) |
| **Веб** | `:8008`, gateway `/workspace/*`, Telegram Mini App |
| **Репозиторий** | `vitpandex-netizen/workspace` |

#### Trading Agents — Multi-Agent Trading
| Поле | Значение |
|------|----------|
| **Статус** | 🟡 Active (у BGT) |
| **Суть** | 5 AI-агентов голосуют по сделкам + FinRL + Web3 DeFi (TradingAgents-inspired) |
| **Репозиторий** | `vitpandex-netizen/trading-agents` |

#### MoneyPrinter — AI Video Generator
| Поле | Значение |
|------|----------|
| **Статус** | ⏸ Пауза (обсудить перед запуском) |
| **Суть** | Тема → AI сценарий → TTS → FFmpeg → видео (MoneyPrinterTurbo-inspired) |
| **Репозиторий** | `vitpandex-netizen/moneyprinter` |

#### Backup System
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active, ежедневно 3:00 UTC+5 |
| **Суть** | Бэкап всех PG баз + Context DB + конфигов, ротация 7 дней |
| **Скрипт** | `~/dev/gh-scout/scripts/backup.sh` на US Server |

---

#### 15. Hermes Web UI
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active |
| **Суть** | Веб-интерфейс для Hermes |

#### 16. Meeting Pipeline
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active |
| **Суть** | Автоматическая расшифровка и саммари встреч |

#### 17. Transcribe Bot / Service
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active (Orbstack) |
| **Суть** | Telegram бот для транскрибации голоса + API сервис |

---

### 🟡 P2: Проекты в работе

#### 18. UZ Market Bot
| Поле | Значение |
|------|----------|
| **Статус** | 🟡 WIP (Mac) |
| **Суть** | Telegram бот для поиска товаров на рынке Узбекистана |
| **Связи** | UZSE мониторинг, FinAnalytics |

#### 19. Stocks UZ (UZSE)
| Поле | Значение |
|------|----------|
| **Статус** | 🟡 Active на **US Server** |
| **Суть** | Мониторинг UZSE акций (56 тикеров) |
| **Сервер** | US Server projects/stocks-uz |
| **Связи** | UZ Market, FinAnalytics |

#### 20. Admin Panel
| Поле | Значение |
|------|----------|
| **Статус** | 🟡 WIP |
| **Суть** | Централизованная админка для всех сервисов |

#### 21. ITOPS — IT Operations Framework (коммерческий продукт)
| Поле | Значение |
|------|----------|
| **Статус** | 🟢 Active |
| **Суть** | **Отдельный коммерческий продукт.** Enterprise IT-поддержка: заявки, SLA, Telegram self-service, AI Voice Operator |
| **Архитектура** | Core Service + Event Bus (Redis) + PostgreSQL. Полностью независимая, своя шина, своя БД |
| **Сервер** | US Server (изолированная инфраструктура) |
| **Telegram** | Свой бот, отличается от всех наших личных проектов |
| **AI Voice** | STT → LLM → ответ, встроен в Telegram бот. Без Twilio |
| **Репозиторий** | `vitpandex-netizen/it-operations-framework` (отдельный) |
| **Изоляция** | 🟢 **Полная — НИКАК не связан с нашими проектами** |

---

### 🔵 P3: Спящие / Будущие

#### 22. NOFX
| Поле | Значение |
|------|----------|
| **Статус** | 💤 Sleep |
| **Суть** | Торговый бот (альтернатива Bitget) |

#### 23. Agents Toolkit
| Поле | Значение |
|------|----------|
| **Статус** | 💤 Sleep |
| **Суть** | Набор инструментов для AI-агентов |

#### 24. Scheduled Skills
| Поле | Значение |
|------|----------|
| **Статус** | 💤 Sleep |
| **Суть** | Планировщик задач по расписанию |

#### 25. LinkID Pro Post
| Поле | Значение |
|------|----------|
| **Статус** | 💤 Sleep |
| **Суть** | Автопостинг в соцсети |

---

## 🔷 Telegram чаты и топики

| Топик | ID | Проекты |
|-------|-----|---------|
| Expert Consilium | 7941 | Expert Consilium |
| UZ Stocks | 576 | Stocks UZ |
| US Stocks | 577 | — |
| HH Jobs | 15 | HH Jobs |
| HH Remote | 52 | HH Remote |
| Мониторинг | 203 | Health Check, Agent Dashboard |
| FinAnalytics | 239 | FinAnalytics, Trading Dashboard |
| InterP_Ai_Bot | 258 | — |
| DataCore Signals | 397 | Datacore |
| AnyIdea | 7607 | AnyIdea |

**Группа:** `-1004297012607` — AI Assistant Family

---

## 🔷 Шина данных (Data Bus)

```
Mac (RAG API :3004) ◄──Tailscale──► US Server (Agent Dashboard :3003)
     │                                      │
     │ ChromaDB поиск по коду               │ Trading Dashboard (:3002)
     │ Все проекты в ~/dev/                 │ Health Check (:8081)
     │                                      │ Datacore (:8001/8083)
     │                                      │ AnyIdea (:8002)
     └──────────────────────────────────────┘
```

**Принцип:** Mac — код и RAG, US Server — продакшен сервисы.
Связь через Tailscale. Если Mac выключен — RAG недоступен,
но продакшен сервисы работают.

---

## 🔷 Изоляция vs Экосистема

| Проект | В экосистеме? | Почему |
|--------|--------------|--------|
| Agent Dashboard | ✅ **Ядро** | Единая точка входа, шина данных |
| Trading Dashboard | ✅ Да | Потребляет данные из Bitget + HL |
| Health Check | ✅ Да | Мониторит все сервисы |
| Datacore | ✅ Да | Шина данных, EventBus |
| AnyIdea | ✅ Да | Через DataCore шину |
| Bitget-bot | ⚡ **Только API** | Изолирован, наружу только через API |
| Hyperliquid Bot | ⚡ **Только API** | Изолирован |
| HH Jobs | ❌ **Изолирован** | Независимый проект |
| HH Remote | ❌ **Изолирован** | Независимый проект |
| Meeting Pipeline | ❌ **Изолирован** | Независимый сервис |
| Transcribe Bot | ❌ **Изолирован** | Независимый сервис |
| UZ Market | ❌ **Изолирован** | Независимый проект |
| Stocks UZ | ❌ **Изолирован** | Независимый проект |
| FinAnalytics | ❌ **Изолирован** | Независимый проект |
| **Мобильное приложение** | 🔜 **Будет решено** | |

---

## 🎯 Мобильное приложение — План

**Отложено в отдельный чат.** Первичные вопросы:

| Вопрос | Статус |
|--------|--------|
| Платформа | 🔴 Не решено |
| API Gateway | 🔴 Нужно проектировать |
| Какие проекты входят | 🔴 Нужно определить |
| Изоляция от экосистемы | 🔴 Нужно решить |
| Монетизация | 🔴 Нужно придумать |

---

## 💰 Приоритет монетизации

```
1. Bitget-bot       → $88 → $100 → $200 → $500 (P0)
2. HH Jobs          → Найти работу IT Director (P1)
3. HH Remote        → Найти удалённую работу (P1)
4. FinAnalytics     → Контроль долгов и бюджета (P2)
5. UZ Markets       → UZSE дивиденды (P2)
6. Новые источники  → Фриланс, консалтинг, passive income (P3)
```

---

## ⚡ Быстрые команды для чатов

| Скажи | Что сделаю |
|-------|-----------|
| *«проекты»* | Покажу этот файл |
| *«статус»* | Покажу дашборд агента (:3003) |
| *«проект X»* | Открою проект, правила, статус |
| *«монетизация»* | Покажу стратегию дохода |
| *«архитектура»* | Покажу схему экосистемы |
| *«чат X»* | Покажу информацию о Telegram чате |
| *«Sync для чата»* | Отправлю этот файл в текущий чат |