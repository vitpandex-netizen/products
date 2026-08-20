# Meeting Pipeline — Пайплайн обработки встреч

> Автоматическая обработка записей встреч: аудио → транскрипция → AI-анализ → Notion

---

## Обзор

Meeting Pipeline — это сервис для автоматической обработки записей встреч.
Пайплайн принимает аудиофайлы (или готовые транскрипты), транскрибирует их через
локальный Whisper, анализирует через DeepSeek (OpenRouter) и сохраняет
структурированный результат в Notion.

**Целевая аудитория:** команды и отделы, которые проводят много встреч и хотят
автоматически получать саммари, экшен-айтемы и заметки.

---

## Архитектура

```
meeting-pipeline/
├── meeting_service.py     # HTTP-сервис (порт 8001)
│   POST /process-audio    # Аудио → транскрипция → AI → Notion
│   POST /process-text     # Текст → AI → Notion
│   GET  /health           # Health check
├── watch_service.py       # Наблюдатель за папками (auto-watch)
├── auto_upload.py         # Настройка авто-выгрузки (rclone)
├── flush_notion.py        # Отправка очереди Notion-записей
├── Dockerfile             # Docker-образ (python:3.14-slim)
├── docker-compose.yml     # Docker Compose (зависит от transcribe-net)
├── ecosystem.config.js    # PM2-конфигурация
├── requirements.txt       # Python-зависимости
└── .interpreter-rules     # Правила для Interpreter
```

---

## Компоненты

### meeting_service.py — HTTP-сервис

Основной сервис пайплайна. Принимает HTTP-запросы:

| Endpoint | Метод | Описание |
|---|---|---|
| `/process-audio` | POST | Аудиофайл → Whisper (транскрипция) → DeepSeek (анализ) → Notion |
| `/process-text` | POST | Готовый транскрипт → DeepSeek (анализ) → Notion |
| `/health` | GET | Health check |

**Технологии:**
- Транскрипция: локальный Whisper (модель `small`)
- AI-анализ: DeepSeek v4 Flash через OpenRouter
- Нотификация: Notion (через queue-файлы → Interpreter MCP)

### watch_service.py — Наблюдатель

`watch_service.py --dir /path/to/recordings/` — запускает polling-наблюдатель
за указанной директорией. При появлении нового аудиофайла автоматически отправляет
его на обработку в meeting_service.

- Поддерживает рекурсивный обход (`--recursive`)
- Проверяет, что файл полностью записан (сравнивает размер с паузой 3с)
- Обрабатывает файлы по убыванию mtime (новейшие — первыми)

### auto_upload.py — Авто-выгрузка

Настройка автоматической синхронизации записей из облачных хранилищ:

- **Zoom:** Автозапись в облако → rclone sync → локальная папка
- **Google Meet:** Meet Transcript / Tactiq → Google Drive → rclone
- **Microsoft Teams:** SharePoint → rclone sync
- **Универсально:** rclone sync с launchd (macOS) для периодической синхронизации

### flush_notion.py — Отправка в Notion

Читает очередь Notion-записей (`/tmp/meeting_pipeline/notion_queue/`) и отправляет
их через Interpreter MCP (notion-create-pages).

- Режим `--watch`: непрерывное наблюдение за очередью
- Режим `--once`: однократная обработка всех ожидающих записей
- Автоматическое перемещение обработанных файлов в `processed/`, ошибок — в `error/`

---

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить API-ключ OpenRouter
# Ключ хранится в ~/.secure/vault.py (get OPENROUTER_API_KEY)

# 3. Запустить сервис
python3 meeting_service.py

# 4. Отправить файл на обработку
curl -X POST http://localhost:8001/process-audio \
  -H "Content-Type: application/json" \
  -d '{"audio_path": "/path/to/recording.mp3", "title": "Еженедельный синк"}'

# 5. Или запустить наблюдатель за папкой
python3 watch_service.py --dir /Volumes/External/recordings/
```

### Docker

```bash
docker compose up -d
```

### PM2 (production)

```bash
pm2 start ecosystem.config.js
```

---

## Формат ответа

```json
{
  "status": "ok",
  "title": "Название встречи",
  "transcript_length": 12345,
  "summary": "Краткое саммари встречи",
  "action_items": "- **Имя**: Задача",
  "notion_url": "queue://notion_queue_20260813_120000_abc123.json",
  "analysis": {
    "summary": "...",
    "extended_summary": "...",
    "bullet_notes": "...",
    "action_items": "...",
    "participants_guessed": ["Имя1", "Имя2"],
    "type_guessed": "Внутренняя",
    "tags_guessed": ["важное", "решения"]
  }
}
```

---

## Зависимости

- Python 3.14+
- Whisper (локальная модель `small`)
- OpenRouter API ключ
- Notion (через Interpreter MCP)
- ffmpeg (для аудио)
- Docker (опционально)
- PM2 (опционально, для production)

---

## Лицензия

MIT