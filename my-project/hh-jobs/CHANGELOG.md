# 📜 Журнал изменений (Changelog) — UZ IT Jobs Suite

Все изменения проекта документируются в этом файле согласно стандарту [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/) и придерживаются [Semantic Versioning](https://semver.org/lang/ru/).

---

## [1.0.1] — 2026-09-12 (Hotfix)

### Fixed
- **[TASK-005]** Исправление SQL-запроса в боте `@hhjob_ai_bot` (`src/bot.py`): замена несуществующей колонки `published_at` на `created_at` в функции `get_top_vacancies_text`. Устраняет ошибку `⚠️ Ошибка выборки: no such column: published_at` при нажатии «🔥 Топ Match» и вызове `/top`.

### Planned
- Локальное сохранение избранных вакансий (Bookmarks) в интерфейсе Mini App через `localStorage`.
- Дополнительная валидация фильтров минимального скоринга.

---

## [1.0.0] — 2026-09-10 (Enterprise Production Release)

Первый официальный боевой релиз системы мониторинга рынка труда Узбекистана **UZ IT Jobs**.

### Added
- **Telegram Mini App («UZ IT Jobs»):**
  - Разработан Mobile-first SPA-интерфейс с поддержкой Telegram WebApp SDK (авто-тема, полноэкранный режим, haptic feedback).
  - Интерактивный каталог вакансий с живым поиском и фильтрацией по 5 категориям рынка Узбекистана (`🔥 Топ Match`, `👔 Руководство / C-Level`, `🛠 DevOps / Инфраструктура`, `🔒 Инфобез / SOC`, `💻 Разработка`, `🏢 Enterprise / 1C / ERP`).
  - Всплывающее окно (Bottom Sheet) с подробными требованиями работодателя, зарплатной вилкой и прямой ссылкой на HH.uz.
  - Интеллектуальный генератор персонализированных сопроводительных писем под выбранную вакансию на русском и узбекском языках.
  - Вкладка глубокой аналитики рынка Узбекистана: ключевые метрики, рейтинг топовых IT-работодателей (TBC, Anor Bank, UZCARD, Paynet, Huawei) и технологические кластеры спроса.
- **Автономный Telegram-бот (`@hhjob_ai_bot`):**
  - Разработан независимый сервис `src/bot.py` на базе systemd (`hhjob-bot.service`).
  - Поддержка команд `/start`, `/app`, `/stats`, `/top` и кнопки быстрого запуска WebApp.
  - Интеграция системной кнопки меню (ChatMenuButton) для открытия Mini App в один клик.
- **Бэкенд и инфраструктура сбора (US Server 24/7):**
  - Бэкенд на FastAPI (`webapp/server.py`) под управлением `uzjobs-tma.service` на порту `:8095`.
  - Прямое подключение к `hh.db` (918+ актуальных вакансий, 509 IT-компаний Узбекистана).
  - 4 автономных сборщика в `crontab` на US Server:
    - HH Ташкент (`area=97`, RSS): каждые 2 часа с 08:00 до 20:00 $\to$ топик 15.
    - HH Remote (СНГ-удалёнка, RSS): 4 раза в сутки $\to$ топик 52.
    - Habr Карьера API: 2 раза в сутки $\to$ топик 15.
    - Remote-сервисы (RemoteOK, WWR): 2 раза в сутки $\to$ топик 15.
  - Публикация через Tailscale Funnel с доверенным HTTPS: `https://us.tailc8105c.ts.net/uzjobs`.

### Security (Enterprise Private-Only Standard)
- **Изоляция проектов:** Полная автономия от биржевого бота `@stock_uz_bot` и сервисов других контуров.
- **Строгий Whitelist:** Доступ к боту и бэкенду открыт исключительно для авторизованных пользователей по белому списку `ALLOWED_TELEGRAM_USER_IDS` и `TELEGRAM_USER_ID` из Vault.
- **Криптографическая защита WebApp:** Валидация подписи `initData` по алгоритму HMAC-SHA256 с использованием секретного ключа бота. Прямые запросы из интернета без авторизации мгновенно блокируются с кодом `403 Forbidden`.
- **Pre-Push контроль:** Кодовая база проверена аудитором `audit.py` с присвоением наивысшего рейтинга **Grade A** (0 утечек секретов).
- **Хранение секретов:** Токен `HH_JOBS_BOT_TOKEN` защищён в зашифрованном Vault (`~/.secure/vault.enc`) и изолированном `.env` с правами `chmod 600`.

## [1.2.0] - 2026-09-12 (Sprints 2, 3, 4)
### Added
- **AI Matching & Deep LLM Scoring:** Интеграция парсинга неявных навыков, Red Flag Detector (токсичность) и предсказание скрытых ЗП (TASK-HH-027, TASK-HH-028, TASK-HH-033).
- **Executive Workflow:** Внедрен поиск ЛПР (Executive Scout), генерация кастомных Cover Letters и PDF-резюме под вакансию (TASK-HH-016, TASK-HH-021, TASK-HH-023).
- **Automation:** Headless Auto-Apply (имитация) в 1 клик, трекинг откликов (TASK-HH-015, TASK-HH-025, TASK-HH-029).
- **Multi-Persona:** Поддержка переключения профилей CIO / CISO / CTO (TASK-HH-031, TASK-HH-032).
- **Notifications:** Ежедневный Executive Digest и мгновенные Whale Alerts для C-Level вакансий от $4000+ (TASK-HH-019, TASK-HH-024).
- **Copilot:** Голосовой симулятор собеседований и Company Backchannel Radar (TASK-HH-034, TASK-HH-035).
- **Habr Parser:** Интегрирован дополнительный источник парсинга (TASK-HH-020).
