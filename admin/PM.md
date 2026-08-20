# Project Charter: Admin Panel
Status: 🟡 In Progress
Priority: P3 (Low — сервисный инструмент)

## Goal
Единая точка управления всеми сервисами и проектами.

## Stakeholders
- Owner: @vitpandex-netizen
- Tester: @s.zaxidova2022
- Users: Personal + Tester

## Resources
- Server: Mac (PM2) + US Server (Caddy proxy)
- Stack: Flask + SQLite + pyotp
- Port: 3030
- Dependencies: PM2, US Server Caddy

## Success Criteria
- [x] Login with password
- [x] 2FA support (TOTP)
- [x] Service management (start/stop)
- [x] Audit log
- [ ] Settings page (working)
- [ ] Full admin features

## Backlog

### 📋 To Do
- Fix settings page functionality — P1
- Add service management (start/stop PM2) — P1
- Add project status dashboard — P2
- Add user management — P2

### 🔄 In Progress
- Fix redirect loop (Caddy config) — P0

### ✅ Done (last 7 days)
- [x] Created v1 dashboard — 2026-08-12
- [x] Created v2 with Flask + auth + 2FA — 2026-08-12
- [x] Integrated with Caddy proxy — 2026-08-12