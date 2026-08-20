# PROJECT MEMORY — постоянная память проектов

> Последнее обновление: 2026-08-08
> Не удалять. Читать перед началом любой работы.

---

## 1. 🧠 КТО Я И КАК МЫШЛЮ

**Пользователь:** IT Director / Head of IT Infrastructure, 19+ лет в IT, 10 лет руководителем.
**Локация:** Ташкент, Узбекистан (UTC+5).
**Цель:** Пассивный доход + удалённая работа на зарубежные компании.
**Ожидания по зарплате:** $4,000–6,000/net.
**Стек:** VMware vSphere, Hyper-V, Proxmox, M365/Exchange, Zero Trust, ITSM/ITIL, AD, VPN, СКУД, СКС, Zabbix, Jira SM.
**Железо:** Mac M1, 8GB RAM, 256GB SSD.
**Характер:** Ценит конкретику, не терпит пустых обещаний. Говорит коротко — отвечай коротко.

---

## 2. 📐 СТАНДАРТЫ И ПРАВИЛА (НАВСЕГДА)

### 2.1 Git
- Всё хранится в git. Каждый проект = отдельный репозиторий.
- Приватный remote: `git@github.com:vitpandex-netizen/<project>.git`
- Никаких `_v2`, `_old`, `copy`, `backup` файлов — для истории есть git.
- SSH ключи (ED25519), не HTTPS с токенами.
- Commit'ы с осмысленными сообщениями, префиксы: `feat:`, `fix:`, `docs:`, `security:`, `chore:`.

### 2.2 Структура диска
```
/Volumes/External/
├── dev/              ← все проекты (каждый = git-репо)
├── models/           ← ollama, lmstudio модели
├── services/         ← данные сервисов
└── docker-volumes/   ← bind-mount для Docker
```
- Ничего не класть в корень диска или корень dev/.
- Новый проект = новая папка в dev/ + git init + remote.

### 2.3 Код
- Python 3.14, venv, requirements.txt.
- .env в .gitignore, права 600.
- shared/ модули для общего кода (db.py, net.py, models.py).
- SQLite через shared.db или свой класс с `with self._conn()`.
- OpenRouter API через `deepseek/deepseek-v4-flash`.
- Telegram: `@famaly_helper_bot`, группа `-1004297012607`, топики по проектам.

### 2.4 Безопасность
- .env: права 600, в .gitignore.
- SSH ключи (ED25519), не пароли.
- Tailscale VPN + exit node (Oracle Cloud).
- Никаких API ключей в коде — только в .env.
- Внешний диск — желательно шифровать (APFS FileVault).

---

## 3. 🏗️ ИНФРАСТРУКТУРА

### 3.1 Машины
| Машина | Роль | Адрес |
|--------|------|-------|
| Mac M1 | Разработка, Docker (OrbStack), launchd | 100.89.205.45 (Tailscale) |
| Oracle Cloud | 24/7 сервер, cron, exit node | 168.138.162.167 / 100.94.224.89 (Tailscale) |

### 3.2 Сеть
- Tailscale: аккаунт `vitpandex-netizen@github`, IP `100.75.108.11`.
- Exit node: Oracle Cloud (Сингапур, 168.138.162.167).
- Весь трафик шифрован (WireGuard → Oracle → интернет).

### 3.3 Docker (OrbStack)
- OrbStack v2.2.2 вместо Docker Desktop.
- `docker-compose up -d` (не `docker compose`).
- Сеть: `transcribe-net` (shared между transcribe-bot и transcribe-service).
- Проблема: HOME интерпретатора не совпадает с реальным. Использовать `HOME=/Users/vitaliyr docker ...`.

### 3.4 Запуск по расписанию
| Сервис | Машина | Расписание | Механизм |
|--------|--------|------------|----------|
| passive-income | Mac | 09:30, 17:00 | launchd (RunAtLoad=true) |
| passive-income | Oracle | 04:30 UTC, 12:00 UTC | cron |
| sync-all | Oracle | каждый час | cron (git pull) |

---

## 4. 📁 ПРОЕКТЫ

