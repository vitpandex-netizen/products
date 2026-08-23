# SPEC: Консилиум Экспертов (Expert Consilium)

> **Версия:** 1.0.0
> **Статус:** 🟢 Spec утверждён
> **Приоритет:** P1 (инструмент для принятия решений)

---

## 1. Концепция

Telegram бот, который прогоняет вопрос пользователя через **5 ИИ-экспертов** с разными ролями и выдаёт консолидированный ответ.

**Ключевая идея:** не «прогон через 5 моделей», а **коллегия экспертов** — каждая модель получает роль и угол анализа, результат осмысленно синтезируется.

---

## 2. Роли экспертов

| Роль | Модель (базовая) | Модель (премиум) | Что делает |
|------|-----------------|-------------------|------------|
| 🧠 **Стратег** | DeepSeek V4 Flash | DeepSeek V4 | Общая картина, тренды, стратегические выводы |
| 📊 **Аналитик** | Gemini 2.5 Flash | Gemini 2.5 Pro | Данные, цифры, факты, структурированный разбор |
| ⚡ **Критик** | Claude 4 Haiku | Claude Sonnet 4 | Поиск слабых мест, рисков, контраргументов |
| 💡 **Креативщик** | GPT-4o-mini | GPT-4o | Нестандартные углы, скрытые возможности |
| 🎯 **Синтезатор** | Grok 3 mini | Grok 3 | Сборка консенсуса, расхождения, итог |

### Smart Mode

- **Базовый режим (default):** 5 бюджетных моделей (Flash/mini/Haiku)
- **Премиум-режим (auto):** если вопрос сложный (длина >200 символов, содержит ключевые слова: архитектура, стратегия, анализ, код, риск, оптимизация) — подключаются премиум-модели
- **Форсированный премиум:** команда `/deep` или слово «глубоко» в вопросе

---

## 3. Поток работы

```
User → Telegram → Bot (Python) → Core Service
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │ Стратег  │ │Аналитик  │ │ Критик   │
                    │ (DeepSeek)│ │ (Gemini) │ │(Claude)  │
                    └──────────┘ └──────────┘ └──────────┘
                    ┌──────────┐ ┌──────────┐
                    │Креативщик│ │Синтезатор│
                    │ (GPT-4o) │ │ (Grok)   │
                    └──────────┘ └──────────┘
                          │           │
                          └─────┬─────┘
                                ▼
                    ┌──────────────────┐
                    │  Синтезатор      │
                    │  → консенсус     │
                    │  → расхождения   │
                    │  → confidence    │
                    │  → рекомендация  │
                    └──────────────────┘
                                │
                                ▼
                    ┌──────────────────┐
                    │  Telegram ответ  │
                    │  + Web Dashboard │
                    └──────────────────┘
```

### 3.1 Детальный флоу

1. **User** пишет сообщение в Telegram topic 7941
2. **Bot** отвечает: «🔍 Анализирую... Опрошено 0/5 экспертов»
3. **Core Service** получает вопрос, определяет режим (basic/premium)
4. **Core Service** отправляет **параллельные** запросы всем 5 экспертам
5. **Bot** обновляет статус по мере получения ответов: «Опрошено 3/5...»
6. **Синтезатор** получает все 5 ответов → генерирует консолидированный ответ
7. **Bot** отправляет финальный ответ в Telegram
8. **Запись** сохраняется в PostgreSQL + Web Dashboard

---

## 4. Формат ответа

```markdown
🧠 *Консилиум Экспертов*

**Ваш вопрос:** [текст вопроса]

---

### 📋 Консенсус
[Что эксперты сошлись во мнении — 2-3 абзаца]

### ⚡ Расхождения
- **Стратег vs Критик:** [в чём разошлись]
- **Аналитик vs Креативщик:** [в чём разошлись]

### 🎯 Рекомендация
[Итоговая рекомендация на основе консенсуса]

### 📊 Детали экспертов
<details>
<summary>🧠 Стратег</summary>
[краткий тезис эксперта]
</details>
<details>
<summary>📊 Аналитик</summary>
[краткий тезис эксперта]
</details>
<details>
<summary>⚡ Критик</summary>
[краткий тезис эксперта]
</details>
<details>
<summary>💡 Креативщик</summary>
[краткий тезис эксперта]
</details>

---
*Confidence: ⭐⭐⭐⭐☆ (4/5) | Режим: Базовый ⚡*
*Спросить уточнение → просто напиши reply*
```

---

## 5. Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие, описание |
| `/help` | Справка по командам |
| `/deep` | Форсированный премиум-режим для следующего вопроса |
| `/panel` | Состав экспертов и их роли |
| `/history` | Последние 5 запросов (ссылка на дашборд) |
| `/mode` | Текущий режим (basic/premium) |
| `любой вопрос` | Анализ в текущем режиме |

---

## 6. Веб-дашборд

**URL:** `http://100.84.223.96:XYZ/consilium/` (через Caddy gateway :8083)

