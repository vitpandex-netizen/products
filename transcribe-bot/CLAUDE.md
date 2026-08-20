# transcribe-bot — Context for Claude Code / Hermes

## Что это

Telegram-бот `@you_transcriptions_bot` для персональной транскрибации аудио.
- Принимает голосовые/аудиофайлы в личном чате (в группе — редиректит в личку)
- Отправляет на `transcribe-service` (faster-whisper, CPU, int8, модель medium, язык ru)
- Возвращает расшифровку пользователю
- 3-уровневый RBAC: owner → admin → user
- Кнопочная admin-панель в топике Admin супергруппы

## Инфраструктура

- Docker-контейнеры, команда `docker-compose` (не `docker compose`)
- Сеть: `transcribe-net` (shared с transcribe-service)
- Данные: `/Volumes/External/docker-volumes/transcribe-bot/data/state.json`
- Секреты: `/Volumes/External/dev/transcribe-bot/.env` (права 600, в .gitignore)
- Git: `github.com/vitpandex-netizen/transcribe-bot`, ветка `main`
- После изменений: `docker-compose up -d --build` + коммит + пуш

## Контейнеры

| Сервис | Образ | Роль |
|---|---|---|
| `telegram-bot-api` | `aiogram/telegram-bot-api:latest` | Локальный Telegram Bot API (лимит 2000 МБ вместо 20) |
| `transcribe-bot` | сборка из `Dockerfile` | Основной бот |

Бот обращается к Telegram через `http://telegram-bot-api:8081` (env `TELEGRAM_API_ROOT`).
К сервису транскрибации — через `http://transcribe-service:8000` (env `TRANSCRIBE_SERVICE_URL`).

## Файлы

| Файл | Назначение |
|---|---|
| `main.py` | Polling-цикл, обработка сообщений, `process_audio()` |
| `bot_api.py` | Обёртка Telegram API: `send_message`, `send_document`, `download_file`, `scrub` |
| `admin_panel.py` | Кнопочная admin-панель (inline keyboards) |
| `state.py` | RBAC + scope-реестр, персистент в JSON |
| `vault.sh` | Зашифрованный secrets vault (AES-256, пароль в macOS Keychain) |
| `setup.sh` | Первоначальная настройка (права файлов, docker network) |

## Что НЕ трогать

- `admin_panel.py` — менять только если задача явно касается admin-панели
- `state.py` — RBAC-логика стабильна, не ломать
- `.env` — не коммитить, права 600
- Топики группы (THREAD_ID=59, ADMIN_THREAD_ID=66) — не менять ID

## Текущий спринт

### P1 — Файловый вывод транскрипции [✅ ГОТОВО — 2026-08-06]

**Сделано:**
- `bot_api.py`: добавлена `send_document()` — отправка файла через multipart/form-data, исправлен `MAX_MESSAGE_LEN`
- `main.py`: `transcribe()` возвращает `(text, segments)`, формат с таймстемпами `[MM:SS]`, файл `transcription_YYYY-MM-DD_HH-MM.txt`
- Fallback: если сегментов нет — отправка plain text как раньше

### P2 — Диаризация (кто говорит) [⏳ В ОЧЕРЕДИ — после P1]

**Задача:** определять спикеров в `transcribe-service`, добавить в сегменты поле `speaker`.

Детали — в `CLAUDE.md` transcribe-service.

**Что делать в боте (после реализации в сервисе):**
- Если в сегментах есть `speaker` — формат файла:
  ```
  [00:00] SPEAKER_00: Привет всем
  [00:05] SPEAKER_01: Привет, как дела?
  ```
- Если нет `speaker` — формат без имён (как в P1)

## Backlog

- Прогресс-бар во время длинной транскрибации (edit_message с обновлением)
- Уведомление когда очередь занята (transcribe_lock захвачен)
