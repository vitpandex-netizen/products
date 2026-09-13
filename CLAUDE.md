# 🎯 CLAUDE.md — Единый стандарт для ВСЕХ чатов, ботов и агентов

---

## 📌 Быстрый старт

**Перед началом работы:**
1. Прочитай `/dev/TRIAD_SYNC.md` (последние записи + блокеры)
2. Выбери задачу из `/dev/BACKLOG.md` по своему домену
3. Включи context isolation (одна сессия → одна задача)
4. Следуй 5 Quality Gates перед пушем

**После окончания:**
1. Закоммити с `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>`
2. Пусни `/audit --history` перед push (ОБЯЗАТЕЛЬНО)
3. Обнови `/dev/BACKLOG.md` (mark done + DOD verified)
4. Напиши handover в `/dev/TRIAD_SYNC.md` (что сделал + что дальше)

---

## 🧠 10 Вайб-привычек для роста эффективности

### 1️⃣ Качество промпта определяет результат
**Правило:** Плохой результат = плохая постановка. Прежде чем жаловаться на модель, переформулируй промпт.
- ✅ Быть максимально конкретным (не "сделай UI", а "кнопка с border-radius 8px, hover эффект fade-in 200ms")
- ✅ Предоставить контекст (структура проекта, constraints, примеры)
- ✅ Ожидать уточнения в ответ (хороший промпт часто требует диалога)

**Action:** Перед тем как отклонить результат, попробуй переформулировать промпт 3 варианта.

---

### 2️⃣ Изоляция контекста (Context per task)
**Правило:** Одна сессия = одна задача. Новая задача = новое окно/сессия.
- ✅ Экономит токены (не копишь контекст старых задач)
- ✅ Чистое состояние (нет degrade когда контекст переполняется)
- ✅ Easier handover (новому агенту не нужно разбираться в истории)

**Action:** Закрывай сессию перед переходом на другую задачу. Исключение: если в одной сессии 2+ связанные задачи (OK на 30-40 минут).

---

### 3️⃣ Переиспользование паттернов (Skills & Templates)
**Правило:** Если ты уже писал похожее — ищи skill или ранее созданный шаблон.
- ✅ `/code-review` — для ревью кода (low/medium/high/ultra)
- ✅ `/audit` — для security проверки (A–F grade)
- ✅ `/role-*` — для специализированных взглядов (architect, security, reviewer, qa)
- ✅ `/design` — для UI/UX дизайна
- ✅ `/dataviz` — перед графиками и дашбордами

**Action:** Перед началом — гугли, есть ли skill для этого. `/` и ищи похожее.

---

### 4️⃣ Фиксация правил из ошибок (Error Formalization Loop)
**Правило:** Ошибка, повторённая дважды — это правило для системы.
- ✅ Задокументируй в `~/dev/SECURITY_RULES.md` или `CLAUDE.md`
- ✅ Добавь в pre-push hook (если security) или в тесты
- ✅ Напиши в MEMORY.md с `[[cross-reference]]` если нужно запомнить навсегда

**Примеры:**
- "Hermes confabulation" → now `[[hermes_confabulation_context_not_model]]` in MEMORY
- "IPv6 blocks Python" → now `[[telegram_ipv6_blocked]]` in MEMORY
- "Tailscale SSH broken" → now `[[us_server_tailscale_ssh_broken]]` in MEMORY

**Action:** Когда ошибка повторится, STOP, документируй, добавь контроль.

---

### 5️⃣ Аудит архитектурной целесообразности (Arch Review)
**Правило:** Перед кодингом — почемучка. "Нужно ли это вообще? Есть ли проще?"
- ✅ Запусти `/role-architect` перед крупными изменениями
- ✅ Спроси: "Это лучший способ? Какие trade-offs?"
- ✅ Если сомневаешься → CONSILIUM в `/dev/TRIAD_SYNC.md`

**Action:** Для задач на 2+ дня: планирование в `/dev/BACKLOG.md` (status: ARCH_REVIEW) до кодинга.

---

