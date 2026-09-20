# Skill Updates — 17.09.2026

## Обновлённые навыки

### bgt-multi-agent-workflow
- **Capital Registry: reserve = MAXIMUM NOTIONAL** — предупреждение про leverage
- **ATR Calculation Pitfall** — True Range вместо mid-to-mid
- **UNAUTHORIZED DEPLOY** — инциденты 16-17.09, действия при обнаружении
- **Проверка суммы перед деплоем** — `sum(reserved) ≤ limit`, дубли в capital_allocation.json

### bgt-status-reporting
- **Двойной учёт в capital_allocation.json** — сводка + детальные = $40 вместо $20

## Уроки сессии

1. **capital_registry reserve = MAXIMUM NOTIONAL**, не formal barrier
2. **Проверять сумму ДО деплоя** — `sum(reserved) ≤ limit`
3. **ATR считать через True Range** (high-low), не mid-to-mid
4. **Не дублировать записи** — либо сводка, либо детальные, не оба
5. **Любой торговый скрипт требует явного подтверждения**
