# AGENTS.md — Trading Monitor (Monetization Track)

> **Проект:** Trading Monitor — единый дашборд для биржевых позиций
> **Цель:** Полная монетизация → пассивный доход
> **Статус:** 🟡 Активная разработка
> **Ветка:** `trading-monitor` (https://github.com/vitpandex-netizen/products)

---

## 🔷 Текущее состояние

### Работает
- ✅ Bitget баланс: $88.27 (1 позиция ETH/USDT)
- ✅ Hyperliquid цены: 947 инструментов
- ✅ P&L история: 24 точки (7 дней)
- ✅ Health Check: 9/9 сервисов
- ✅ Agent Dashboard: модель, провайдер, uptime
- ✅ Data Bus: Mac ↔ US Server через Tailscale

### Не работает / нужно доделать
- ❌ Hyperliquid wallet: пустой адрес (нужно создать кошелёк)
- ❌ Landing page: нет
- ❌ Telegram алерты: не настроены на сделки
- ❌ Демо-доступ для клиентов: нет
- ❌ Платёжная система: нет

---

## 💰 Стратегия монетизации

### Продукт
**Trading Monitor** — единый дашборд для крипто-трейдера:
- Bitget + Hyperliquid (и другие биржи в будущем)
- Telegram алерты при сделках
- P&L график, ROI, drawdown
- Ежедневные отчёты

### Цены
| План | Цена | Что входит |
|------|------|-----------|
| 🚀 Starter | $49/мес | 1 портфель, Telegram алерты, P&L |
| 👥 Pro | $149/мес | 5 портфелей, алерты, отчёты, приоритет |
| 🏢 Enterprise | $499/мес | Безлимит, API, свой сервер |

### Каналы продаж
1. Прямые продажи через Telegram
2. ProductHunt / местные IT-сообщества
3. Партнёрства с трейдерами

---

## 🚀 Ближайшие шаги

### День 1 (сегодня) ✅
- [x] Landing page Transcribe Bot
- [x] Правила проекта (AGENTS.md)
- [x] PRODUCTS.md структура
- [x] Git ветки

### День 2 (завтра)
- [ ] Landing page Trading Monitor
- [ ] Деплой на US Server
- [ ] Добавить демо-доступ

### День 3-4
- [ ] Telegram алерты по сделкам
- [ ] P&L за неделю/месяц
- [ ] Платёжная система (Stripe / Telegram Stars)

### День 5-7
- [ ] Запуск на ProductHunt
- [ ] Посты в Telegram каналах
- [ ] Первые клиенты

---

## 🔧 Технический стек

### Фронтенд
- HTML5 + CSS (dark theme) — без фреймворков
- Chart.js для графиков
- Деплой через Caddy reverse proxy

### Бэкенд
- Python 3.12 + FastAPI / HTTP server
- Bitget API (ccxt)
- Hyperliquid API (public + private)
- PostgreSQL (Datacore) для истории

### Инфраструктура
- US Server: 24/7, systemd, Docker
- Mac: разработка, RAG, ChromaDB
- Tailscale: связь между серверами
- Caddy: reverse proxy, HTTPS

---

## ⚠️ Важные правила

1. **Никаких API ключей в коде** — только через .env / vault
2. **Всегда деплоить через git** — ветки, PR, merge
3. **Health Check обязателен** — каждый сервис проверяется
4. **Логирование** — все ошибки в Telegram (topic 203)
5. **Backup** — еженедельный backup БД на Mac