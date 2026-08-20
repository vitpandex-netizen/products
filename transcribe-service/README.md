# transcribe-service 🎙🔊

**FastAPI-сервис транскрибации аудио на базе faster-whisper (CPU, int8).**

Принимает аудиофайл через HTTP, конвертирует в WAV 16kHz моно через ffmpeg, транскрибирует моделью Whisper и возвращает текст с временными сегментами.

Сервис используется `transcribe-bot` как бэкенд, но может работать и как самостоятельный API.

---

## API

### `POST /transcribe`

Принимает аудиофайл (multipart/form-data, поле `file`).

**Ответ:**
```json
{
  "text": "полный текст транскрипции",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": " Привет всем"},
    {"start": 5.2, "end": 8.1, "text": " как дела"}
  ]
}
```

**Ограничения:**
- Очередь: один запрос за раз (asyncio.Lock)
- Таймаут: 60 минут на транскрибацию
- Язык: русский (hardcode, `language="ru"`)

### `GET /health`

Возвращает `{"status": "ok"}`. Используется для healthcheck в Docker.

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.12 |
| Фреймворк | FastAPI + uvicorn |
| Модель | faster-whisper (medium, int8, CPU) |
| Конвертация | ffmpeg |
| Контейнер | Docker (python:3.12-slim) |

---

## Быстрый старт

```bash
# 1. Создать общую сеть
docker network create transcribe-net 2>/dev/null || true

# 2. Запустить
docker-compose up -d --build

# 3. Проверить
curl http://localhost:8000/health
# → {"status":"ok"}
```

### Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|:-----------:|----------|
| `WHISPER_MODEL_SIZE` | `medium` | Размер модели (tiny/base/small/medium/large) |
| `WHISPER_COMPUTE_TYPE` | `int8` | Тип вычислений (int8_float16, int8, float32) |

---

## Файлы проекта

| Файл | Назначение |
|------|-----------|
| `main.py` | FastAPI-приложение: /transcribe, /health |
| `Dockerfile` | python:3.12-slim + ffmpeg + faster-whisper |
| `docker-compose.yml` | Сервис + сеть + кеш модели |
| `requirements.txt` | Зависимости |

---

## Архитектура

```
POST /transcribe (file)
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Сохранить файл на диск (чанки 1МБ)│
│ 2. ffmpeg -i input → 16kHz mono WAV │
│ 3. faster-whisper.transcribe(wav)   │
│ 4. Вернуть {text, segments}         │
└─────────────────────────────────────┘
```

Модель кешируется в `/root/.cache/huggingface` (persistent volume).

---

## Статус

Проект стабилен, в активной разработке. См. [ROADMAP.md](./ROADMAP.md) и [CHANGELOG.md](./CHANGELOG.md).