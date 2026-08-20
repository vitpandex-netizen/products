# transcribe-bot 🤖🎙

**Telegram-бот для транскрибации голосовых и аудиосообщений в текст.**

Принимает голосовые, аудиофайлы и видеозаметки в личных сообщениях, отправляет их на `transcribe-service` (faster-whisper) и возвращает расшифровку с таймстемпами в виде файла.

Бот предназначен для личного/семейного использования — доступ по заявкам через RBAC.

---

## Архитектура

```
Пользователь
    │ голосовое / аудио
    ▼
┌──────────────┐     POST /transcribe     ┌────────────────────┐
│ transcribe-bot│ ───────────────────────► │ transcribe-service │
│  (Telegram)   │ ◄─────────────────────── │  (FastAPI + WHISPER)│
└──────────────┘    JSON {text, segments}  └────────────────────┘
    │
    ▼
Расшифровка (.txt) → пользователю
```

- **Транскрибация** — только в личных сообщениях (с 2026-08-04)
- **Админ-панель** — в топике Admin супергруппы (inline-кнопки)
- **Meeting Pipeline** — опционально: DeepSeek-анализ → Notion

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.12 |
| Telegram API | Long-polling (requests) |
| Транскрибация | transcribe-service (faster-whisper) |
| Админ-панель | Inline-кнопки Telegram |
| RBAC | state.json (файловое хранение) |
| Запуск | Docker Compose |
| Сеть | transcribe-net (shared) |

---

## Быстрый старт

```bash
# 1. Клонировать и настроить
cp .env.example .env
# Заполнить TELEGRAM_BOT_TOKEN, CHAT_ID, ADMIN_USER_IDS

# 2. Убедиться, что есть общая сеть
docker network create transcribe-net 2>/dev/null || true

# 3. Запустить
docker-compose up -d --build
```

### Переменные окружения (.env)

| Переменная | Обязательная | Описание |
|-----------|:-----------:|----------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен бота (@you_transcriptions_bot) |
| `TELEGRAM_CHAT_ID` | ✅ | ID супергруппы |
| `TELEGRAM_THREAD_ID` | ✅ | Топик Transcribe-Service (59) |
| `ADMIN_THREAD_ID` | ✅ | Топик Admin (66) |
| `ADMIN_USER_IDS` | ✅ | ID владельцев (через запятую) |
| `TRANSCRIBE_SERVICE_URL` | — | http://transcribe-service:8000 |
| `STATE_PATH` | — | /data/state.json |

---

## Файлы проекта

| Файл | Назначение |
|------|-----------|
| `main.py` | Polling-цикл, обработка сообщений, `process_audio()` |
| `bot_api.py` | Обёртка Telegram API (sendMessage, sendDocument, downloadFile) |
| `admin_panel.py` | Кнопочная admin-панель (inline keyboards) |
| `state.py` | RBAC + scope-реестр, персистент в JSON |
| `Dockerfile` | Контейнер на python:3.12-slim |
| `docker-compose.yml` | Сервис + сеть + volumes |
| `vault.sh` | AES-256 vault для секретов |
| `setup.sh` | Первоначальная настройка |

---

## RBAC (Ролевая модель)

- **Owner** — задаётся через `ADMIN_USER_IDS` в .env, не может быть понижен через бота
- **Admin** — управляет пользователями через admin-панель
- **User** — имеет доступ к транскрибации

Пользователи запрашивают доступ через личку → админы получают уведомление с кнопками Одобрить/Отклонить.

---

## API (внутренние)

Бот обращается к:
- **Telegram Bot API** — `https://api.telegram.org/bot<TOKEN>/...` (или self-hosted)
- **transcribe-service** — `POST /transcribe`, `GET /health`
- **meeting-pipeline** — `POST /process-text` (опционально)

---

## Статус

Проект в активной разработке. См. [ROADMAP.md](./ROADMAP.md) и [CHANGELOG.md](./CHANGELOG.md).