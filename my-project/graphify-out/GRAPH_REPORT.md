# Graph Report - .  (2026-07-31)

## Corpus Check
- Corpus is ~19,626 words - fits in a single context window. You may not need a graph.

## Summary
- 263 nodes · 423 edges · 14 communities
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.7)
- Token cost: 114,183 input · 0 output

## Community Hubs (Navigation)
- hh-jobs: Parser & Main Entrypoint
- Monorepo Docs & Hermes Workflow
- hh-remote-jobs: Main Entrypoint
- hh-jobs: HH Parser Details
- hh-remote-jobs: Matcher
- hh-remote-jobs: HH Client
- finanalytics Module
- hh-jobs: Bug Fixes & Ops Lessons
- hh-jobs: Responder (Rationale)
- hh-remote-jobs: Responder (Rationale)
- shared/db: Database Layer
- shared/tools: UZSE Ticker File
- shared/models: Data Models

## God Nodes (most connected - your core abstractions)
1. `Database` - 25 edges
2. `HHParser` - 16 edges
3. `hh-jobs STATUS.md (progress log)` - 16 edges
4. `Vacancy` - 15 edges
5. `Responder` - 14 edges
6. `VacancyMatcher` - 13 edges
7. `run_pipeline()` - 12 edges
8. `main()` - 11 edges
9. `HHClient` - 11 edges
10. `Responder` - 10 edges

## Surprising Connections (you probably didn't know these)
- `hh_parser.py (HHParser class)` --references--> `Database`  [EXTRACTED]
  hh-jobs/HERMES_TASK.txt → shared/db.py
- `MVP.md Technical Spec` --references--> `Database`  [EXTRACTED]
  hh-jobs/MVP.md → shared/db.py
- `hh_parser.py (HHParser class)` --references--> `Vacancy`  [EXTRACTED]
  hh-jobs/HERMES_TASK.txt → shared/models.py
- `MVP.md Technical Spec` --references--> `Vacancy`  [EXTRACTED]
  hh-jobs/MVP.md → shared/models.py
- `hh-jobs Project (README index)` --semantically_similar_to--> `hh-remote-jobs HERMES_TASK.md (Phase 1 MVP spec)`  [INFERRED] [semantically similar]
  README.md → hh-remote-jobs/HERMES_TASK.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Hermes-Claude-User Autonomous Development Loop** — hh_jobs_communication_protocol, hh_jobs_status_md, morning_report_hourly_monitoring, hh_jobs_autonomous_workflow [EXTRACTED 0.90]
- **HH-Jobs Parse-Match-Notify Pipeline** — hh_jobs_hh_parser, hh_jobs_matcher, hh_jobs_responder, hh_jobs_main_loop [EXTRACTED 0.95]
- **Lessons Transferred from hh-jobs to hh-remote-jobs** — hh_remote_jobs_lessons_from_hh_jobs, hh_jobs_target_skill_matches_fix_2, hh_jobs_word_boundary_matching, hh_jobs_flock_lockfile, hh_jobs_message_chunking [INFERRED 0.90]

## Communities (14 total, 0 thin omitted)

### Community 0 - "hh-jobs: Parser & Main Entrypoint"
Cohesion: 0.07
Nodes (34): HH.uz Parser — scraping tashkent.hh.uz search results (API requires OAuth).…, _acquire_lock(), load_config(), main(), _mark_run_completed(), _minutes_since_last_run(), HH Jobs Automation — Main Entry Point. Полный цикл: парсинг → матчинг →…, Main entry point: parse → match → notify. (+26 more)

### Community 1 - "Monorepo Docs & Hermes Workflow"
Cohesion: 0.13
Nodes (30): Commit Message Convention, CONTRIBUTING.md Contribution Guide, Tests & Code Quality CI Workflow, Autonomous Agent Workflow (Hermes works independently, Claude monitors, user interrupted only on blocker), Candidate Profile (IT Infrastructure Engineer, 19y exp, Tashkent, $4.5-6k), Blocker Escalation Protocol, Hermes ↔ Claude Communication Protocol, STATUS.md as Progress Diary (channel) (+22 more)

### Community 2 - "hh-remote-jobs: Main Entrypoint"
Cohesion: 0.13
Nodes (22): acquire_lock(), init_db(), main(), mark_digested(), mark_notified(), Connection, main.py — HH Remote Jobs оркестратор. Pipeline: HHClient.search_and_enrich() →…, Подключиться к SQLite, создать таблицу если её нет. (+14 more)

### Community 3 - "hh-jobs: HH Parser Details"
Cohesion: 0.14
Nodes (12): _contains_excluded(), HHParser, main(), Search vacancies, return list of Vacancy objects., Parse HTML search results page., Extract Vacancy from a search result card., Parse salary text. HH.uz uses 'сум' (UZS)., True if any exclude keyword occurs in `text` (already lowercased) as a whole… (+4 more)

### Community 4 - "hh-remote-jobs: Matcher"
Cohesion: 0.13
Nodes (15): _any_term_in_text(), _parse_experience(), Vacancy Matcher — оценивает совпадение удалённой вакансии с профилем. Алгоритм:…, Match remote vacancies against a user profile., Check if a vacancy should be hard-rejected. Returns: None if OK, or a string…, Score a single enriched vacancy dict. Returns: enriched dict with match fields…, Match multiple vacancies. Skips hard-rejected ones., Create matcher from .env file. (+7 more)

