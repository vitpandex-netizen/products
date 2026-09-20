# 🗂️ Реестр сервисов us-server (единый источник правды)

> **Зачем этот файл:** 20.09 обнаружен `live-trend.service` — дубликат
> `bgt-live-trend.service`, крашился 82 часа (29752 рестарта) никем не
> замеченный, потому что ни один агент не знал о его существовании — не было
> единого списка "что вообще запущено и кто за это отвечает". Этот файл
> закрывает именно этот пробел.
>
> **Правило:** любой агент, создающий/переименовывающий/удаляющий systemd-unit
> на us-server, **обязан** в ту же сессию:
> 1. Проверить `systemctl list-units --all | grep <ключевое слово>` — нет ли
>    уже существующего юнита под старым именем для того же скрипта
> 2. Если переименовывает — `systemctl disable --now <старое_имя>` **в тот же
>    момент**, не "потом" (именно на "потом" и сломалось 13.09)
> 3. Обновить этот файл (строка: имя юнита, скрипт, домен/чат, с какой даты)
>
> Разовая сверка всего списка юнитов — 20.09, при разборе инцидента.

---

## BGT (Bitget Bot) — домен: чат BGT

| Юнит | Скрипт | Что делает | С какой даты | Статус |
|---|---|---|---|---|
| `bgt-live-trend` | `live_trend.py` | Live trend-follow + funding-арбитраж GRAM | 13.09 | ✅ активен |
| `bgt-spot-grid` | `spot_grid.py --pair FIL` | Сетка FIL (Claude) | — | ✅ активен |
| `bgt-spot-grid-sui` | `spot_grid.py --pair SUI` | Сетка SUI (Claude) | — | ✅ активен |
| — (без systemd, вручную) | `spot_grid.py --pair AIN` | Сетка AIN (Гермес) | — | ✅ процесс жив, **не под systemd** — нет автоперезапуска при краше |
| — (без systemd, вручную) | `spot_grid.py --pair PONS` | Сетка PONS (Гермес) | — | ✅ процесс жив, **не под systemd** |
| `bgt-tg-admin` | Telegram kill-switch | Админ-бот, аварийный стоп | — | ✅ активен |
| `bgt-exporter` | Prometheus metrics | Метрики | — | ✅ активен |
| `bgt-monitor` | `monitor_improvement.py` (`/home/us/dev/bitget-bot`) | Непрерывный мониторинг+улучшение | ~19.09 | ✅ активен, поставлен, предположительно, Гермесом |
| `bgt-cross-screener` | `cross_arb_screener.py` | Bitget↔Binance funding-спреды | 19.09 (переписан Claude) | ✅ активен, штатный часовой цикл |
| `bgt-funding-screener` | `funding_arb_screener.py` | Скан funding-арб кандидатов | — | ⏸ таймер, раз в 30 мин |
| `bgt-lead-lag`, `bgt-market-sensor`, `bgt-screener`, `bgt-sonar`, `bgt-whale-sonar`, `bgt-scalper`, `bgt-stat-arb` | research/paper-trading боты | Разное исследование, не боевые деньги | — | ✅ активны (paper) |
| `bgt-qc-gate`, `bgt-risk-qa`, `bgt-strategy-hunter` | Research-боты | Помечены "(Hermes Bot)" в описании | — | ✅ активны — **владелец: Гермес, не Claude** |
| `bgt-multi-screener` | `multi_screener.py` | Автоперезапись пар в `test_3_days_multi.py` через `sudo systemctl restart` | — | ⏸ inactive, **создан Antigravity, архитектурный риск отмечен, не убран** (см. TRIAD_SYNC) |
| `bgt-trailer` / `trailer.py` | Трейлинг-стоп для чужих позиций | — | — | владелец не подтверждён |
| `bgt-test-3-days` | Тест-спринт (Antigravity, конкурс) | — | — | ⏸ inactive, конкурс завершён 17.09 |
| `HyperArb` (`funding_arb_cross.py`) | Bitget↔Hyperliquid арбитраж | **не под systemd** — запускается вручную командой, план перевести под systemd после недели стабильной работы | 19.09 | ✅ live, XMR пилот |

**Дубли, найденные и закрытые 20.09:**
- ❌ `live-trend.service` (без bgt-, создан 01.09 Antigravity, забыт при рефакторе 13.09) — **удалён**
- ❌ `bot-watchdog`, `daily-digest`(+таймер), `bitget-bot` (указывал на несуществующий `bot.py`) — **удалены**, настоящие версии (`bgt-watchdog`, `bgt-digest`) активны

**НЕ дубли — забытые ВЫКЛЮЧЕННЫМИ, восстановлены 20.09:**
- `funding-arb-guard` — ADL-детект/авто-ребаланс/авто-выход для GRAM. Был выключен вручную 10.09, забыт на 10 дней. **Включён обратно.**
- `bgt-watchdog` — dead-man's switch + Alertmanager webhook. Выключен 14.09, забыт на 6 дней. В коде было зашито старое имя `live-trend` вместо `bgt-live-trend` — исправлено. Вебхук был на `0.0.0.0:9094` (публично!) — перепривязан на `100.84.223.96`. **Включён обратно.**

**⚠️ Найден 20.09, НЕ мой домен, публичные порты — см. TRIAD_SYNC для деталей:**
Параллельный paper-trading стек (Freqtrade ×6 `*-bgt-ag`, Hummingbot `*-bgt`,
Jesse `jesse-bgt`) — Docker-контейнеры, не systemd. Проверено: dry_run/без
ключей биржи, капиталу ничего не грозит. Но порты 18091-18096/8097/8000/8098/18083
открыты на `0.0.0.0` — нарушение "только Tailscale". Похоже на активную
работу Antigravity (миграция на Freqtrade, virtual money). Не трогал.

---

## Другие домены (владелец подтверждает сам — не угадываю)

| Юнит | Похоже на домен |
|---|---|
| `hermes-dashboard`, `hermes-change-log`, `hermes-message-bus`, `hermes-serve` | Инфраструктура самого Гермеса |
| `linkid-webapp`, `funnel-keeper` | LinkID |
| `stocks-uz-bot`, `stocks-uz-brief`, `stocks-uz-collect` | Stocks UZ |
| `hhjob-bot`, `uzjobs-tma` | HH Jobs |
| `search-market-bot`, `tg-smart`, `trading-dashboard`, `trading-landing`, `miniapp` | не подтверждено |
| `itops-backup` | IT Ops |
| `vast-proxy`, `ollama`, `ollama-openai-proxy` | инфраструктура LLM, общая |
| `health-check`, `infra-status`, `stack-backup`, `alert-webhook` | похоже на общую инфраструктуру Antigravity |

*(Остальное — системные `dbus-*`, `syslog`, `cloud-init`, `ip6tables` и т.п., не наше)*
