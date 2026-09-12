# Triad Sync (Global Handoff & Context)

## Последнее обновление
- **Дата:** 2026-09-12
- **Проект:** BGT (bitget-bot)
- **Агент:** Antigravity

## Статус: 🟢 СПРИНТ 4 — P0 ИНФРАСТРУКТУРА ЗАВЕРШЕНА
Проект **BGT** переведен на полностью модульную архитектуру и защищен механизмами авто-восстановления.
- **Архитектура:** Monolith-файлы `bot.py` и `strategies.py` разбиты на пакеты `core/` и `strategies/`. Тесты успешно проходят, линтер чист.
- **Надежность:** Внедрена система `heartbeat` для `live_trend.py`. Скрипт `watchdog.py` теперь умеет сам делать `systemctl restart` зависшего торгового движка и принимать вебхуки от Prometheus Alertmanager для пересылки в Telegram.
- **Деплой:** Созданы systemd unit файлы (`bgt-live-trend.service`, `bgt-watchdog.service`, `bgt-exporter.service`) и установочный скрипт `deploy/install_services.sh`.

## Инструкции для следующего агента (BGT):
P0-задачи закрыты. Бот готов к накатыванию на боевой US-сервер (через `deploy/install_services.sh`). Можно приступать к задачам **P1 — Торговая логика и Risk Management** (Whale Sonar Filter, Dynamic Leverage & ATR-фильтры).

- **Проект:** BGT (bitget-bot)
- **Агент:** Antigravity

## Статус: 🟢 ЗАВЕРШЕНИЕ СПРИНТА 3 (Quality Gates & CI/CD)
Проект **BGT** успешно прошел фазу стабилизации инфраструктуры и тестирования.
- **Что сделано:** Зафиксированы точные версии в `requirements.txt`, настроен пайплайн CI/CD в GitHub Actions (`.github/workflows/ci.yml`), написано исчерпывающее покрытие тестами для API клиента (`test_api_client.py`), устранены все ошибки `flake8` и восстановлен синтаксис `live_trend.py`. 
- **Метрики качества:** Pytest (100% passed), Flake8 (0 ошибок), ИБ (без секретов в коде).
- **Бэклог:** Очищен `BACKLOG.md`, закрыт Спринт 3. Подготовлена структура для Спринта 4 (Рефакторинг `strategies.py`, Модули метрик, Whale Sonar).

## Инструкции для следующего агента (BGT):
Код-база чиста и протестирована. Можно приступать к Спринту 4, начиная с архитектурного рефакторинга (`strategies.py` и `bot.py`).


## Последнее обновление
- **Дата:** 2026-09-12
- **Проект:** HH Jobs
- **Агент:** Antigravity

## Статус: 🟢 ЭПИК ЗАВЕРШЕН (Спринты 1, 2, 3, 4)
Проект **HH Jobs** успешно переведён из состояния "Базовый парсер" в "Enterprise AI Career Agent".
- Интегрированы модули: Deep-LLM Scoring, Auto-Apply, Executive Scout, Whale Alerts, Multi-Persona (CIO/CISO/CTO), Resume PDF Tailoring, Habr Parser.
- Все задачи в `BACKLOG.md` (до TASK-HH-035 включительно) закрыты.
- Код прошел 5 рубежей качества (Quality Gates). Синтаксис проверен (`py_compile`), секреты в коде отсутствуют (соблюден ИБ Zero Tolerance), службы `uzjobs-tma.service` и `hhjob-bot.service` на US Server в статусе `active`.
- Оформлен мажорный релиз `v1.2.0` в `CHANGELOG.md`.

## Инструкции для следующего агента:
Проект HH Jobs полностью стабилизирован. Бэклог пуст. Вы можете планировать **Спринт 5** для HH Jobs или переключиться на другие проекты (Stocks UZ, BGT, LinkID, IT Ops), исходя из приоритетов владельца.
### 2026-09-12 09:15 - Antigravity
- **Проект**: LinkID Pro Post
- **Статус**: 🟢 DONE (Спринт 3 - Задачи продолжаются)
- **Что сделано**: 
  - Реализован TASK-LINKID-017 (Автогенерация визуальных обложек к постам).
  - Добавлено поле `cover_image_url` в модели `Post` и соответствующие Pydantic схемы.
  - Разработан сервис `ImageGenerator` для генерации картинок через DALL-E 3 API (с заглушкой при отсутствии ключа).
  - Celery-задача `generate_posts_task` теперь использует `ImageGenerator` для генерации обложек.
  - Обновлен `admin/templates/posts.html` для отображения превью сгенерированной картинки.
  - Написан миграционный скрипт `scripts/migrate_017_add_cover.py`.
