# 🚀 HERMES: HH-Jobs MVP - ФИНАЛЬНЫЙ ПРОМТ

---

## ГЛАВНОЕ

**Ты работаешь НЕЗАВИСИМО от пользователя. Я (Claude) будут мониторить твой прогресс каждый час.**

Пользователь подключится ТОЛЬКО если есть проблема, которую он может решить.

**Как мы общаемся:**
- Ты пишешь код → делаешь commits → обновляешь STATUS.md
- Я читаю commits → понимаю прогресс → спрашиваю пользователя если блокер
- Пользователь отвечает ТОЛЬКО если нужен его ввод

**Результат:** Максимальная автономность, минимум отвлечений пользователя.

---

## 📋 ЗАДАЧА

Реализовать MVP парсера вакансий HH.uz с анализом совпадения профиля.

**Дедлайн:** 48 часов  
**Статус:** НАЧИНАЙ ПРЯМО СЕЙЧАС  

---

## 📁 ВСЕ ФАЙЛЫ ГОТОВЫ

Прочитай эти файлы ДО начала:

1. `/my-project/hh-jobs/MVP.md` ← Полное техническое ТЗ
2. `/my-project/hh-jobs/HERMES_TASK.txt` ← Детали реализации
3. `/my-project/hh-jobs/COMMUNICATION.md` ← Как мы общаемся
4. `/my-project/hh-jobs/.env` ← Конфиг (УЖЕ ЗАПОЛНЕН)

**Все пути:** /Users/vitaliyr/Desktop/Cowork/ClaudeCODE/my-project/hh-jobs/

---

## ⚡ БЫСТРЫЙ СТАРТ

```bash
cd /Users/vitaliyr/Desktop/Cowork/ClaudeCODE/my-project/hh-jobs

# 1. Подготовка
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Запуск (когда готово)
python src/main.py

# 3. Проверка результатов
sqlite3 data/hh.db "SELECT COUNT(*) FROM vacancies;"
tail logs/hh-jobs.log
```

---

## 🔄 КАК ОБЩАТЬСЯ СО МНОЙ (CLAUDE)

### Когда НАЧИНАЕШЬ новую задачу:
```
1. Обновишь STATUS.md:
   - Status: 🔄 In Progress - [name]
   - Last Updated: [timestamp]
   - Progress: 0%

2. Делаешь commit:
   git commit -m "feat: start [component] implementation"
```

### Когда есть ПРОГРЕСС:
```
1. Обновляешь % в STATUS.md
2. Пишешь что сделал в "What Hermes is doing"
3. Commit: git commit -m "feat: [component] (XX% done)"
```

### Когда ЗАВЕРШАЕШЬ компонент:
```
1. STATUS.md → ✅ Completed, 100%
2. Commit с полным описанием:
   git commit -m "feat: complete [component]
   
   - Feature 1
   - Feature 2
   - Tests: 10/10 passed"
```

### Если БЛОКЕР (не можешь продолжать):
```
1. STATUS.md → 🔴 BLOCKED
2. Описываешь проблему:
   - Что не работает
   - Почему не работает
   - Что нужно для решения
3. Commit: git commit -m "fix: [blocker] (BLOCKED - waiting)"
4. ЖДИ: я спрошу пользователя → он ответит → ты продолжишь
```

### Если ВОПРОС (не уверен):
```
1. STATUS.md → Questions section
2. Пишешь вопрос:
   - Что не понимаешь
   - Почему это важно
   - Варианты решения
3. ЖДИ: я спрошу пользователя → получу ответ → обновлю STATUS.md
```

---

## 📊 STATUS.md - ТВОЙ ДНЕВНИК

Вот что ты обновляешь:

```markdown
**Last Updated:** 2026-07-27 14:30
**Status:** 🔄 In Progress - hh_parser.py
**Hermes Progress:** 35%

| Phase | Task | Status | Progress | ETA |
| 1 | hh_parser.py | 🔄 In Progress | 35% | 6h |

**What Hermes is doing:**
- Implemented API connection to HH.uz
- Testing with 10 vacancies
- Working on error handling for network timeouts

**Blockers:**
- None

**Questions/Issues:**
- None (will add if found)

**Next Action:**
- Save parsed vacancies to SQLite
- Implement database schema
```

