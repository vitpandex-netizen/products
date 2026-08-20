# transcribe-service — Context for Claude Code / Hermes

## Что это

FastAPI-сервис транскрибации аудио на базе `faster-whisper` (CPU, int8).
Принимает аудиофайл, конвертирует через ffmpeg в WAV 16kHz моно, транскрибирует, возвращает текст и сегменты.

## Инфраструктура

- Docker-контейнер, команда `docker-compose` (не `docker compose`)
- Сеть: `transcribe-net` (shared с transcribe-bot)
- Порт: `127.0.0.1:8000` (наружу только localhost, внутри сети — по имени `transcribe-service`)
- Модель кешируется в: `/Volumes/External/docker-volumes/transcribe-service/hf-cache`
- Git: `github.com/vitpandex-netizen/transcribe-service`, ветка `main`
- После изменений: `docker-compose up -d --build` + коммит + пуш

## API

### `POST /transcribe`

Принимает: `multipart/form-data`, поле `file`.

Возвращает:
```json
{
  "text": "полный текст транскрипции",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": " Привет всем"},
    {"start": 5.2, "end": 8.1, "text": " как дела"}
  ]
}
```

### `GET /health`

Возвращает `{"status": "ok"}`.

## Файлы

| Файл | Назначение |
|---|---|
| `main.py` | FastAPI-приложение, эндпоинты `/transcribe` и `/health` |
| `Dockerfile` | python:3.12-slim + ffmpeg |
| `docker-compose.yml` | Сервис + сеть + кеш модели |
| `requirements.txt` | `faster-whisper`, `fastapi`, `uvicorn` |

## Конфиг (env vars)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `WHISPER_MODEL_SIZE` | `medium` | Размер модели (tiny/base/small/medium/large) |
| `WHISPER_COMPUTE_TYPE` | `int8` | Тип вычислений |

## Текущий спринт

### P1 — Диаризация (кто говорит) [⏳ В ОЧЕРЕДИ]

**Задача:** добавить определение спикеров в сегменты транскрипции.

**Что делать:**
1. Исследовать варианты CPU-диаризации без GPU:
   - `pyannote.audio` (требует HuggingFace токен, тяжёлая модель)
   - `whisperx` (альтернатива, может работать на CPU)
   - `simple-diarizer` (лёгкая, без GPU)
2. Выбрать вариант который работает в CPU Docker-контейнере
3. Добавить в `main.py` опциональную диаризацию (env `DIARIZE=1`, по умолчанию выключена)
4. Если `DIARIZE=1` — добавить `speaker` в каждый сегмент:
   ```json
   {"start": 0.0, "end": 5.2, "text": " Привет", "speaker": "SPEAKER_00"}
   ```
5. Если диаризация отключена или не удалась — `"speaker": null`
6. Добавить `HUGGING_FACE_TOKEN` в `.env.example` если нужен для модели

**Ограничения:**
- CPU only (нет GPU в Docker на этом Mac)
- Контейнер должен оставаться на базе `python:3.12-slim`
- Не ломать существующий API (speaker — дополнительное поле, не обязательное)

## Backlog

- Язык транскрибации через параметр запроса (сейчас hardcode `ru`)
- Очередь заданий с прогресс-уведомлениями (сейчас asyncio.Lock)
- Метрики: время транскрибации, длина файла, количество сегментов
