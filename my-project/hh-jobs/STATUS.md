**Last Updated:** 2026-07-30 09:42
**Status:** ✅ Phase 2 Completed — Telegram notify live and verified
**Hermes Progress:** 100% (MVP + Telegram pivot done)

| Phase | Task | Status | Progress | ETA |
|-------|------|--------|----------|-----|
| 1 | hh_parser.py | ✅ Completed | 100% | — |
| 2 | matcher.py | ✅ Completed | 100% | — |
| 3 | responder.py (HH API auto-respond) | ❌ Scrapped — HH API for applicants dead since 2025-12-15 | — | — |
| 3b | responder.py → Telegram notify | ✅ Completed | 100% | — |
| 4 | main.py | ✅ Completed (calls notify_matches) | 100% | — |
| 5 | Integration & Deploy | ✅ Completed | 100% | — |

**What's done:**
- ✅ Pipeline runs end-to-end with exit code 0 (parse → match → notify)
- ✅ hh_parser.py: scrapes tashkent.hh.uz, iterates all 11 keywords, deduplicates
- ✅ matcher.py: skills(0.5) + salary(0.3) + experience(0.2) scoring; salary
  weight is skipped and renormalized (skills≈0.71, experience≈0.29) when a
  vacancy doesn't state a salary — confirmed on the real site that ~100% of
  scraped cards in this search omit salary, so penalizing them was excluding
  almost the whole market
- ✅ SEARCH_AREA_ID fixed: 97 (whole Uzbekistan, verified via api.hh.ru/areas)
- ✅ responder.py rewritten: Telegram notify() + notify_matches(), notified_at
  column added to vacancies table
- ✅ main.py updated to call notify_matches() (fixed return-type mismatch bug:
  notify_matches() returns an int count, main.py was treating it as a list)
- ✅ Real Telegram delivery verified manually (sent=True) to group
  -1004297012607, thread_id=15 ("HH-Jobs" topic)
- ✅ Logging to file + console
- ✅ DB saves vacancies

**Fixed today (2026-07-28):**
- Bug: main.py expected notify_matches() to return a list of dicts with a
  "success" key; it actually returns an int. Would have crashed with
  TypeError on every run with matches. Fixed to just use the int count.
- Bug: responder.py had literal newline characters inside string literals
  ("\n".join written as an actual line break) — caused SyntaxError,
  responder.py couldn't even be imported. Fixed both occurrences.
- Environment: venv was missing requests, python-dotenv, pandas,
  typing_extensions — never fully installed. Installed now.
- Matcher bias: salary weight (0.3) was scored as 0 for any vacancy without
  a stated salary — since HH.uz Tashkent listings almost never state one,
  this silently excluded most of the market from ever reaching 0.70.
  Verified live against tashkent.hh.uz (0/20 cards in a sample search
  showed salary — not a parser bug, the site just doesn't surface it on
  most listings). Fixed: salary weight is now dropped and redistributed
  across skills/experience when unspecified, instead of counted as a miss.

