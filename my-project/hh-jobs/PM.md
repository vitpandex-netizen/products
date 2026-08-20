# Project Charter: HH Jobs
Status: 🟢 Active
Priority: P1 (High — работа)

## Goal
Поиск IT-вакансий в Ташкенте с Telegram-уведомлениями 24/7.

## Stakeholders
- Owner: @vitpandex-netizen
- Tester: @s.zaxidova2022
- Users: Personal

## Resources
- Server: US Server (cron) + Mac (PM2)
- Keywords: 54 ключевых слова
- Skills: 69 навыков
- Dependencies: HeadHunter RSS, Telegram API

## Success Criteria
- [x] RSS search (обходит DDoS-Guard)
- [x] 15+ matches per run
- [x] Telegram notifications
- [ ] 24/7 on US Server
- [ ] 0.30 match threshold

## Backlog

### 📋 To Do
- Migrate to US Server 24/7 — P1
- Improve matcher for RSS-only data — P1
- Add salary highlight (>$4000) — P2

### 🔄 In Progress
- None

### ✅ Done (last 7 days)
- [x] RSS search fixed — 2026-08-12
- [x] 54 keywords, 69 skills — 2026-08-12
- [x] MIN_MATCH_SCORE lowered to 0.30 — 2026-08-12
- [x] Telegram notifications sending — 2026-08-12