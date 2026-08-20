# Project Charter: Meeting Pipeline
Status: 🟢 Active
Priority: P3 (Low — пассив)

## Goal
Автоматическая транскрипция встреч → саммари → Notion.

## Stakeholders
- Owner: @vitpandex-netizen
- Users: Personal

## Resources
- Server: Mac (PM2, watch service)
- Stack: Whisper + DeepSeek + Notion API
- Port: 8001
- Dependencies: faster-whisper, recordings/ directory

## Success Criteria
- [x] HTTP service running on 8001
- [x] Watch service monitoring /recordings/
- [x] Transcription via Whisper
- [x] Summary via DeepSeek
- [x] Notion integration

## Backlog

### 📋 To Do
- Replace OI binary with direct Whisper — P1
- Add auto-upload from cloud storage — P2
- Add meeting calendar integration — P3

### 🔄 In Progress
- None

### ✅ Done (last 7 days)
- [x] v0.2.0 — watch service, auto_upload, flush_notion — 2026-08-12
- [x] PM2 service running — 2026-08-12

## Week of 2026-08-12

### Done
- v0.2.0 released ✅

### Blockers
- 🚫 None

### Next
- Replace OI binary