- **Следующий шаг**: Настройка Prometheus метрик (TASK-LINKID-019).

## Последнее обновление
- **Дата:** 2026-09-12
- **Проект:** IT Ops
- **Агент:** Antigravity

## Статус: 🟢 ЗАВЕРШЕНИЕ СПРИНТА 4
Проект **IT Ops** успешно прошел QA (Quality Assurance) для кода, написанного в Спринте 4.
- **Что сделано:**
  1. Выполнены интеграционные и юнит тесты (`pytest` с mock Redis). Все тесты успешно пройдены (3/3).
  2. Запущен линтер `ruff` на новые модули (`sso.py`, `multitenancy.py`, `metrics.py`, `circuitbreaker.py`, `self_healing_sentinel.py`, `featureflags.py`). Ошибки форматирования и неиспользуемые импорты автоматически исправлены.
  3. Проведен ручной аудит ИБ (Слой 1): все конфигурации и ключи используют `os.getenv`, заглушки (mock data) безопасны. Hardcoded секретов нет.
  4. Обновления закоммичены и отправлены в `main` (commit `d494667`).
- **Спринт 4 официально закрыт.** Проект переведен в стабильное состояние, Enterprise Quality Gates соблюдены.

## Инструкции для следующего агента:
Можно приступать к планированию **Спринта 5**.
- Миграция БД и перезапуск контейнеров (api, admin, celery) на US Server выполнены успешно.
- **Проект**: LinkID Pro Post
- **Статус**: 🟢 DONE (Спринт 3 - Задачи продолжаются)
- **Что сделано**: 
  - Реализован TASK-LINKID-019 (Prometheus-метрики использования LLM).
  - Добавлен пакет `prometheus-client` в `requirements.txt`.
  - Эндпоинт `/metrics` выставлен в `app/main.py`.
  - В `ContentEngine` добавлены метрики: `llm_requests_total`, `llm_tokens_total`, `llm_latency_seconds`.
- **Следующий шаг**: Настройка CI/CD авто-тестов (TASK-LINKID-020).
### 2026-09-12 09:18 - Antigravity (Quality Gate & Sprint 3 Closure)
- **Проект**: Экосистема / Триада
- **Статус**: 🟢 DONE (Спринт 3 Завершен)
- **Что сделано**: 
  - Проведен локальный ИБ- и синтаксический аудит Python-кода (ошибок нет, хардкод секретов отсутствует).
  - Верифицирован статус production-контейнеров на US Server (все healthy/Up, healthcheck `/health` отдает 200 OK).
  - Оставшиеся некритичные задачи Спринта 3 (020, 021, 022, 023, 024) закрыты/перенесены в бэклог следующего Спринта 4.
  - Спринт 3 официально закрыт.
- **Следующий шаг**: Начать формирование Спринта 4.
### 2026-09-12 09:23 - Antigravity
- **Проект**: LinkID Pro Post
- **Статус**: 🟢 DONE (Спринт 4)
- **Что сделано**: 
  - Реализован TASK-LINKID-020 (Авто-тесты CI/CD для парсеров, генераторов и публикации).
  - Написаны базовые unit-тесты для `ContentEngine` и `ImageGenerator` (`pytest`, `pytest-asyncio`).
  - Создан GitHub Actions пайплайн (`.github/workflows/ci.yml`), включающий:
    - Запуск тестов.
    - Статический анализ на наличие секретов с помощью `gitleaks` (в рамках покрытия требования TASK-ITOPS-015).

## Последнее обновление
- **Дата:** 2026-09-12
- **Проект:** IT Ops
- **Агент:** Antigravity

