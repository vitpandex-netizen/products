# HH Jobs Automation

Автоматизация для мониторинга вакансий на hh.ru и отправки автоматических ответов с подготовкой сопроводительного письма.

## 📋 Функционал

- 🔍 Поиск вакансий по критериям
- ✅ Автоматическое совпадение (matching) с профилем
- 💌 Отправка ответов на совпадающие вакансии
- 📄 Генерация сопроводительного письма
- 📊 История обработанных вакансий (SQLite)

## 🚀 Запуск

### 1. Подготовка окружения

```bash
cd hh-jobs
python -m venv venv
source venv/bin/activate  # macOS/Linux
# или: venv\Scripts\activate  # Windows
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка конфигов

```bash
cp .env.example .env
```

Отредактируй `.env`:
```env
HH_API_TOKEN=your_token_here
HH_USER_ID=your_user_id
OPENAI_API_KEY=your_key  # Если используешь ChatGPT для писем

# Критерии поиска
SEARCH_SPECIALIZATION=1  # ID специализации на hh.ru
MIN_SALARY=100000
KEYWORDS=python,django,fastapi
```

### 4. Запуск

```bash
python src/main.py
```

## 📁 Структура

```
hh-jobs/
├── src/
│   ├── main.py              ← Entry point
│   ├── hh_parser.py         ← Парсинг вакансий с hh.ru
│   ├── matcher.py           ← Проверка совпадения
│   ├── responder.py         ← Отправка ответов
│   ├── cover_letter.py      ← Генерация писем
│   └── logger.py            ← Логирование
├── tests/
│   ├── test_matcher.py
│   └── test_parser.py
├── data/
│   └── hh.db               ← SQLite БД (в .gitignore)
├── logs/                    ← Логи приложения
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Технологии

- **Python 3.9+**
- **hh-api** — API hh.ru
- **sqlite3** — Встроенная БД
- **requests** — HTTP запросы
- **python-dotenv** — Управление конфигами

## 📝 Примеры кода

### Парсинг вакансий

```python
from src.hh_parser import HHParser

parser = HHParser(api_token=os.getenv("HH_API_TOKEN"))
vacancies = parser.search(
    keywords="python",
    area_id=1,  # Москва
    min_salary=100000
)
for vacancy in vacancies:
    print(f"{vacancy['name']} - {vacancy['salary']}")
```

### Проверка совпадения

```python
from src.matcher import VacancyMatcher

matcher = VacancyMatcher(profile_skills=["Python", "Django", "FastAPI"])
score = matcher.calculate_match(vacancy)
if score > 0.7:
    print("Подходит! Отправляем ответ")
```

## 🗄️ База данных

История обработанных вакансий хранится в SQLite:

```sql
CREATE TABLE vacancies (
    id INTEGER PRIMARY KEY,
    hh_id INTEGER UNIQUE,
    title TEXT,
    company TEXT,
    salary INTEGER,
    url TEXT,
    matched_score REAL,
    responded_at TIMESTAMP,
    created_at TIMESTAMP
);
```

## ⚙️ Переменные окружения

| Переменная | Описание | Пример |
|------------|---------|--------|
| `HH_API_TOKEN` | Token HH API | `abc123...` |
| `HH_USER_ID` | Твой ID на hh.ru | `12345` |
| `OPENAI_API_KEY` | Ключ OpenAI (опционально) | `sk-...` |
| `MIN_SALARY` | Минимальная зарплата | `100000` |
| `KEYWORDS` | Ключевые слова для поиска | `python,django` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

## 🧪 Тестирование

```bash
python -m pytest tests/
```

## 📊 Мониторинг

Логи пишутся в `logs/hh-jobs.log`:

```
2026-07-26 10:15:23 INFO Found 5 vacancies matching criteria
2026-07-26 10:15:25 INFO Matched 3 vacancies (score > 0.7)
2026-07-26 10:15:30 INFO Sent response to "Senior Python Developer"
```

## 🤝 Contribution

1. Fork проект (или просто clone main repo)
2. Создай ветку: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "feat: описание"`
4. Push: `git push origin feature/my-feature`
5. Создай PR

## 📚 Полезные ссылки

- [HH API Docs](https://dev.hh.ru/)
- [HH Vacancies Endpoint](https://dev.hh.ru/vacancies)
- [Python dotenv](https://github.com/theskumar/python-dotenv)

---

**Статус:** 🟢 В разработке

**Участники:** Hermes

**Последнее обновление:** 2026-07-26
