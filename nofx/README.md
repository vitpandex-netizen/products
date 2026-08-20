# NOFX — AI-Powered Trading System

> **Альтернативная сборка NOFX — AI-трейдинг с открытым API**

NOFX — это AI-управляемая торговая система, развёртываемая через Docker. Проект предоставляет готовую инфраструктуру для запуска AI-трейдеров с веб-интерфейсом, REST API и интеграцией с CoinAnk для получения рыночных данных.

## Стек

| Компонент | Технология |
|-----------|-----------|
| Backend | Go (GORM, SQLite) |
| Frontend | Предустановленный web-интерфейс |
| База данных | SQLite (через GORM) |
| Контейнеризация | Docker / Docker Compose |
| Рыночные данные | CoinAnk API (WebSocket) |
| Шифрование | Встроенный encryption service |

## Установка

### Быстрый старт (одной командой)

```bash
curl -fsSL https://raw.githubusercontent.com/NoFxAiOS/nofx/main/install.sh | bash
```

### Ручная установка

```bash
# 1. Скачать конфигурацию
curl -O https://raw.githubusercontent.com/NoFxAiOS/nofx/main/docker-compose.prod.yml

# 2. Создать .env файл
cp .env.example .env
# Отредактировать .env: установить API ключи

# 3. Запустить
docker compose -f docker-compose.prod.yml up -d
```

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Health check |
| GET | `/api/traders` | Публичный лидерборд AI-трейдеров (top 50) |
| GET | `/api/competition` | Данные соревнования |
| GET | `/api/top-traders` | Top-5 трейдеров |
| GET | `/api/equity-history?trader_id=xxx` | История доходности |
| POST | `/api/traders` | Создать AI-трейдера |
| DELETE | `/api/traders/:id` | Удалить AI-трейдера |
| POST | `/api/traders/:id/start` | Запустить трейдера |
| POST | `/api/traders/:id/stop` | Остановить трейдера |
| GET | `/api/models` | Конфигурация AI-моделей |
| PUT | `/api/models` | Обновить конфигурацию моделей |
| GET | `/api/exchanges` | Конфигурация бирж |
| GET | `/api/account?trader_id=xxx` | Информация о счёте |
| GET | `/api/positions?trader_id=xxx` | Список позиций |
| GET | `/api/decisions?trader_id=xxx` | Лог решений трейдера |

## Конфигурация

Основные переменные окружения (`.env`):

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `NOFX_BACKEND_PORT` | Порт backend | `8080` |
| `NOFX_FRONTEND_PORT` | Порт frontend | `3000` |
| `TZ` | Часовой пояс | `Asia/Shanghai` |
| `AI_MAX_TOKENS` | Максимум токенов AI | `8000` |
| `CORS_ALLOWED_ORIGINS` | Разрешённые CORS-источники | (только localhost) |

## Структура проекта

```
nofx/
├── docker-compose.yml     # Docker Compose конфигурация
├── data/                  # Данные (БД, логи)
│   ├── nofxd.db          # SQLite база данных
│   └── nofx_*.log        # Логи работы системы
├── .env                   # Переменные окружения
├── README.md              # ← текущий файл
├── ROADMAP.md             # План развития
├── CHANGELOG.md           # История изменений
└── STATUS.md              # Текущее состояние проекта
```

## Требования

- Docker 24+
- Docker Compose v2+
- Доступ к ghcr.io (GitHub Container Registry)