**Страницы:**
- `/` — Список последних запросов (карточки)
- `/request/{id}` — Детальный просмотр: 5 табов экспертов side-by-side
- `/compare` — Сравнение точности экспертов по категориям
- `/stats` — Статистика: какая модель в чём сильнее, стоимость

**API:**
- `GET /api/v1/requests` — список запросов (пагинация)
- `GET /api/v1/requests/{id}` — детали запроса + ответы экспертов
- `GET /api/v1/stats` — статистика

---

## 7. Стек технологий

| Компонент | Технология |
|-----------|-----------|
| **Язык** | Python 3.12 |
| **Фреймворк** | FastAPI (единый backend для бота и API) |
| **AI Gateway** | OpenRouter (единый API для всех моделей) |
| **База данных** | PostgreSQL 16 |
| **Кэш / очереди** | Redis 7 |
| **Telegram Bot** | python-telegram-bot (или aiogram 3) |
| **Web Dashboard** | FastAPI + HTMX (как DataCore admin) |
| **Деплой** | Docker Compose на US Server |
| **Gateway** | Caddy (:8083/consilium/*) |
| **Мониторинг** | Health Check (:8081) |

---

## 8. Архитектура (контейнеры)

```yaml
services:
  consilium-bot:       # Telegram bot handler (aiogram)
  consilium-api:       # FastAPI core + API
  consilium-web:       # HTMX web dashboard (может быть в api)
  consilium-worker:    # Фоновый воркер для опроса экспертов
  postgres:            # PostgreSQL 16
  redis:               # Redis 7
```

**Коммуникация:**
- Bot → API: HTTP (внутри Docker сети)
- API → Worker: Redis Pub/Sub (очередь задач)
- Worker → AI Models: OpenRouter HTTP API
- Worker → Bot: Redis Pub/Sub (результаты)
- API → PostgreSQL: SQLAlchemy async

---

## 9. Smart Mode — детали

### Определение сложности вопроса
```python
COMPLEXITY_KEYWORDS = [
    "архитектур", "стратеги", "анализ", "оптимизаци",
    "risk", "design pattern", "архитектур", "код",
    "алгоритм", "инфраструктур", "деплой", "security",
    "производительност", "масштабировани", "миграци"
]

def is_complex_query(text: str) -> bool:
    """Определяет, нужен ли премиум-режим"""
    if len(text) > 200:  # Длинный вопрос
        return True
    if any(kw in text.lower() for kw in COMPLEXITY_KEYWORDS):
        return True
    return False
```

### Цены за запрос (ориентировочно)

| Режим | Модели | Стоимость за запрос |
|-------|--------|-------------------:|
| 🟢 Базовый | 5 Flash/mini/Haiku | ~$0.003-0.005 |
| 🟡 Премиум | 5 Pro/Sonnet/Full | ~$0.05-0.10 |
| 🟢 Смешанный | 4 базовых + 1 премиум | ~$0.01-0.02 |

---

## 10. База данных

```sql
-- Запросы
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,        -- Telegram user ID
    username TEXT,
    question TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'basic',  -- basic / premium / forced
    complexity_score FLOAT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending / processing / completed / failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Ответы экспертов
CREATE TABLE expert_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id) ON DELETE CASCADE,
    role TEXT NOT NULL,       -- strategist / analyst / critic / creative / synthesizer
    model TEXT NOT NULL,       -- deepseek-v4-flash / gemini-2.5-flash / ...
    response_text TEXT NOT NULL,
    tokens_in INT,
    tokens_out INT,
    cost DECIMAL(10,6),
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Фидбек пользователя
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id) ON DELETE CASCADE,
    user_id BIGINT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 11. Non-functional requirements

- **Время ответа:** < 30 секунд для базового режима, < 60 сек для премиум
- **Availability:** 24/7 на US Server
- **Cost:** < $5/мес на API (базовый режим), < $20/мес с премиум
- **Reliability:** Retry 3 раза при падении модели, fallback на другую модель
- **Security:** Никакие токены не хранятся в коде, только .env
- **Scalability:** Горизонтальное масштабирование worker'ов через Redis

---

## 12. Этапы реализации

| Этап | Что | Оценка |
|------|-----|--------|
| **P0** | Core Service + базовый Telegram бот + 5 экспертов | 1 день |
| **P1** | Smart Mode + синтезатор + форматирование ответа | 1 день |
| **P2** | Web Dashboard + история запросов | 1 день |
| **P3** | Статистика + сравнение + фидбек | 1 день |
| **P4** | Мониторинг + Health Check + CI | 0.5 дня |

---

## 13. Риски

| Риск | Вероятность | Влияние | Митигация |
|------|:-----------:|:-------:|-----------|
| OpenRouter rate limit | 🟡 Средняя | 🟡 Среднее | Retry + fallback |
| Превышение бюджета | 🟡 Средняя | 🟢 Низкое | Smart mode + лимиты |
| Медленный ответ (30+ сек) | 🟡 Средняя | 🟡 Среднее | Streaming + прогресс |
| Падение одной модели | 🟢 Высокая | 🟢 Низкое | Продолжить без неё |

---

*Spec by Hermes Agent | 2026-08-20*