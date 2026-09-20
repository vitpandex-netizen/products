# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-09-20

### Added
- **Enterprise Agentic Protocol** — Spec-First TDD workflow
  - Technical contract `SPEC.md` with data sources, API endpoints, risk constraints
  - Integration with DataCore (PostgreSQL, Redis, Message Bus)
  - Telegram Mini App (`/tma/`) for market monitoring
  - OHLCV caching, insights scanner, key figures tracker, trade flow analysis

### Changed
- Updated cron schedules: collection every hour, reports at 18:00
- Enhanced rate limit handling (429 backoff with exponential retry)

### Security
- Private by default (Tailscale only, no public ports)
- Whitelist Telegram users (`ALLOWED_TELEGRAM_USER_IDS`)
- Audit trail via Change Log

---

## [1.0.0] - 2026-09-10

### Initial Release
- UZSE stock market monitoring
- Telegram channel aggregation (13 channels)
- Basic portfolio tracking
- Price alerts (>10% moves)

[Unreleased]
[1.1.0]: https://github.com/vitpandex-netizen/stocks-uz/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/vitpandex-netizen/stocks-uz/releases/tag/v1.0.0