---

## ✅ ЧТО НУЖНО СДЕЛАТЬ (в порядке приоритета)

### Phase 1: hh_parser.py (12 часов)
- [ ] Подключиться к HH API (https://api.hh.uz/api/v2)
- [ ] Парсить вакансии по критериям из .env
- [ ] Возвращать List[Vacancy]
- [ ] Сохранять в SQLite
- [ ] Тестировать: 10+ вакансий

**Checklist commit:**
```
git commit -m "feat: complete hh_parser.py

- Connects to HH API
- Parses vacancies by keywords/salary
- Saves to data/hh.db
- Error handling implemented
- Tested with 50+ vacancies"
```

### Phase 2: matcher.py (12 часов)
- [ ] Реализовать scoring алгоритм
- [ ] Сравнивать skills (weight 0.5)
- [ ] Проверять зарплату (weight 0.3)
- [ ] Проверять опыт (weight 0.2)
- [ ] Возвращать MatchResult

**Commit:**
```
git commit -m "feat: complete matcher.py

- Scoring algorithm: skills*0.5 + salary*0.3 + experience*0.2
- Matches against profile from .env
- Returns MatchResult with reasons
- Tested: perfect=1.0, partial=0.7, none=0.0"
```

### Phase 3: responder.py (12 часов)
- [ ] Создать функцию respond()
- [ ] Для MVP: мокировать отправку (или реальная если просто)
- [ ] Логировать результаты
- [ ] Сохранять responded_at в БД

**Commit:**
```
git commit -m "feat: complete responder.py

- Responds to vacancies via HH API
- Logs all responses
- Updates database
- Error handling for network issues"
```

### Phase 4: main.py + Integration (12 часов)
- [ ] Собрать parser + matcher + responder
- [ ] Основной цикл: parse → match → respond
- [ ] Логирование всех операций
- [ ] Тестирование end-to-end

**Commit:**
```
git commit -m "feat: complete HH-Jobs MVP

- Main loop: parse vacancies → match → respond
- Proper logging to logs/hh-jobs.log
- Database: 50+ vacancies parsed
- Status: READY FOR PRODUCTION"
```

---

## 🔍 КРИТЕРИИ УСПЕХА

Когда ты завершишь все фазы:

✅ **Parser:**
- Парсит минимум 10 вакансий
- Сохраняет в data/hh.db
- Обрабатывает ошибки API

✅ **Matcher:**
- Считает score для каждой вакансии
- Находит хорошие совпадения (score >= 0.70)
- Логирует результаты

✅ **Responder:**
- Может отправить ответы
- Сохраняет статус в БД
- Логирует операции

✅ **Main:**
- Запускается без ошибок
- Полный цикл работает
- Логи писались корректно

✅ **Git:**
- Все файлы закоммичены
- Commits имеют смысл
- STATUS.md обновлен

---

## 🎯 ЧТО ДЕЛАЕТ CLAUDE (Я)

- Проверяю твои commits каждый час
- Читаю STATUS.md
- Если блокер → спрашиваю пользователя
- Если всё хорошо → просто мониторю
- Когда ты закончишь → интегрирую + деплою

**Тебе ничего не нужно делать кроме кодирования!**

---

## 🚀 НАЧНИ ПРЯМО СЕЙЧАС

1. Прочитай все .md файлы в папке hh-jobs
2. Напиши hh_parser.py
3. Обновляй STATUS.md и делай commits
4. Я буду мониторить каждый час
5. Если нужна помощь пользователя → я спрошу

**Дедлайн: 48 часов. НАЧИНАЙ!** 🔥

---

## 📞 Если КРИТИЧЕСКИЙ блокер

Если что-то СОВСЕМ не работает (not just a bug, но что-то принципиально):

1. Обновляешь STATUS.md → 🔴 CRITICAL
2. Описываешь суть проблемы
3. Commit: `git commit -m "CRITICAL: [explain]"`
4. Я увижу это сразу (мониторю каждый час)
5. Я спрошу пользователя → он решит

---

**РАБОТАЙ НЕЗАВИСИМО. РЕЗУЛЬТАТЫ ГОВОРЯТ САМИ ЗА СЕБЯ.**

Удачи! 🚀🔥💪
