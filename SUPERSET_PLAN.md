# Apache Superset — BI платформа

## Статус: ✅ ГОТОВО

## Доступ
- **URL:** http://us.tailc8105c.ts.net:8088
- **Логин:** admin / admin
- **Через порт**, не через Caddy (Superset не поддерживает sub-path)

## Что подключено
- ✅ **DataCore PostgreSQL** — trades, daily_pnl, signals, strategy_metrics
- ✅ **MCP (AI tools)** — fastmcp 3.4.7 установлен
  - AI tools: `get_schema`, `health_check` (можно писать SQL на русском)
- ✅ **Port 8088** — открыт для Tailscale
- ✅ **Hub page** — обновлена с ссылкой на Superset

## Что можно создать
- 📊 Trading P&L — дашборд по trades и daily_pnl
- 📈 Signals — аналитика сигналов
- 💼 HH Jobs — импортировать через SQLite dataset
- 💰 FinAnalytics — импортировать через SQLite dataset

## Как создать дашборд
1. Открыть http://us.tailc8105c.ts.net:8088
2. Войти admin/admin
3. Data → Datasets → найти DataCore PostgreSQL
4. Charts → +Chart → выбрать таблицу
5. Настроить визуализацию → Save → Add to Dashboard

## Известные ограничения
- Caddy proxy не работает с /superset (Superset использует абсолютные URL)
- Нужен прямой доступ через порт 8088 (только Tailscale)
- MCP требует дополнительной настройки для production