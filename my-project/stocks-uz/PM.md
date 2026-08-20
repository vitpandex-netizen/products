# Project Charter: Stocks-UZ
Status: 🟡 In Progress
Priority: P2 (Medium — инвестиции)

## Goal
Мониторинг акций UZSE (Республиканская фондовая биржа «Тошкент»). Сбор данных, анализ, уведомления.

## Stakeholders
- Owner: @vitpandex-netizen
- Users: Personal

## Resources
- Server: Mac (cron)
- Stack: Python + SQLite + Telegram
- Tickers: 56 (старт с HMKB)
- Dependencies: UZSE API/website

## Success Criteria
- [ ] Real-time price for HMKB
- [ ] Price history in SQLite
- [ ] Telegram notifications on price changes
- [ ] Top 10 tickers monitored

## Backlog

### 📋 To Do
- Find working UZSE data source — P0
- Implement uzse_client.py — P1
- SQLite price_history table — P1
- Telegram notifications — P1
- Expand to 10 tickers — P2

### 🔄 In Progress
- None

### ✅ Done (last 7 days)
- [x] HERMES_TASK.md created — 2026-08-12
- [x] .env created — 2026-08-12

## Week of 2026-08-12

### Done
- Task doc created ✅

### Blockers
- 🚫 UZSE website blocks non-browser clients

### Next
- Find alternative data source
- Implement price collector