### Community 5 - "hh-remote-jobs: HH Client"
Cohesion: 0.14
Nodes (11): HHClient, _make_vacancy_id(), HH.ru API Client — поиск удалённых вакансий через публичное API. Использует…, Search for vacancies on HH. Returns list of raw vacancy dicts. Args: keywords:…, Convert raw HH API item to our internal format. Returns dict with keys matching…, Search HH and enrich results into internal format., Client for HH.ru / HH.kz public API (read-only)., Respect X-RateLimit headers and minimum delay. (+3 more)

### Community 6 - "finanalytics Module"
Cohesion: 0.18
Nodes (17): analytics.py (Financial analytics/reports), portfolio.py (Investment portfolio), FinAnalytics README, finanalytics requirements.txt (pandas, scikit-learn, plotly), wallet.py (Wallet/Accounts management), finanalytics Project (README index), market-events Project (planned), MY Project Monorepo (+9 more)

### Community 7 - "hh-jobs: Bug Fixes & Ops Lessons"
Cohesion: 0.18
Nodes (17): salary_currency hardcoded UZS bug fix, fcntl.flock Lock File (prevent parallel run duplicate sends), HERMES_TASK_2.txt Phase 2 (Telegram pivot), HH.uz Applicant API Auth Closed (2025-12-15), launchd Autostart Agent (com.vitaliyr.hh-jobs.plist), _send_chunked Telegram message splitting (avoid 4000-char truncation), Matcher salary-weight bias bug fix (redistribute weight when salary unstated), SEARCH_AREA_ID Fix (97, whole Uzbekistan) (+9 more)

### Community 8 - "hh-jobs: Responder (Rationale)"
Cohesion: 0.16
Nodes (9): Send `entries` (pre-formatted vacancy blocks) as one or more Telegram messages,…, Find all matched-but-unnotified vacancies and send notification. Args:…, Send a compact digest of weaker matches (below the notify threshold) so the…, Format a single vacancy line for the compact digest message., Notify about matched vacancies via Telegram., Send a batch notification about matched vacancies to Telegram. Args: vacancies:…, POST a pre-built message to the Telegram topic. Return True on success., Format a single vacancy block for the full notify() message. (+1 more)

### Community 9 - "hh-remote-jobs: Responder (Rationale)"
Cohesion: 0.17
Nodes (8): Responder — Telegram-уведомления о подобранных удалённых вакансиях. Принимает…, Форматировать число с пробелами-разделителями разрядов, без копеек., Разбить cards на части, не превышающие _MAX_MSG_LEN, и отправить. Каждая часть…, POST одного сообщения в Telegram Bot API (в топик, если thread_id задан)., Отправляет карточки вакансий в Telegram-топик., Отправить список вакансий в Telegram, разбив на части при необходимости. Args:…, Одна карточка вакансии: должность, компания, зарплата (оригинал + USD), score,…, Responder

### Community 10 - "shared/db: Database Layer"
Cohesion: 0.19
Nodes (7): Any, Connection, Get database connection, Execute INSERT query and return last row id, Execute UPDATE/DELETE query and return affected rows, Create table if not exists, Check if table exists

### Community 11 - "shared/tools: UZSE Ticker File"
Cohesion: 0.24
Nodes (10): build_search_query(), Генератор/обновление файла тикеров UZSE в формате, найденном в…, Прочитать xlsx в этом формате. Пропускает заголовок., Записать список TickerRow в xlsx с теми же колонками, что в оригинале., Обновить цену конкретного тикера в списке (in-place). Вернёт False если тикер…, Собрать SearchName в формате оригинала: "(Имя1 OR Имя2 OR TICKER)", read_tickers(), TickerRow (+2 more)

### Community 12 - "shared/models: Data Models"
Cohesion: 0.25
Nodes (4): Any, Convert to dictionary, User profile for matching, UserProfile

## Knowledge Gaps
- **11 isolated node(s):** `finanalytics requirements.txt (pandas, scikit-learn, plotly)`, `wallet.py (Wallet/Accounts management)`, `analytics.py (Financial analytics/reports)`, `cover_letter.py (AI cover letter generation)`, `vacancies SQLite table schema` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Database` connect `hh-jobs: Parser & Main Entrypoint` to `hh-jobs: Responder (Rationale)`, `Monorepo Docs & Hermes Workflow`, `shared/db: Database Layer`, `hh-jobs: HH Parser Details`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `Vacancy` connect `hh-jobs: Parser & Main Entrypoint` to `Monorepo Docs & Hermes Workflow`, `hh-jobs: HH Parser Details`, `shared/models: Data Models`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `hh_parser.py (HHParser class)` connect `Monorepo Docs & Hermes Workflow` to `hh-jobs: Parser & Main Entrypoint`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Database` (e.g. with `HHParser` and `VacancyMatcher`) actually correct?**
  _`Database` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `HHParser` (e.g. with `Database` and `Vacancy`) actually correct?**
  _`HHParser` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Vacancy` (e.g. with `HHParser` and `VacancyMatcher`) actually correct?**
  _`Vacancy` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `finanalytics requirements.txt (pandas, scikit-learn, plotly)`, `wallet.py (Wallet/Accounts management)`, `analytics.py (Financial analytics/reports)` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._