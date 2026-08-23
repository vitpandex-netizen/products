# Архитектура: Консилиум Экспертов

> **Базовый документ для разработки.**
> Все изменения — через Spec, не напрямую.

---

## Общая схема

```
┌─────────────────────────────────────────────────────┐
│                     Telegram                         │
│              @Expert_consilium_bot                   │
└──────────────────────┬──────────────────────────────┘
                       │ webhook / polling
                       ▼
┌─────────────────────────────────────────────────────┐
│                  Caddy Gateway (:8083)               │
│  /consilium/* ──────────────────► consilium-api     │
│  /consilium/api/* ──► consilium-api (:8007)         │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              consilium-api (FastAPI :8007)           │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Telegram    │  │ REST API     │  │ Web        │ │
│  │ Webhook     │  │ (дашборд)    │  │ Dashboard  │ │
│  └──────┬──────┘  └──────┬───────┘  │ (HTMX)    │ │
│         │                │          └────────────┘ │
│         └────────────────┼─────────────────────────┘ │
│                          │                           │
│              ┌───────────▼───────────┐               │
│              │   Task Producer       │               │
│              │   (Redis Stream)      │               │
│              └───────────────────────┘               │
└──────────────────────┬───────────────────────────────┘
                       │ Redis Stream
                       ▼
┌────────────────────────────────────────────────────┐
│              consilium-worker                      │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Стратег  │ │Аналитик  │ │ Критик   │            │
│  │ DeepSeek │ │ Gemini   │ │ Claude   │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│  ┌──────────┐ ┌──────────┐                         │
│  │Креативщик│ │Синтезатор│                         │
│  │ GPT-4o   │ │ Grok     │                         │
│  └──────────┘ └──────────┘                         │
│          │         │                                │
│          └────┬────┘                                │
│               ▼                                     │
│       ┌──────────────┐                              │
│       │  Результат   │──► Redis Stream (результаты) │
│       └──────────────┘                              │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────┐
│                   PostgreSQL 16                     │
│  requests | expert_responses | feedback             │
└─────────────────────────────────────────────────────┘
```

---

## Коммуникация между сервисами

### 1. Telegram → Bot → API
- **Webhook:** Telegram шлёт updates на `https://us.tailc8105c.ts.net/consilium/webhook`
- **Long polling:** fallback если webhook не настроен (dev режим)

### 2. API → Worker (запрос на анализ)
- Канал: `consilium:tasks` (Redis Stream)
- Формат:
```json
{
  "request_id": "uuid",
  "question": "текст вопроса",
  "mode": "basic|premium|forced",
  "user_id": 12345,
  "created_at": "2026-08-20T10:00:00Z"
}
```

### 3. Worker → API (результаты экспертов)
- Канал: `consilium:results:{request_id}` (Redis Pub/Sub)
- Каждый эксперт шлёт свой результат по мере готовности
- Синтезатор шлёт финальный результат

### 4. API → Bot (обновление статуса + финальный ответ)
- In-process вызов (API и Bot в одном процессе или HTTP)

---

## OpenRouter конфигурация

```yaml
models:
  strategist:
    basic: "deepseek/deepseek-v4-flash"     # $0.35/$0.40
    premium: "deepseek/deepseek-v4"          # ~$3/$10
  analyst:
    basic: "google/gemini-2.5-flash"         # $0.15/$0.60
    premium: "google/gemini-2.5-pro"          # $1.25/$10
  critic:
    basic: "anthropic/claude-4-haiku"        # $0.25/$1.25
    premium: "anthropic/claude-sonnet-4"      # $3/$15
  creative:
    basic: "openai/gpt-4o-mini"              # $0.15/$0.60
    premium: "openai/gpt-4o"                  # $2.5/$10
  synthesizer:
    basic: "grok/grok-3-mini"                # $0.30/$0.80
    premium: "grok/grok-3"                    # ~$3/$15
```

---

## Безопасность

- **Токены:** только в `.env` (никогда в коде)
- **OpenRouter API key:** хранится в 1Password / .env.prod
- **Telegram webhook:** только HTTPS через Caddy
- **CORS:** дашборд только через Caddy, прямой доступ запрещён
- **Rate limiting:** 10 запросов/мин на пользователя
- **Cost limiting:** максимальная дневная стоимость запросов

---

## Разработка

```bash
# Локально (на Mac)
cd ~/dev/expert-consilium
cp .env.example .env
# заполнить токены
docker compose up -d

# На US Server
rsync -avz --exclude .git --exclude .env ~/dev/expert-consilium/ us@100.84.223.96:~/services/expert-consilium/
ssh us@100.84.223.96
cd ~/services/expert-consilium
cp .env.prod .env
docker compose up -d
```