### 6️⃣ Обязательный Security Review (InfoSec Zero-Tolerance)
**Правило:** Никакого деплоя без security OK. Это не опционально.
- ✅ `/audit [DIR]` локально перед push
- ✅ `/audit --history [DIR]` если touching секреты (ловит утёкшие в истории)
- ✅ Гейт: Grade A = минимум, иначе БЛОК на push
- ✅ 4-layer security обязательна:
  - Layer 0: prompt masking + secret-guard hook
  - Layer 1: `.env` chmod 600, в `.gitignore`
  - Layer 2: encrypted vault `~/.secure/vault.enc`
  - Layer 3: GitHub Secrets / systemd / compose `${VAR}`

**Action:** `/audit --history` → grade A → only then push. Никаких исключений.

---

### 7️⃣ Поэтапное проектирование (Design Funnel)
**Правило:** Идея → Архитектура → План → Код. No skipping steps.

```
1. IDEA:        Что нужно сделать? Зачем?
2. ARCHITECTURE: Как это вместит в систему? Какие компоненты?
3. PLAN:        Детальный шаг за шагом (в BACKLOG.md как subtasks)
4. CODE:        Писать только когда 1-3 кристально ясны
```

**Action:** Задачи в BACKLOG → `status: PLANNING` → subtasks с DoD → только потом `status: IN_PROGRESS`.

---

### 8️⃣ Утренний брифинг агента (Daily Standup)
**Правило:** День начинается с синхронизации: приоритеты, бюджет, блокеры.
- ✅ Читай `/dev/PROJECTS.md` (текущий статус всех проектов)
- ✅ Смотри `~/dev/BACKLOG.md`: что TOP-3 для моего домена?
- ✅ Проверь блокеры в `~/dev/TRIAD_SYNC.md`
- ✅ Посмотри бюджет (token limits, сроки)

**Для специализированных чатов:**
- BGT: скоринг за ночь, топ-пары, риск-метрики
- IT Ops: мультитенант-готовность, инциденты
- Stocks UZ: волатильность рынка, новости UZSE
- GH Scout: 50+ конкурентов, что обновилось

**Action:** Первый день — запросить брифинг у Master Orchestrator (Antigravity).

---

### 9️⃣ Вечерняя ретроспектива (Daily Standup + Metrics)
**Правило:** День заканчивается аудитом: что сделано, сколько времени, lessons learned.
- ✅ Логируй: `git log --oneline` за день
- ✅ Метрики: lines changed, tests written, issues closed
- ✅ Lesson learned (1-2 предложения) → `/dev/TRIAD_SYNC.md`
- ✅ Обнови `/dev/PROJECTS.md` (% completion, velocity)

**Action:** Перед закрытием сессии: `git log`, запиши в TRIAD_SYNC.md, обнови PROJECTS.md.

---

### 🔟 Оркестрация мультиагентных систем (Multi-Agent Orchestration)
**Правило:** Сложные задачи (2+ дня, мультикомпонентные) → разложить для параллелизма.
- ✅ Master Orchestrator (Antigravity) разбивает на subtasks
- ✅ Каждый агент берёт свой домен (domain affinity)
- ✅ Sync через `/dev/TRIAD_SYNC.md` (CONSILIUM блоки)
- ✅ Rollup результатов в общий handover

**Домены:**
| Чат | Проект | Ответство |
|-----|--------|-----------|
| BGT | bitget-bot | Скоринг, торговля, funding-arb |
| IT Ops | it-operations-framework | Мультитенант, API, деплой |
| Stocks UZ | stocks-uz | UZSE market, волатильность |
| GH Scout | (monitor) | 50+ конкурентов, анализ |
| LinkID | linkid-service | ID/auth инфра |
| DataCore | (data) | Analytics, storage, sync |
| Expert Consilium | architecture | Сложные решения, reviews |

**Action:** Задачи `complexity: HIGH` → CONSILIUM в TRIAD_SYNC.md → декомпозиция.

---

## 🔒 Security (Zero-Tolerance Policy)

**Canonical standard:** `~/dev/SECURITY_RULES.md`

### Layers
- **Layer 0:** Prompt masking, secret-guard hook (блокирует утечки наружу)
- **Layer 1:** `.env` chmod 600, в `.gitignore`, никогда не коммитить
- **Layer 2:** Encrypted vault `~/.secure/vault.enc` (для длительного хранения)
- **Layer 3:** GitHub Secrets, systemd env, `docker-compose.yml` с `${VAR}`