### 4.1 my-project
Главный проект. Содержит:
- **passive-income** — исследователь идей + сканер вакансий (LLM + OpenRouter)
- **hh-jobs** — мониторинг вакансий HH.ru (Telegram уведомления)
- **hh-remote-jobs** — удалённые вакансии СНГ
- **stocks-uz** — акции UZSE (Ташкентская биржа)
- **stocks-us** — американские акции (yfinance)
- **finanalytics** — финансовый анализ
- **market-events** — рыночные события
- **passive-income** — пассивный доход
- **shared/** — общие модули (db.py, net.py, models.py)

### 4.2 Остальные проекты (10)
| Проект | Описание | Статус |
|--------|----------|--------|
| agents-toolkit | Оптимизация промптов, batch-обработка | ✅ |
| artifacts | Артефакты | ✅ |
| hermes-webui | Веб-интерфейс для Hermes | ✅ Docker |
| it-operations-framework | Фреймворк IT-операций | ✅ |
| open-interpreter | Open Interpreter | ✅ |
| project-notes | Личные заметки | ✅ приватный |
| scheduled-skills | Планировщик | ✅ |
| transcribe-bot | Telegram-бот расшифровки аудио | ✅ Docker |
| transcribe-service | MLX-транскрибация | ✅ Docker |

---

## 5. 📱 КОММУНИКАЦИЯ

- **Telegram бот:** `@famaly_helper_bot`
- **Группа:** AI Assistant — Family (`-1004297012607`, `is_forum: true`)
- **Топики:**
  - `15` — HH-Jobs
  - `80` — Stocks-UZ
  - `116` — Stocks-US
  - `127` — 📊 Passive Income
  - `59` — Transcribe (общий)
  - `66` — Admin
- **Токен:** `8938976950:AAHXiyYdc9oZMUhCYXRomSMpDSkWNv6WyWc` (в .env, не в коде)
- **Чат пользователя:** `110627043` (личный, для алертов)

---

## 6. 🔐 КЛЮЧИ И СЕКРЕТЫ

| Секрет | Где хранится | Примечание |
|--------|-------------|------------|
| OpenRouter API | `passive-income/.env` | `sk-or-v1-...` |
| Telegram token | `.env` всех проектов | `8938976950:...` |
| SSH ключ | `~/.ssh/id_ed25519` | В GitHub |
| Tailscale auth | `~/.keys.enc` (AES-256-GCM) | Расшифровка через пароль диска |
| Tailscale API | Keychain (macOS) | `tskey-api-...` |
| External Disk PW | Keychain (macOS) | `VNJ61MNggomtprpKrOw2spfGQSpfdBEbpomOb41ANCA=` |

---

## 7. 📋 ЧЕКЛИСТ ПОСТОЯННОГО УЛУЧШЕНИЯ

Каждый раз когда работаешь с проектами:
- [ ] Git status — всё ли закоммичено и запущено?
- [ ] .env — права 600, не в git?
- [ ] Код — нет захардкоженных ключей?
- [ ] Проекты — всё чисто, нет orphaned папок?
- [ ] Tailscale — exit node активен?
- [ ] Docker — контейнеры работают?
- [ ] Oracle — cron активен, проекты синхронизированы?

---

## 8. ⚠️ ГРАБЛИ (ЧТО НЕЛЬЗЯ ПОВТОРЯТЬ)

1. **Не шифровать диск без согласования пароля** — приводило к потере данных.
2. **Не писать в Keychain из sandbox** — HOME интерпретатора не совпадает с реальным. Использовать `osascript` или скрипт для пользователя.
3. **Не вызывать `interpreter-app` из shell** — его нет в PATH для shell-процессов.
4. **Не забывать про `shared/net.py`** — `force_ipv4()` обязателен для Telegram.
5. **Не оставлять venv и data/ в git** — они в .gitignore.
6. **Не создавать файлы вне External диска** — только `/Volumes/External/dev/`.
7. **Не использовать `sudo` без `osascript`** — из sandbox не сработает.

---

## 9. 🎯 БЛИЖАЙШИЕ ПЛАНЫ

- [ ] Мобильное приложение (React Native / Flutter)
- [ ] Реальный парсинг LinkedIn/Upwork через API
- [ ] Telegram-команды для бота (/research, /offers, /top)
- [ ] PostgreSQL для единой БД passive-income
- [ ] Миграция на Team G50 2TB (новый диск)

---

## 10. 🧭 GRAPHYFY — ГРАФ ЗНАНИЙ

Graphify — инструмент для построения навигабельного графа знаний из любой папки файлов.
Уже используется в `it-operations-framework` и `my-project` (результаты в `graphify-out/`).

**Команда (Claude Code):** `/graphify` в корне проекта
**Результат:** `graphify-out/graph.html` (интерактивный граф), `graph.json` (GraphRAG), `GRAPH_REPORT.md`

**Когда использовать:**
- Нужно понять архитектуру проекта
- Найти связи между компонентами
- Проверить что ничего не потерялось
- Перед большим рефакторингом

**Актуальность:** сейчас рано для глубокого графа — проекты только начаты. Но когда кодовая база вырастет — graphify даст карту всей экосистемы.

---

## 11. 💡 МОНИТОРИНГ ИДЕЙ И ТРЕНДОВ

Постоянный сбор актуальных идей и трендов по темам проектов. Обновляется при каждом исследовании.

**Темы для мониторинга:**
- DevOps / IT инфраструктура — удалённая работа, контракты
- Zero Trust / ITSM / M365 — тренды, сертификации
- Пассивный доход — новые инструменты, платформы
- Узбекистан — IT-рынок, инвестиции, финтех
- AI-агенты — новые модели, инструменты, практики
- Удалённая работа — платформы, зарплаты, визы

**Формат:** идеи собираются в `my-project/ideas/` и в БД passive-income.

**Откуда брать:**
- Reddit (r/devops, r/freelance, r/sidehustle, r/passive_income)
- TechCrunch / Hacker News
- LinkedIn (через сканер офферов)
- OpenRouter — новые модели
- GitHub — новые инструменты и тренды
