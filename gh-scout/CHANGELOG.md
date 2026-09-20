# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-09-20

### Added
- **Enterprise Agentic Protocol** — Spec-First TDD workflow
  - Technical contract `SPEC.md` with monitoring targets
  - Multi-source GitHub data collection (P0/P1/P2 priority)
  - Recommendation engine with trend detection
  - Automated digest via Telegram
- **Auto-Improver** — Small tasks auto-implemented, large tasks reviewed
- **Change Log Integration** — All deployments audited

### Changed
- Collector optimization: parallel repos, deduplication
- Recommendation scoring: star growth rate + activity score
- Notification timing: daily digest 11:00 UTC+5

### Security
- GitHub API rate limit handling (429 backoff)
- No secret exposure in logs
- Audit trail via Change Log (:8310)

---

## [1.0.0] - 2026-09-05

### Initial Release
- GitHub repository monitoring
- Trending projects tracking
- Basic recommendation engine
- Telegram notifications