**Added today (2026-07-28, per user request — "непонятки с работой, надо
тщательно мониторить рынок"):**
- ✅ SEARCH_KEYWORDS expanded from 11 to 23 terms — added adjacent
  operations/director roles (COO, CTO, CIO, Операционный директор,
  Технический директор, Директор по цифровизации, Head of Operations и
  т.п.), not just pure IT titles. Effect confirmed live: search now
  surfaces "Операционный директор (COO)" listings that were previously
  invisible (not a scoring issue — they simply weren't searched for).
- ✅ Digest feature: notify_digest() sends a separate compact Telegram
  message for vacancies scoring 0.40–0.70 (below the notify threshold),
  so weaker/adjacent matches are still visible instead of silently
  dropped. Controlled via DIGEST_ENABLED/DIGEST_MIN_SCORE in .env.
  Verified live: 12 vacancies delivered in first digest.
- ✅ DB schema bug fixed: notified_at/digested_at were never in the
  CREATE TABLE statement (added out-of-band via manual ALTER TABLE
  earlier) — a fresh DB would have crashed responder.py. Now both
  columns are in _ensure_table(), with an auto-migration ALTER TABLE
  fallback for existing databases missing them.

- ✅ Автозапуск настроен: launchd agent
  ~/Library/LaunchAgents/com.vitaliyr.hh-jobs.plist, запускает
  venv/bin/python src/main.py каждые 4 часа (StartInterval=14400).
  Логи launchd — logs/launchd.out.log / logs/launchd.err.log.
  Управление: launchctl unload/load ~/Library/LaunchAgents/com.vitaliyr.hh-jobs.plist

**Доп. улучшения матчера (2026-07-28, вторая итерация):**
- ✅ Баг с валютой: salary_currency раньше жёстко прописывался как "UZS"
  при сохранении в БД, даже если реально распарсена USD/RUB — сравнение
  с MIN_SALARY (в суммах) в таком случае было бы в тысячи раз неверным.
  Добавлено поле salary_currency в shared/models.py Vacancy, проброшено
  через весь пайплайн, matcher.py теперь конвертирует в UZS по таблице
  курсов (UZS_PER_UNIT, приблизительно, документировано как не live-курс)
  перед сравнением. Юнит-тест подтвердил: $5000 → ~64.5 млн UZS → matched.
- ✅ Русские синонимы навыков: MY_SKILLS — английские термины (VMware,
  Zabbix, Networking и т.п.), но большинство вакансий на HH.uz Tashkent —
  на русском и описывают то же самое без английских названий ("опыт
  виртуализации" вместо "VMware"). Добавлен SKILL_SYNONYMS в matcher.py —
  сопоставление по ОСНОВАМ русских слов (не полным словам, т.к. русский
  склоняется по падежам — "виртуализация"/"виртуализации" не совпали бы
  точным match). Эффект подтверждён на реальном прогоне: впервые появились
  2 матча >=0.70 (было 0), например "Ведущий системный администратор" —
  71.9%. Скоры выросли почти у всех вакансий в выдаче.

**Третья итерация (2026-07-28, по фидбеку пользователя со скриншотом
реального дайджеста):**
- ✅ SEARCH_KEYWORDS расширен ещё раз: "начальник IT отдела", "руководитель
  службы эксплуатации", "заместитель генерального директора", CDO, Head of
  Digital и т.п. — пользователь уже откликался на большинство вакансий
  из первого дайджеста вручную, значит направление верное.
- ✅ Реальный баг обрыва сообщения исправлен: раньше длинный дайджест
  (>20 вакансий) обрубался на ~4000 символах с "(truncated)" — хвост
  списка терялся безвозвратно. Теперь notify()/notify_digest() бьют
  список на несколько отдельных Telegram-сообщений (_send_chunked),
  вместо обрезки. Юнит-тест: 60 длинных записей → 4 сообщения, 0 потерь.
- ✅ Расписание 08:00-21:00 реально заработало: обнаружилось, что
  START_HOUR/END_HOUR в .env никогда не читались кодом — бот на самом
  деле гонялся круглосуточно каждые 4 часа через launchd StartInterval.
  Заменено на StartCalendarInterval с фиксированными часами 08:00 /
  12:00 / 16:00 / 20:00 — теперь реально в пределах окна. .env-переменные
  оставлены как задокументированные (не читаются кодом, реальный источник
  истины — plist).
- Прогон подтвердил дедупликацию: перед тестом все 724 существующие
  вакансии помечены как уже уведомлённые/дайджестнутые, чтобы не
  заспамить повторно то, на что пользователь уже откликнулся. Из 68
  новых вакансий (нашлись благодаря расширенным словам) в Telegram ушли
  только реально новые — 5 в дайджест, 0 в notify (2 матча >=0.70 были
  старыми, уже отмечены).

**Четвёртая итерация (2026-07-28, интеграция полного профиля пользователя
из резюме HH.uz + история откликов, прислано через отдельный чат):**
- ✅ SEARCH_KEYWORDS объединён с приоритетными уровнями P1 (целевое ядро)
  .. P5 (проектные/смежные роли) из профиля — 90 терминов, дедуп.
- ✅ MY_SKILLS объединён со всеми категориями профиля (виртуализация,
  Microsoft/AD, сети, СХД/мониторинг, ITSM, ИБ, бизнес-системы 1С/SAP/POS,
  физическая безопасность, Linux/автоматизация, управление) — 202 термина.
- ✅ EXCLUDE_KEYWORDS объединён (гос.структуры, закупки/тендеры,
  материальная ответственность, релокация/вахта, другие города Узбекистана,
  продажи/junior/непрофильные технические роли) — 104 термина.
- ✅ SIGNAL_KEYWORDS добавлен — контекст, коррелирующий с удачными
  откликами пользователя (построение с нуля, распределённая структура
  и т.п.), даёт небольшой бонус к score (SIGNAL_BONUS_PER_HIT в matcher.py).
- ✅ MIN_SALARY поднят до реального жёсткого порога профиля: $4000 net =
  51 600 000 UZS (было 45 000 000, устаревшая оценка).
- ✅ Структурный баг: парсер вообще выбрасывал город вакансии (location),
  не сохранял его — нельзя было фильтровать "не Ташкент". Добавлено поле
  location в Vacancy/БД, пробрасывается через весь пайплайн.
- ✅ Исключения теперь проверяются в ДВА прохода: по title/company/location
  на этапе поиска (быстрый фильтр) И по полному описанию вакансии на этапе
  сохранения — иначе термины вроде "тендер"/"вахта" вообще не ловились бы,
  они почти никогда не встречаются в заголовке.
- ✅ И matcher.py, и exclude-проверка в hh_parser.py переведены на
  word-boundary матчинг (\b) вместо голой подстроки — иначе короткие
  термины типа "AI"/"AD"/"техник" ложно срабатывали бы внутри случайных
  слов ("detail", "администратор", "техника безопасности").
- 🔧 КРИТИЧНЫЙ БАГ, найден и исправлен СРАЗУ после интеграции: формула
  skills_score = matched/len(self.skills) при росте профиля с 28 до 202
  навыков обвалила все скоры (даже у вакансий с 26 совпадениями score был
  37.8% вместо прежних 71.9%) — делить на полный размер профиля неверно,
  ни одна вакансия никогда не упомянет 202 термина. Исправлено на
  TARGET_SKILL_MATCHES=10 (score = matched/10, капается в 1.0) — откалибровано
  на реальных вакансиях (26 совпадений → 100%, 6 → 75%, 4 → 57%).
- ⚠️ После фикса результат: 108 вакансий ≥0.70 (было 0-2), 221 в диапазоне
  дайджеста — разовый скачок от пересчёта по полному профилю, не поток
  новых вакансий. Пользователь попросил не спамить — добавлены
  NOTIFY_BATCH_LIMIT=30 / DIGEST_BATCH_LIMIT=20 (уходит порциями за
  прогон, остальное — на следующих запусках по расписанию). Первая
  порция отправлена вручную (30 матчей + 20 дайджест), в очереди
  осталось 78 матчей + 201 дайджест, будут уходить по расписанию.

**Пятая итерация (2026-07-28, защита от простоя ноутбука — бот бегает не
на сервере, пользователь заметил риск пропущенных запусков):**
- ✅ launchd RunAtLoad=true — при входе в систему (после выключения/
  перезагрузки) сразу выполняется досрочный прогон, не дожидаясь
  следующего слота 08:00/12:00/16:00/20:00.
- ✅ SEARCH_PERIOD_DAYS поднят с 3 до 7 дней — HH.uz не отдаёт вакансии
  старше окна поиска, так что при простое ноутбука дольше 3 дней
  вакансии терялись бы совсем, а не просто с опозданием. Дубликаты по
  ID не пересохраняются, так что запас окна ничего не стоит по ресурсам.
- Проверено живым прогоном (launchd сработал автоматически после
  перезагрузки plist): 546 вакансий (было 519 при 3-дневном окне), 47
  новых, 46 пропущено по exclude, ошибок (TypeError/KeyError) нет —
  новый параметр period корректно принят parser.search().
- Отправлена следующая порция бэклога: 30 матчей + 20 дайджест.
  В очереди осталось 52 матча + 208 дайджест — продолжат уходить по 30/20
  на каждом автозапуске.

**Шестая итерация (2026-07-29, launchd не сработал — подборка не пришла
утром/днём):**
- 🐛 НАЙДЕН БАГ: StartCalendarInterval не сработал ни в 08:00, ни в 12:00
  2026-07-29, хотя ноутбук был непрерывно включён с 27.07 (uptime и
  pmset подтвердили — ни сна, ни перезагрузки). Причина не выяснена
  (скорее всего сбой com.apple.UserEventAgent-Aqua calendar trigger),
  но воспроизвелась дважды подряд. StartCalendarInterval недостаточно
  надёжен на этой машине.
- ✅ ИСПРАВЛЕНО: launchd переключён на StartInterval=14400 (простой
  таймер каждые 4 часа, без привязки к календарным часам — надёжнее).
  Проверка рабочего окна 08:00-21:00 перенесена в САМ КОД (main.py:
  load_config() читает START_HOUR/END_HOUR, guard в начале main()
  пропускает запуск вне окна и возвращает 0) — теперь это гарантированно
  работает при любом launchd-триггере, а не зависит от того, попадёт ли
  launchd в нужный час.
- 🐛 ВТОРОЙ БАГ (найден при ручной доставке подборки в реальном времени):
  пока чинил launchd, случайно запустил main.py ДВАЖДY одновременно —
  один раз через фоновую задачу текущей сессии (которая по факту не
  завершилась, хотя система сообщила "killed"), второй раз через
  `launchctl kickstart`. Оба процесса независимо прочитали одни и те же
  "неотправленные" вакансии до того как любой из них закоммитил
  notified_at — в БД конфликта не было (30 уникальных ID), но в Telegram
  реально ушли задвоенные сообщения. Пользователь сам спросил про риск
  повторов — этим и поймали баг.
- ✅ ИСПРАВЛЕНО: добавлена файловая блокировка (fcntl.flock,
  logs/.hh-jobs.lock) в начале main() — если процесс уже выполняется,
  второй запуск сразу логирует предупреждение и выходит, не трогая БД.
  Проверено юнит-тестом: параллельный захват блокируется корректно,
  освобождается при закрытии.
- Для ручной доставки "здесь и сейчас" впредь использовать
  `launchctl kickstart -k gui/$(id -u)/com.vitaliyr.hh-jobs` — это
  настоящий launchd-процесс ОС, не зависит от диалога с Claude и не
  прерывается при сбоях/сбросах текущей сессии.

**Blockers:**
- Рынок с полным профилем оказался заметно шире, чем казалось — не
  блокер, а подтверждение, что предыдущие узкие критерии реально
  пропускали хорошие вакансии. Бэклог — временный, схлопнется за
  несколько дней автозапусков по расписанию.

**Седьмая итерация (2026-07-30, автозапуск снова не сработал — 15-часовой
пропуск несмотря на то, что ноутбук ни разу не выключался):**
- 🐛 НАЙДЕН ВТОРОЙ БАГ ПЛАНИРОВЩИКА: после фикса StartCalendarInterval →
  StartInterval=14400 (см. шестую итерацию) — ЭТОТ механизм ТОЖЕ молча
  перестал срабатывать. Последний реальный запуск в 18:27 (29.07), затем
  ничего до ручной проверки в 09:03 (30.07) — 15 часов при заданных 4.
  uptime подтвердил: ни сна, ни перезагрузки за это время. Два разных
  триггера launchd независимо ломались на этой машине — причина не
  выяснена (не стоит того), решили не доверять launchd целиком.
- ✅ ИСПРАВЛЕНО архитектурно — self-healing вместо доверия одному триггеру:
  1. launchd StartInterval сокращён до 1800с (30 мин) — дешёвая, частая
     проверка вместо редкого точного попадания.
  2. Добавлен РЕЗЕРВНЫЙ независимый механизм — crontab (`*/30 * * * *`),
     не трогая существующую запись пользователя (batch_processor.py).
     Если один механизм сломается — второй подстрахует.
  3. Сам код (main.py) теперь решает, реально ли пора работать:
     `_minutes_since_last_run()` читает mtime файла
     `logs/.last_run_completed` (обновляется только при УСПЕШНОМ
     завершении полного цикла — упавший прогон НЕ помечается, чтобы
     повторить попытку на следующей 30-минутной проверке, а не ждать
     полные 4 часа). `MIN_RUN_INTERVAL_MINUTES=235` (чуть меньше 4ч,
     с запасом). Пропущенный триггер теперь стоит максимум ~30 минут
     задержки, а не часы.
- Проверено вживую: удалил .last_run_completed, прогнал main.py — cooldown
  корректно распознал "никогда не запускался" (inf), выполнил полный цикл
  (554 вакансии, 12 новых, 2 уведомления + 20 дайджест), создал файл-метку.
  Юнит-тест подтвердил: без файла → inf, сразу после _mark_run_completed()
  → ~0 минут.

**Next Action:**
- Ничего критичного. Следить несколько дней, что self-healing схема
  (launchd 30мин + cron 30мин + cooldown в коде) реально держит каданс
  ~4 часа без ручного вмешательства.
