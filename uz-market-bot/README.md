# uz-market-bot 🏪🤖

**Telegram-бот для поиска лучших предложений на рынке Узбекистана.**

Помогает находить товары на OLX.uz с интеллектуальным анализом через DeepSeek. Поддерживает диалоговый режим: пользователь описывает, что ищет, бот задаёт уточняющие вопросы, затем парсит площадки и выдаёт рейтинг лучших предложений.

---

## Возможности

- 🔍 **Поиск по OLX.uz** — парсинг через открытое API
- 🧠 **AI-анализ** — DeepSeek (через OpenRouter) анализирует результаты и даёт рекомендации
- 💬 **Диалоговый режим** — уточняющие вопросы перед поиском
- 🏷 **Фильтрация** — по цене, городу, состоянию (новое/б/у)
- 📊 **Ранжирование** — автоматическая сортировка по цене + бонусы за фото и город
- 👥 **Групповой режим** — работает в топике Telegram-группы (по упоминанию бота)
- 🔒 **Безопасное хранение секретов** — через vault.py (AES-256, пароль в macOS Keychain)

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.12 / 3.14 |
| Telegram | python-telegram-bot 22.x |
| LLM | DeepSeek V4 Flash через OpenRouter |
| Парсинг | OLX.uz API (REST, httpx) |
| Запуск | Docker Compose / pm2 |
| Секреты | vault.py (AES-256) |

---

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить конфиг
cp config/config.json.example config/config.json
# Заполнить telegram_token и openrouter_key

# 3. Запустить
python run.py

# Или через Docker:
docker-compose up -d --build
```

---

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Начать диалог / сбросить сессию |
| `/help` | Показать справку |
| `/cancel` | Отменить текущий поиск |

В **личных сообщениях**: любой текст без команды сразу запускает поиск.

В **групповом топике**: сообщение в нужном топике или с упоминанием бота запускает поиск.

---

## Архитектура

```
Пользователь (Telegram)
    │ /start или текст
    ▼
┌────────────────────────────────────────────┐
│ MarketBot                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ OLXParser │  │ LLMClient│  │Aggregator│  │
│  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────────────────────────────┘
    │
    ├── OLX.uz API ──► Результаты поиска
    └── OpenRouter ──► DeepSeek-анализ
```

### Компоненты

- **`OLXParser`** — парсинг OLX.uz через API /v1/offers
- **`LLMClient`** — клиент OpenRouter для DeepSeek (генерация вопросов + анализ результатов)
- **`Aggregator`** — объединение, фильтрация, ранжирование и форматирование
- **`MarketBot`** — основной класс бота с ConversationHandler

---

## Файлы проекта

| Файл | Назначение |
|------|-----------|
| `run.py` | Entrypoint, чтение секретов из vault, запуск бота |
| `src/bot/market_bot.py` | Основной класс бота + ConversationHandler |
| `src/parsers/olx_uz.py` | Парсер OLX.uz через REST API |
| `src/utils/llm_client.py` | Клиент OpenRouter / DeepSeek |
| `src/utils/aggregator.py` | Агрегатор + ранжирование + форматирование |
| `config/config.json` | Конфигурация (токены, ID) |
| `Dockerfile` | Контейнер на python:3.12-slim |
| `docker-compose.yml` | Docker Compose сервис |

---

## Конфигурация

### config/config.json

```json
{
    "telegram_token": "ваш_токен",
    "openrouter_key": "ваш_ключ"
}
```

### Источники секретов (в порядке приоритета)
1. `vault.py` — `~/.secure/vault.py` (AES-256, ключ в macOS Keychain)
2. Переменные окружения: `UZ_MARKET_TELEGRAM_TOKEN`, `OPENROUTER_API_KEY`
3. `config/config.json`

---

## Статус

Проект в активной разработке. См. [ROADMAP.md](./ROADMAP.md) и [CHANGELOG.md](./CHANGELOG.md).