## Статус: 🟢 ЗАВЕРШЕНИЕ СПРИНТА 5 (AIOps, Zero Trust, Chaos Engineering)
- **Что сделано:** Успешно спроектированы и внедрены 6 новых Enterprise-фич в `it-operations-framework`:
  1. `rca_agent.py` — Авто-генерация RCA отчетов на базе LLM.
  2. `jit_access.py` — Механизм выдачи временных (Just-In-Time) credentials в БД.
  3. `tracing.py` — Интеграция OpenTelemetry для распределенного трейсинга.
  4. `chaos.py` — Chaos Monkey Middleware для проверки отказоустойчивости Circuit Breaker.
  5. `zombie_hunter.py` — FinOps-скрипт поиска брошенных ресурсов и оптимизации затрат.
  6. Расширение `ratelimit.py` — Behavioral Rate Limiting (бан по аномалиям 4xx/5xx).
- Все тесты написаны и успешно пройдены (Pytest).
- ИБ аудит и PEP8 Линтер (Ruff) пройдены без ошибок.
- Изменения интегрированы в `main` и зафиксированы в `BACKLOG.md`.

## Инструкции для следующего агента (IT Ops):
Спринт 5 завершен. Проект IT Ops теперь обладает функционалом AIOps и Zero Trust. Ожидайте дальнейших указаний владельца (CIO) для Спринта 6.
### 2026-09-12 14:19 - Antigravity
- **Проект**: LinkID Pro Post
- **Статус**: 🟢 DONE (Спринт 4)
- **Что сделано**: 
  - Выполнена задача TASK-LINKID-021 (Systemd Watchdog & Auto-restart).
  - Скрипт `sentinel.sh` переписан в фоновый демон `sentinel-daemon.sh` с бесконечным циклом и ping'ом `systemd-notify WATCHDOG=1`.
  - Создан systemd service `linkid-sentinel.service` (WatchdogSec=600).
  - Создан systemd wrapper `linkid-app.service` для управления жизненным циклом `docker-compose up -d`.
  - Старые cron-скрипты удалены.
### 2026-09-12 14:25 - Antigravity
- **Проект**: LinkID Pro Post
- **Статус**: 🟢 DONE (Спринт 4)
- **Что сделано**: 
  - Реализован TASK-LINKID-033 (AI Visual Infographics & Meme Generator).
  - В `ImageGenerator` добавлены методы `generate_infographic` и `generate_meme`.
  - В `celery_app.py` добавлена привязка генерации нужных типов изображений по типу поста (`listicle`, `tutorial`, `funny`, `meme`).
  - Telegram-бот переведён на асинхронный вызов генерации через API Celery (`/api/v1/posts/generate`), полностью убран legacy `subprocess`.
  - В клавиатуру бота добавлены быстрые кнопки: «🤡 Мем/Шутка» и «📊 Инфографика».

### 2026-09-12 14:40 - Antigravity
- **Проект**: Cross-Triad R&D (UZ Stock, HH Jobs, BGT, LinkID, Data Lake)
- **Статус**: 🟢 СТРАТЕГИЧЕСКИЙ R&D-СПРИНТ ЗАВЕРШЁН
- **Что сделано**:
  - **BGT**: Разработан DSL-фреймворк для быстрой валидации стратегий (YAML-based) и безопасный AST-парсер (simpleeval). Добавлен Walk-Forward тестер `walkforward_test.py`.
  - **HH Jobs**: Реализован генератор персональных дайджестов (`digest_generator.py`) с учетом навыков, удаленки (`is_remote`) и гео-локации. Добавлен интерфейс бота (`/set_profile`, `/my_digest`).
  - **UZ Stock**: Внедрен кэш исторических данных (OHLCV) на InfluxDB (`docker-compose.yml`, `etl_historical.py`), API отдачи.
  - **LinkID**: Создан пакет провайдеров (`base_provider.py`, `rss_provider.py`). Написан специализированный парсер Habr (`habr_provider.py`), который интегрирован в `trend_analyzer.py`.
  - **Data Lake (Кросс-проект)**: Развернут MinIO (`common/data_lake`). Написан Airflow DAG `etl_cross_project.py` и Telegram-алертер `report_generator.py` для кросс-проектной аналитики.
- **Следующий шаг**: Деплой новых сервисов (InfluxDB, MinIO) на US Server.
