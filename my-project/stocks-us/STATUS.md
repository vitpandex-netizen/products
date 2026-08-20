**Last Updated:** 2026-08-06 (Claude — проверено живым прогоном)
**Status:** ✅ Синтаксис OK, Yahoo Finance работает, Telegram thread не настроен

| Фаза | Задача | Статус |
|------|--------|--------|
| 0 | Источник данных | ✅ Yahoo Finance (yfinance) — без API ключа |
| 1 | src/tickers.py | ✅ 56 тикеров (акции + ETF + металлы) |
| 2 | src/db.py | ✅ SQLite price_history |
| 3 | src/yf_client.py | ✅ fetch_quotes() работает |
| 4 | src/main.py | ✅ Синтаксис OK |
| 5 | Telegram тема | ⏸️ Нужно создать тему и вписать ID в .env |
| 6 | Launchd расписание | ⏸️ Не начато |

## Проверено живыми запросами (2026-08-06):

```
AAPL  $309.73  -0.26%
NVDA  $222.01  +2.55%
SPY   $771.84  -0.10%
```

## Источник данных

Yahoo Finance через `yfinance` — бесплатно, без API ключа, батч-запрос на все 56 тикеров.

Тикеры TG Wallet имеют суффикс `x` (INTCx, GOOGLx) — это токенизированные акции.
Мониторим через стандартные Yahoo Finance символы (без `x`).

## Пропущены намеренно

- SpaceX (SPCXx) — не торгуется публично
- Bending Spoons (BSPx) — не на NYSE
- SK Hynix (SKHYx) — корейская биржа (000660.KS)
- SanDisk (SNDKx) — делистинг
- DFDVx, AMBRx, TONx — неизвестны или крипто

## NYSE часы работы (UTC)

14:30–21:00 UTC пн-пт. Мониторинг: 14:00–22:00 UTC (TRADE_START_UTC/TRADE_END_UTC в .env).

## Дальше

1. Создать тему stocks-us в Telegram-группе → вписать TELEGRAM_THREAD_ID в .env
2. Запустить `TRADE_HOURS_ONLY=false venv/bin/python3 src/main.py` для полного теста
3. Создать launchd plist (аналогично stocks-uz)
