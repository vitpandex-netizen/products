# 📱 Telegram Bot Map — Экосистема

> Единый реестр всех Telegram ботов, топиков и проектов.
> Sync: `~/dev/TELEGRAM_MAP.md`

---

## 1. Боты

| Бот | Токен | Проект | Назначение | Сервер |
|-----|-------|--------|------------|--------|
| **@search_market_uz_bot** | `8686429988:...` | stocks-uz (UZSE) | ❌ **Захвачен** — котировки UZSE | US Server |
| **@famaly_helper_bot** | `8938976950:...` | Transcribe Bot | 🟢 Голос→текст, AI-саммари | US Server |
| **@Expert_consilium_bot** | `8888781924:...` | Expert Consilium | 🟢 AI-консультации | US Server |
| **@anyidea_ai_bot** | `8818072631:...` | AnyIdea | 🟢 Генерация идей | US Server |
| **@finanalytics_ai_bot** | `8636604102:...` | FinAnalytics | 🟢 Финансовая аналитика | US Server |
| **@bitget_bot** | (в .env) | Bitget Bot | 🟢 Трейдинг, алерты | US Server |

## 2. Топики Telegram

| ID | Название | Проект | Бот |
|-----|---------|--------|-----|
| **576** | 📊 UZ Stocks | stocks-uz | @search_market_uz_bot |
| **577** | 📈 US Stocks | Trading Dashboard | @finanalytics_ai_bot |
| **15** | 💼 HH-Jobs | HH Jobs | @famaly_helper_bot |
| **52** | 💼 HH-Remote | HH Remote | @famaly_helper_bot |
| **127** | 💰 Passive Income | — | — |
| **203** | 📋 Мониторинг | Agent Dashboard | — |
| **239** | 📊 FinAnalytics | FinAnalytics | @finanalytics_ai_bot |
| **258** | 🤖 InterP_Ai_Bot | — | — |
| **397** | 📡 DataCore Signals | DataCore | @famaly_helper_bot |
| **7607** | 💡 AnyIdea | AnyIdea | @anyidea_ai_bot |

## 3. Админ-боты (Hermes)

| Бот | Назначение |
|-----|------------|
| **@hermes_bot** | Основной канал связи с агентом |
| (Твой личный) | Команды управления |

## 4. Проблемы

### ❌ @search_market_uz_bot — конфликт
- **Сейчас:** Используется проектом `stocks-uz` (UZSE котировки)
- **Должен:** Быть для UZ Market (поиск товаров на рынке Узбекистана)
- **Решение:** Создать новый бот через @BotFather для stocks-uz, освободить @search_market_uz_bot

### ❌ Bitget Bot — не определён
- Токен есть, но имя бота не установлено

## 5. План исправления

1. Создать в @BotFather **нового бота** для `stocks-uz` (название: UZSE Stocks Bot)
2. Обновить токен в `/home/us/projects/stocks-uz/.env`
3. Перезапустить stocks-uz бота
4. @search_market_uz_bot освободить для UZ Market
5. Обновить PROJECTS.md

---

*Последнее обновление: 2026-08-23*