### Pre-push gate
```bash
/audit --history [REPO_DIR]  # MUST be Grade A
```
Если Grade B+ → БЛОКИРУЕТСЯ пушить. Никаких исключений.

### Telegram Bots (все)
- ✅ `ALLOWED_TELEGRAM_USER_IDS` в конфиге (whitelist, не blacklist)
- ✅ Неавторизованные ID → IGNORE без ответа
- ✅ Никаких error messages, leak information

### Secrets в git history
Если засветился:
1. Ротация в соответствующем сервисе (@BotFather, GitHub, AWS, etc.)
2. Обновление в `.env` + vault
3. Рестарт сервисов (CI/CD или manual)
4. Логирование в `/dev/TRIAD_SYNC.md` с меткой `[SECURITY_INCIDENT]`

---

## 🚀 Engineering Standards

### No Overengineering
- ✅ Решение должно быть ПРОСТЫМ на 80%
- ✅ Complexity only если есть clear ROI
- ✅ Prefer existing patterns over new abstractions

### Always Verify
- ✅ `lint` перед commit
- ✅ `test` перед PR
- ✅ `build` перед deploy
- ✅ `smoke test` на staging/prod

### 5 Quality Gates (Mandatory)
```
1. LINT       → code style, no warnings
2. SEC        → /audit grade A minimum
3. REVIEW     → /code-review (peer OK or role-reviewer)
4. SMOKE      → deployed to staging, basic checks pass
5. QA_SIGNOFF → QA verified, DoD met, BACKLOG updated
```

No shortcuts. No "we'll fix later". Every gate or no push.

---

## 📋 Governance & Release

**Canonical standards:** `~/dev/TRIAD_GOVERNANCE_POLICY.md` + `~/dev/RELEASE_POLICY.md`

### Versioning: SemVer 2.0.0
- `MAJOR.MINOR.PATCH` (e.g., 0.4.0)
- CHANGELOG.md в каждом repo (Keep a Changelog format)
- Git tag: `v0.4.0`

### Release cycle
1. Feature complete → BACKLOG mark as TESTING
2. QA verifies all DoD → mark as READY_FOR_RELEASE
3. Release lead merges to main, tags version, deploys
4. Post-deploy smoke test, update PROJECTS.md

### Rollback (P0 incidents)
- Automated if available
- Manual if needed: git revert, redeploy, notify TRIAD_SYNC.md

---

## 📍 Chat Domain Affinity (Strictly Enforced)

**Правило:** Каждый чат работает ТОЛЬКО со своим проектом. Никаких пересечений без CONSILIUM.

| Чат | Проект | Scope | Запрещено |
|-----|--------|-------|----------|
| **BGT** | bitget-bot | Торговля, скоринг, funding-arb, P&L | Лезть в IT Ops, менять боевого бота кроме BGT |
| **IT Ops** | it-operations-framework | Мультитенант API, деплой, security | Менять другие проекты, трейдинг |
| **Stocks UZ** | stocks-uz | UZSE market, волатильность, новости | Путать с BGT, менять linkid |
| **GH Scout** | (internal monitor) | 50+ конкурентов, анализ | Никому не трогать автоматизацию |
| **LinkID** | linkid-service | Auth/ID инфра, мультитенант | Путать с IT Ops |
| **DataCore** | (data layer) | Analytics, DB, sync | Только под согласование Arch |
| **Expert Consilium** | (advisory) | Сложные arch решения, reviews | Не код, только рекомендации |

**Нарушение = автоматический REVERT + письмо в TRIAD_SYNC.md**

---

## 🔗 Shared State & Handover

### TRIAD_SYNC.md
**Где:** `~/dev/TRIAD_SYNC.md`
**Читай в начале** перед стартом работы.
**Пиши в конце** перед закрытием сессии.

```markdown
## Session [DATE] [AGENT_NAME]
- **Task:** ID из BACKLOG.md
- **Status:** IN_PROGRESS → DONE
- **Git hash:** abc123def456
- **Changes:** краткое описание
- **Lessons learned:** 1-2 sentence
- **Blockers for next agent:** если есть
- **Time spent:** XX минут

[CONSILIUM_REQUEST] if needed for complex decision
```

