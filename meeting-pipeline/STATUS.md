# Meeting Pipeline — Статус проекта

> Статус: **Активная разработка** (Pre-production)
> Текущая версия: 0.2.0

---

## Общее состояние

| Параметр | Значение |
|---|---|
| **Версия** | v0.2.0 |
| **Лицензия** | MIT |
| **Репозиторий** | `/Users/vitaliyr/dev/meeting-pipeline` |
| **Основная ветка** | `main` |
| **Язык реализации** | Python 3.14 |
| **Платформа** | macOS (launchd), Linux (Docker) |
| **Production** | ❌ Нет (pre-production) |

---

## Статус компонентов

| Компонент | Статус | Production-ready | Тесты |
|---|---|---|---|
| **meeting_service.py** | ✅ Релиз | Нет | Нет |
| **watch_service.py** | ✅ Релиз | Нет | Нет |
| **auto_upload.py** | ✅ Релиз | Нет | Нет |
| **flush_notion.py** | ✅ Релиз | Нет | Нет |
| **Docker** | ✅ Релиз | Да | Нет |
| **PM2** | ✅ Релиз | Да | Нет |

---

## Известные проблемы

### Высокий приоритет
- **Нет тестов** — ни одного теста ни в одном компоненте
- **Обработка ошибок** — при недоступности OpenRouter или Whisper нет graceful degradation
- **Логирование** — базовое, нет структурированных логов
- **Нет CI/CD** — нет автоматических проверок

### Средний приоритет
- **Whisper model** — используется `small`, для production нужно `large-v3`
- **Транскрипты >15000 символов** — обрезаются, теряется информация
- **Нет rate limiting** — сервис не защищён от перегрузки
- **API-ключ** — через vault.py, но нет ротации ключей

### Низкий приоритет
- **Нет авторизации** — endpoint открыт для всех
- **Нет конфигурации** — настройки жёстко зашиты в коде
- **Нет мониторинга** — нет метрик и алертов
- **Notion queue** — файловая очередь, нет гарантии доставки

---

## Метрики

| Метрика | Значение |
|---|---|
| **Python-модулей** | 4 (meeting_service, watch_service, auto_upload, flush_notion) |
| **Тестов** | 0 |
| **Docker образов** | 1 |
| **PM2 процессов** | 2 (meeting-pipeline, meeting-watch) |
| **Поддерживаемых форматов аудио** | 12 (mp3, wav, m4a, ogg, flac, aac, webm, mp4, m4v, mov, avi, mkv) |
| **AI-моделей** | 1 (DeepSeek v4 Flash) |
| **Моделей Whisper** | 1 (small) |
| **Каналов вывода** | 1 (Notion) |

---

## Зависимости

| Зависимость | Тип | Статус |
|---|---|---|
| Python 3.14 | Runtime | ✅ |
| Whisper (builtin-transcribe) | Runtime | ✅ |
| OpenRouter API | External | ✅ |
| Notion (Interpreter MCP) | Runtime | ✅ |
| ffmpeg | System | ✅ |
| Docker | Optional | ✅ |
| PM2 | Optional | ✅ |
| rclone | Optional | ✅ |

---

## Ближайшие задачи

1. **Тесты** — pytest для всех модулей
2. **CI/CD** — GitHub Actions (lint + test + build)
3. **Обработка ошибок** — retry, graceful degradation, alerting
4. **Конфигурация** — вынести настройки в YAML/окружение
5. **Whisper large-v3** — поддержка выбора модели