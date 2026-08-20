# Changelog — transcribe-service

Все заметные изменения проекта фиксируются в этом файле.

---

## [1.0.0] — 2026-07-??

### Добавлено
- Первый релиз FastAPI-сервиса транскрибации
- Endpoint `POST /transcribe` — приём файла, конвертация, транскрибация
- Endpoint `GET /health` — проверка доступности
- ffmpeg-конвертация в WAV 16kHz моно
- faster-whisper модель medium (int8, CPU)
- asyncio.Lock для последовательной обработки (один запрос за раз)
- Dockerfile на python:3.12-slim + ffmpeg
- Docker Compose с persistent volume для кеша HuggingFace
- Healthcheck в Dockerfile (30s interval)

### Инфраструктура
- Общая сеть `transcribe-net` с transcribe-bot
- Порт 8000 (localhost-only снаружи, transcribe-service внутри сети)
- Кеш модели: `/Volumes/External/docker-volumes/transcribe-service/hf-cache`

---

## [0.2.0] — 2026-07-??

### Добавлено
- Чанковая запись файла на диск (1 МБ буфер) — избегает загрузки всего файла в RAM
- Улучшенное логирование: размер файла, статус конвертации, количество сегментов

---

## [0.1.0] — 2026-07-??

### Добавлено
- Прототип сервиса с базовой транскрибацией
- Прямая интеграция с Telegram Bot API (ранняя версия)