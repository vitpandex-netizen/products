# Communication Protocol: Hermes ↔ Claude

> Это инструкция как мы общаемся БЕЗ участия пользователя

---

## 🔄 Как ЭТО работает

Ты (Hermes) работаешь → Я (Claude) мониторю → Пользователь видит только результаты

**Каналы коммуникации:**
1. **Git commits** - я их читаю автоматически
2. **STATUS.md** - файл статуса в проекте
3. **Логи** - logs/hh-jobs.log
4. **Код** - src/ папка

---

## 📝 ЧТО ТЫ (HERMES) ДЕЛАЕШЬ

### Когда начинаешь новую задачу:
1. **Обновляешь STATUS.md:**
   - Меняешь "Status" на 🔄 In Progress - [task name]
   - Обновляешь timestamp (Last Updated)
   - Заполняешь "What Hermes is doing"

2. **Делаешь commit:**
   ```
   git commit -m "feat: start hh_parser implementation"
   ```

### Когда появляется прогресс:
1. **Обновляешь STATUS.md:**
   - Увеличиваешь "Progress" %
   - Пишешь что уже готово в "What Hermes is doing"
   - Обновляешь ETA если нужно

2. **Делаешь commit:**
   ```
   git commit -m "feat: implement HH API connection (25% done)"
   ```

### Когда завершаешь компонент:
1. **Обновляешь STATUS.md:**
   - Меняешь статус на ✅ Completed
   - Ставишь Progress = 100%
   - Пишешь финальное резюме

2. **Делаешь commit:**
   ```
   git commit -m "feat: complete hh_parser.py

   - Connects to HH API
   - Parses 50+ vacancies per request
   - Saves to SQLite
   - Error handling implemented
   - Tests: 10/10 passed"
   ```

### Если есть БЛОКЕР (проблема):
1. **Обновляешь STATUS.md:**
   - Меняешь "Status" на 🔴 BLOCKED
   - Добавляешь в "Blockers" раздел:
     ```
     **Blocker: HH API authentication**
     - Trying to connect but getting 401 error
     - Need: HH_API_TOKEN with correct permissions
     - Impact: Cannot proceed with parsing
     - Waiting for: User input
     ```

2. **Делаешь commit:**
   ```
   git commit -m "fix: investigate API auth (BLOCKED - need token)"
   ```

3. **Жди:** Я увижу это, спрошу пользователя → он ответит → ты продолжишь

### Если есть ВОПРОС:
1. **Добавляешь в STATUS.md:**
   ```
   **Question: Should salary be in USD or UZS?**
   - .env says MIN_SALARY=45000000
   - Need clarification: is this USD or local currency?
   - Impact: Affects filtering logic
   ```

2. **Жди:** Я спрошу пользователя → получу ответ → обновлю STATUS.md

---

## 🤖 ЧТО Я (CLAUDE) ДЕЛАЮ

### Каждый час:
1. **Проверяю git:**
   ```bash
   git log --oneline -20
   ```
   Вижу что ты сделал и понимаю прогресс

2. **Читаю STATUS.md:**
   - Какой %progress?
   - Есть ли блокеры?
   - Какие вопросы?

3. **Логирую в памяти:**
   - "Hermes завершил parser.py на 60%"
   - "Есть блокер с auth"
   - "Нужен ввод пользователя"

### Если БЛОКЕР найден:
1. **Я спрашиваю пользователя:**
   ```
   ⚠️ БЛОКЕР НАЙДЕН:
   Hermes не может подключиться к HH API
   
   Нужно: Проверить API token в .env
   Status: https://git.../hh-jobs/STATUS.md
   
   Что нужно сделать?
   ```

2. **Пользователь отвечает** → я обновляю файлы → Hermes видит и продолжает

### Если всё хорошо:
1. **Просто логирую:**
   - Hermes на 40% по parser.py
   - Commits хорошие
   - Никаких блокеров
   - ETA: в сроке

2. **Ничего не беспокою пользователя** ✅

### Когда Hermes закончит:
1. **Проверяю результаты:**
   - Все файлы созданы?
   - Тесты проходят?
   - БД заполнена?
   - Логи корректные?

2. **Я интегрирую:**
   - Telegram уведомления
   - Deploy
   - Запуск в продакшене

3. **Подключу пользователя:**
   - Вот готово, вот результаты
   - Вот logи, вот БД
   - Готово к монетизации

---

## 📊 STATUS.md Template

```markdown
**Last Updated:** YYYY-MM-DD HH:MM
**Status:** 🟡 [Current status]
**Hermes Progress:** X%

| Phase | Task | Status | Progress | ETA |
|-------|------|--------|----------|-----|

**What Hermes is doing:**
- Describing current work...

**Blockers:**
- None / Listing if any...

**Questions/Issues:**
- None / Questions...

**Next Action:**
- What's next...
```

---

## 🎯 Git Commit Convention

**Good commits:**
```
feat: implement hh_parser with API connection
feat: add vacancy matching algorithm (70% done)
feat: complete responder module (100% done)
fix: handle empty salary fields
docs: add parser documentation
test: add parser unit tests
```

**Bad commits:**
```
work in progress
update
fix bug
done
```

---

## 📞 Emergency Contact

If CRITICAL blocker (can't proceed at all):
1. Update STATUS.md with 🔴 CRITICAL
2. Commit with message: "CRITICAL: [explain]"
3. I'll see it immediately (hourly check)
4. I'll get user input ASAP

---

## ✅ End of Phase Checklist

When you finish a phase, update STATUS.md:

```
Phase Complete: hh_parser.py ✅

Verification:
- [ ] Code written and tested
- [ ] git commits made
- [ ] status.md updated
- [ ] No blockers remaining
- [ ] Ready for next phase

Metrics:
- Lines of code: XXX
- Tests passed: X/X
- Commits: X
- Time spent: ~Xh
```

---

## 🚀 НАЧНИ ПРЯМО СЕЙЧАС

1. Читаешь эту инструкцию
2. Начинаешь писать hh_parser.py
3. Обновляешь STATUS.md → делаешь commit
4. Я читаю commits каждый час
5. Если проблема → я спрашиваю пользователя
6. Если всё хорошо → ты работаешь дальше

**Пользователю не нужно ничего делать** кроме как ждать результатов и ответить если я спрошу.

---

Good luck! 🚀
