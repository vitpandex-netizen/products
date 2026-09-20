# SPEC: GH-Scout — Technical Contract v1.0

> **Дата**: 20.09.2026
> **Статус**: Production
> **Проект**: `/home/us/dev/gh-scout/` (US Server)
> **Цель**: Мониторинг GitHub проектов конкурентов + рекомендации

---

## 1. Технические требования

### 1.1 Core Components
| Component | Stack | Port | Status |
|-----------|-------|------|--------|
| API | FastAPI | :8005 | ✅ Live |
| Collector | Python scripts | cron | ✅ Live |
| DB | PostgreSQL | :5432 | ✅ Live |
| Cache | Redis | :6379 | ✅ Live |
| Gateway | Caddy | /ghscout | ✅ Live |

### 1.2 Data Sources
| Source | Type | Frequency | Priority |
|--------|------|-----------|----------|
| GitHub API | REST | Daily | P0 |
| GitHub Search | API | Real-time | P1 |
| RSS Feeds | XML | 30мин | P2 |
| Twitter/X | API | Daily | P2 |

### 1.3 Monitoring Targets
- **P0**: Trading bots (Freqtrade, 3Commas, OctoBot) — daily
- **P1**: DeFi/AI/ML projects — every 2 days
- **P2**: FinTech startups — weekly
- **Trending**: Daily overview

---

## 2. Feature Set

### 2.1 Collector Module
- GitHub repo metadata fetch (stars, forks, issues, PRs)
- Commit history analysis
- Release tracking
- Dependency audit

### 2.2 Recommendation Engine
- Trend detection (star growth rate)
- Feature comparison matrix
- Tech stack analysis
- Activity score calculation

### 2.3 Notification System
- Telegram alerts for top repos
- Weekly digest (cron 11:00 UTC+5)
- Auto-improver (cron 10:00 UTC+5)

---

## 3. API Contract

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/repos | GET | List monitored repos |
| /api/v1/repos/{id} | GET | Repo details |
| /api/v1/recommendations | GET | Top picks |
| /api/v1/trends | GET | Trending analysis |
| /api/v1/alerts | POST | Create manual alert |

---

## 4. Integration Points

| Service | Port | Purpose |
|---------|------|---------|
| Message Bus | :8200 | Cross-agent events |
| Change Log | :8310 | Deployment audit |
| Context DB | :8006 | Shared knowledge |
| Telegram Bot API | - | Notifications |

---

## 5. Testing Requirements

- [ ] GitHub API rate limit handling (429 backoff)
- [ ] Data deduplication (repo already exists)
- [ ] Cron job reliability (systemd timers)
- [ ] PostgreSQL query performance (indexes)
- [ ] Telegram message delivery

---

## 6. Open Questions

1. **Multi-repo sync**: Parallel collectors for 50+ repos?
2. **AI analysis**: LLM-based feature comparison?
3. **Export**: CSV/Excel export of comparisons?
4. **Alert thresholds**: Customizable star growth triggers?

---

**Document Status**: ✅ Spec Complete
**Last Updated**: 20.09.2026
**Owner**: GH Scout Agent
