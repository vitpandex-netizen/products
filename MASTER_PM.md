# Hermes Master PM Dashboard
Updated: 2026-08-13

## Priority Matrix

| P | Проект | Статус | Категория | Следующий шаг |
|---|--------|--------|-----------|---------------|
| P0 | **bitget-bot** | 🟢 Active | 💰 Деньги | Добавить SOL пару, TP/SL |
| P1 | **my-project** | 🟡 WIP | 💼 Работа | HH на US, FinAnalytics |
| P1 | **admin** | 🟡 WIP | 🔧 Инфра | Настройки, сервисы |
| P1 | **it-ops** | 🟢 Active | 🔧 Инфра | Deploy на US Server |
| P2 | **uz-market** | 🟡 WIP | 💼 Работа | Мониторинг UZSE |
| P2 | **hermes-webui** | 🟢 Active | 🔧 Инфра | Поддержка |
| P2 | **meeting** | 🟢 Active | 🔧 Инфра | Поддержка |
| P2 | **datacore** | 🟢 Active | 🔧 Инфра | Мониторинг |
| P3 | **остальные** | 💤 Sleep | 🔧 Инфра | По необходимости |

## Фокус недели (13-19 Aug)

### 🔴 Критично (P0)
1. Bitget: достичь $100 баланса
2. Bitget: добавить SOL/USDT как вторую пару
3. Bitget: настроить Telegram алерты о сделках

### 🟡 Важно (P1)
4. HH Jobs: перенести на US Server для 24/7
5. Admin: починить страницу настроек
6. FinAnalytics: запустить Telegram бота

### 🟢 Планово (P2)
7. UZ Markets: интеграция jett.uz / goinvest.uz
8. IT Ops: deploy.sh на US Server
9. Dashboard: добавить графики P&L

## Текущие блокеры
- 🚫 Telegram gateway: conflict, нужно `hermes gateway restart`
- 🚫 US Server: HH Jobs без Telegram токена
- 🚫 Admin panel: settings page нерабочая

## Метрики
- US Server: 1 day uptime, 5.4GB RAM free, 122GB disk free
- Bitget: $90.82 balance, 0.01 ETH @ $1858.93
- Docker: 14 containers healthy
- PM2: 5 services online