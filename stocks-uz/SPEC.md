# SPEC: Stocks-UZ — Technical Contract v1.0

> **Дата**: 20.09.2026
> **Статус**: Active
> **Проект**: `/home/us/projects/stocks-uz/` (US Server)
> **Цель**: Мониторинг UZSE (Узбекская фондовая биржа) + аналитика

---

## 1. Технические требования

### 1.1 Источники данных
| Источник | Тип | Частота | Статус |
|----------|-----|---------|--------|
| UZSE API | REST | Каждый час | ✅ Live |
| Telegram channels | WebSocket | 3ч интервал | ✅ 13 каналов |
| OpenInfo.uz | Scraper | При выходе | 🔄 Manual |
| NAPP (OTC) | PDF parser | Ежедневно | ⏳ Pending |

### 1.2 Выходные данные
- OHLCV кэш в PostgreSQL (ohlcv_history таблица)
- Insights из NLP анализа (insights таблица)
- Key figures tracker (key_figures таблица)
- Trade flow агрегация (trade_flow таблица)
- Сигналы >10% в Telegram topic 576

### 1.3 API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/status | GET | Portfolio summary + accounts |
| /api/portfolio | GET | Holdings breakdown |
| /api/ask | POST | AI query interface |
| /tma/ | GET | Telegram Mini App |
| /health | GET | Service health check |

---

## 2. Risk Management

### 2.1 Data Integrity
- **Reconciliation**: Daily check vs broker statements
- **Duplicate prevention**: ticker+date+type unique constraint
- **Source validation**: Multiple source cross-check for dividends

### 2.2 Service Resilience
- **Cron fallback**: If collector fails, use cached data
- **Rate limit handling**: 429 backoff with exponential retry
- **Alerting**: Telegram notification on failures

---

## 3. Integration Points

### 3.1 Internal
| Service | Port | Usage |
|---------|------|-------|
| DataCore Postgres | 5432 | Primary DB |
| DataCore Redis | 6379 | Cache + Pub/Sub |
| Message Bus | :8200 | Cross-project events |

### 3.2 External
| Service | Purpose |
|---------|---------|
| Telegram Bot API | Push notifications |
| Jett/GoInvest LK | Portfolio verification (browser) |

---

## 4. Testing Requirements

### 4.1 Data Validation
- [ ] OHLCV counts match broker statements
- [ ] Dividend calculations verified manually
- [ ] Telegram channel parsing produces no errors
- [ ] API response time < 500ms

### 4.2 Regression
- [ ] Market holidays handling
- [ ] Duplicate insight prevention
- [ ] Currency conversion accuracy (UZS ↔ USD)

---

## 5. Compliance

### 5.1 Logging
- All data fetches with timestamps
- All Telegram messages with chat_id
- All errors with full traceback

### 5.2 Audit
- Daily cron logs to /var/log/stocks-uz/
- Weekly P&L reconciliation report
- Monthly data quality audit

---

## 6. Open Questions

1. **NAPP integration**: Need PDF parser for OTC trades?
2. **Real-time alerts**: WebSocket vs polling for price triggers?
3. **Multi-broker support**: Jett + GoInvest + EXTURE+G?
4. **Tax reporting**: Need export to Excel/CSV for accounting?

---

**Document Status**: ✅ Spec Complete
**Last Updated**: 20.09.2026
**Owner**: Hermes (Stocks UZ Agent)
