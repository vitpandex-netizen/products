# Project Charter: FinAnalytics
Status: 🟡 In Progress
Priority: P0 (Critical — финансовое ядро)

## Goal
Центральная система управления личными финансами и инвестициями. Без неё невозможны все остальные проекты — трейдинг, инвестиции, работа.

## Философия
FinAnalytics — это не просто «долги и бюджет». Это **финансовое ядро**, которое даёт контекст всем остальным проектам:
- bitget-bot → знает, сколько я могу рисковать
- stocks-uz/us → знают, куда инвестировать
- passive-income → знает, сколько свободных средств
- hh-jobs → знает, какая ЗП нужна для покрытия обязательств

## Stakeholders
- Owner: @vitpandex-netizen
- Users: Personal

## Resources
- Server: Mac (PM2) + US Server (резерв)
- Stack: Python + SQLite + Telegram Bot
- Dependencies: Telegram API, vault secrets

## Success Criteria
- [ ] Telegram bot active (polling)
- [ ] Credit import done
- [ ] Payment calendar configured
- [ ] Monthly budget reports to Telegram

## Backlog

### 📋 To Do
- Launch Telegram bot — P0
- Import credit data — P1
- Configure payment calendar — P1
- Add expense categories — P2
- Monthly budget reports — P2

### 🔄 In Progress
- None

### ✅ Done (last 7 days)
- [x] README.md created — 2026-07-26
- [x] venv created, dependencies installed — 2026-08-12
- [x] dotenv installed — 2026-08-12

## Week of 2026-08-12

### Done
- venv + dependencies installed ✅

### Blockers
- 🚫 None

### Next
- Launch Telegram bot
- Import credits
- Configure payment calendar