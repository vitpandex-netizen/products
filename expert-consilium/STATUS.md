## 🎯 Состояние проекта: Expert Consilium (готов к запуску)

### 🟢 Задеплоено и работает
| Компонент | Порт | Статус |
|-----------|:----:|:------:|
| API + Дашборд | `:8007` | ✅ **200 OK** |
| Caddy Gateway | `/consilium/*` → `:8007` | ✅ Проксирует |
| PostgreSQL | `:5444` | ✅ Healthy |
| Redis | `:6444` | ✅ Healthy |
| Docker Compose | 5 контейнеров | ✅ Все образы built |

### 🔴 Ждёт интернет на US Server
| Компонент | Что нужно |
|-----------|-----------|
| **Бот** @Expert_consilium_bot | `docker compose restart consilium-bot` |
| **Worker** (OpenRouter) | `docker compose restart consilium-worker` |

### 📋 Структура проекта
```
~/services/expert-consilium/
├── .env — токены, модели, лимиты
├── docker-compose.yml
├── Dockerfile
├── src/
│   ├── main.py — FastAPI (:8007)
│   ├── bot.py — Telegram polling
│   ├── worker.py — AI parallel queries
│   ├── config.py — pydantic-settings
│   ├── db/ — SQLAlchemy async + asyncpg
│   ├── core/ — OpenRouter, SmartMode, Синтезатор
│   ├── telegram/ — aiogram 3 handlers
│   └── web/ — HTMX дашборд
└── infra/init.sql — схема БД
```

### 🎯 Smart Mode
- **Базовый**: 5 Flash/mini/Haiku ($0.003-0.005/запрос)
- **Премиум**: топ-модели для сложных вопросов (auto-detect)
- **Форсированный**: `/deep` перед вопросом