### BACKLOG.md
**Где:** `~/dev/BACKLOG.md`
**Format:**
```
## ID-001: Feature Name
- **Priority:** P0 / P1 / P2
- **Assigned to:** [Domain] or [Agent]
- **Status:** TODO → PLANNING → IN_PROGRESS → TESTING → DONE
- **DoD (Definition of Done):**
  - [ ] Code written & tests pass
  - [ ] /audit grade A (if applicable)
  - [ ] /code-review approved
  - [ ] Smoke tested on staging
  - [ ] CHANGELOG.md updated
  - [ ] Handover written in TRIAD_SYNC.md
- **Deadline:** YYYY-MM-DD
- **Notes:** Any context
```

### PROJECTS.md
**Где:** `~/dev/PROJECTS.md`
**Обновляй ежедневно:**
```
## [ProjectName]
- **Status:** Design / Active / Blocked / Stable
- **% Complete:** XX%
- **Last update:** YYYY-MM-DD [Agent]
- **Velocity:** XX story points/week
- **Current blockers:** none / [description]
- **Next milestone:** YYYY-MM-DD
```

---

## 🎓 Mentorship & Enterprise Insight

**Правило:** Каждое решение должно объяснить владельцу (не для галочки, а для обучения).

Перед handover пиши **Enterprise Insight** — 2-3 предложения про:
- Почему это решение выбрали (vs alternatives)
- Какой архитектурный принцип за ним стоит
- Что владельцу полезно знать

**Пример:**
```
[ENTERPRISE_INSIGHT]
Мы использовали async queue вместо sync API потому что:
1. Scaling: 1000+ requests/sec требуют decoupling
2. Resilience: если downstream падает, не падаем мы
3. Cost: можем throttle workers, не платим за пиковый трафик

Запомни: когда есть бизнес требование "обработать много" → сразу
думай async, не sync. Это архитектурный паттерн enterprise-grade.
```

---

## 🛠️ Quick Reference

### Before Starting
- [ ] Read `/dev/TRIAD_SYNC.md` (latest entries)
- [ ] Pick task from `/dev/BACKLOG.md` for your domain
- [ ] New session (context isolation)
- [ ] Understand constraints: security, budget, domain affinity

### Before Committing
- [ ] `lint` — no warnings
- [ ] `test` — all pass
- [ ] `build` — works locally

### Before Pushing
- [ ] `/audit --history [DIR]` → Grade A minimum (HARD GATE)
- [ ] `/code-review` → approved or role-reviewer signs off
- [ ] CHANGELOG.md updated (Keep a Changelog)
- [ ] Git commit with attribution: `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>`

### After Finishing
- [ ] Update `/dev/BACKLOG.md` (mark DONE, verify DoD)
- [ ] Write handover in `/dev/TRIAD_SYNC.md` (git hash, summary, lessons)
- [ ] Update `/dev/PROJECTS.md` (progress, velocity)
- [ ] Close session (new task = new window)

---

## 🚨 Do's & Don'ts

### ✅ DO
- ✅ Security first (zero-tolerance)
- ✅ Document your ошибки → rules for system
- ✅ Ask in Consilium if unsure
- ✅ Isolate context per task
- ✅ Verify before deploy
- ✅ Mentorship in handover
- ✅ Domain affinity (stay in your lane)

### ❌ DON'T
- ❌ Commit without `/audit --history` (Grade A)
- ❌ Push untested code
- ❌ Touch other domains without CONSILIUM approval
- ❌ Merge to main without smoke test
- ❌ Leave secrets in code/history
- ❌ Overengineer (KISS)
- ❌ Skip quality gates

---

## 🔄 Continuous Improvement

- **Quarterly arch review:** Is our stack still optimal?
- **Monthly metrics:** Velocity, incident rate, security grade
- **Weekly sync:** CONSILIUM on blockers, decisions
- **Daily:** Morning standup (priorities, blockers) + evening retro (lessons, metrics)

Update this file when new patterns emerge. Это живой документ.

---

**Last updated:** 2026-09-13  
**Version:** 1.0 (with 10 Vibe-Coding Habits)  
**Author:** Triad (Hermes + Antigravity + Claude Code)  
**Policy owner:** Expert Consilium + Master Orchestrator
