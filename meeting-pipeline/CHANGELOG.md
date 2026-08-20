# Meeting Pipeline — Changelog

> Versioning: semver. Формат: [версия] ГГГГ-ММ-ДД — описание.

---

## [Unreleased]

### Added
- **README.md** — полная документация проекта
- **ROADMAP.md** — дорожная карта развития
- **CHANGELOG.md** — этот файл
- **STATUS.md** — статус проекта

---

## [0.2.0] — 2026-08-12

### Added
- **watch_service.py** — polling-наблюдатель за директорией: автоматическая обработка новых аудиофайлов
  - Поддержка рекурсивного обхода (`--recursive`)
  - Проверка целостности файла (ожидание завершения записи)
  - Сортировка по mtime (новейшие — первыми)
- **auto_upload.py** — настройка авто-выгрузки записей из облачных хранилищ
  - rclone sync с launchd (macOS)
  - Инструкции для Zoom, Google Meet, Microsoft Teams
  - Поддержка Dropbox, Google Drive, SharePoint
- **flush_notion.py** — обработчик очереди Notion-записей
  - Режимы `--watch` (непрерывный) и `--once` (однократный)
  - Автоматическое перемещение в processed/error
  - Интеграция с Interpreter MCP (notion-create-pages)
- **Dockerfile** — python:3.14-slim, ffmpeg, curl
- **docker-compose.yml** — сервис + внешняя сеть transcribe-net
- **ecosystem.config.js** — PM2-конфигурация (meeting-pipeline + meeting-watch)
- **.interpreter-rules** — правила для Interpreter Agent

### Changed
- **meeting_service.py** — улучшена обработка ошибок (try/except для каждого этапа)
- **meeting_service.py** — добавлены параметры host, meeting_type, participants, tags

### Fixed
- Исправлена обработка длинных транскриптов (обрезание >15000 символов)

---

## [0.1.0] — 2026-08-10

### Added
- **meeting_service.py** — HTTP-сервис на базе http.server (порт 8001)
  - `POST /process-audio` — аудио → Whisper (транскрипция) → DeepSeek (анализ) → Notion queue
  - `POST /process-text` — текст → DeepSeek (анализ) → Notion queue
  - `GET /health` — health check
- **Whisper integration** — локальная транскрипция через builtin-transcribe (модель small)
- **DeepSeek integration** — AI-анализ через OpenRouter (deepseek-v4-flash)
  - Структурированный JSON: summary, extended_summary, bullet_notes, action_items, participants, type, tags
- **Notion integration** — сохранение результатов в очередь JSON-файлов
  - Поля: Meeting Title, Date & Time, Summary, Extended Summary, Bullet Notes, Action Items, Status
  - Опционально: Meeting Host, Type, Participants, Tags, Transcript Link
- **requirements.txt** — requests, python-dotenv

### Architecture
- Трёхэтапный пайплайн: транскрипция → анализ → сохранение
- Асинхронная запись в Notion через queue-файлы (очередь обрабатывается отдельно)
- API-ключ через vault.py (без хранения в файлах)
- Обрезка транскриптов >15000 символов для предотвращения превышения лимитов