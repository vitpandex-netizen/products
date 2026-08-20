# HH-Jobs MVP Task

## 🎯 Цель MVP

Реализовать автоматический поиск вакансий на HH.uz и отправку ответов для подходящих вакансий.

**Версия:** 0.1 MVP  
**Статус:** В разработке  
**Дедлайн:** 48 часов

---

## 📋 Требования MVP (только самое важное)

### 1. Parser (hh_parser.py)

**Что должно быть:**
- Подключиться к HH API (tashkent.hh.uz)
- Получить вакансии по критериям:
  ```python
  {
    "text": "python",  # Ключевое слово
    "area": 110,      # Узбекистан
    "salary_from": 1000000,  # Минимальная зарплата
  }
  ```
- Вернуть `List[Vacancy]` с полями:
  - id, title, company, url, salary_from, salary_to, skills

**Простой пример:**
```python
class HHParser:
    def __init__(self, api_token=None):
        self.base_url = "https://api.hh.uz/api/v2"
        self.session = requests.Session()
    
    def search(self, keywords: str, min_salary: int = 0) -> List[Vacancy]:
        # Парсить вакансии и вернуть список
        pass
```

**Данные сохранять в БД:**
```python
from shared.db import Database
db = Database("data/hh.db")
db.execute_insert("INSERT INTO vacancies ...", ...)
```

---

### 2. Matcher (matcher.py)

**Что должно быть:**
- Получить профиль (из .env или конфига):
  ```python
  profile = {
    "skills": ["Python", "Django", "PostgreSQL"],
    "experience_years": 5,
    "preferred_salary": 3000000,
  }
  ```
- Для каждой вакансии считать `match_score` (0.0 - 1.0):
  - Сколько скиллов совпало? (weight 0.6)
  - Зарплата подходит? (weight 0.3)
  - Опыт подходит? (weight 0.1)

**Простой пример:**
```python
class VacancyMatcher:
    def __init__(self, profile):
        self.profile = profile
    
    def calculate_match(self, vacancy: Vacancy) -> MatchResult:
        # Посчитать score и вернуть MatchResult
        pass
```

---

### 3. Responder (responder.py)

**Что должно быть:**
- Для вакансий с `match_score >= 0.7` отправить ответ
- HH API endpoint: `POST /vacancy/{id}/responses`

**Простой пример:**
```python
class Responder:
    def __init__(self, hh_user_id, api_token):
        self.user_id = hh_user_id
        self.token = api_token
    
    def respond(self, vacancy_id: int, text: str = "") -> bool:
        # Отправить ответ через HH API
        pass
```

---

### 4. Main Loop (main.py)

**Что должно быть:**
```python
def main():
    # 1. Парсить вакансии
    vacancies = parser.search(keywords="python", min_salary=1000000)
    logger.info(f"Found {len(vacancies)} vacancies")
    
    # 2. Матчить
    matches = [matcher.calculate_match(v) for v in vacancies]
    good_matches = [m for m in matches if m.is_good_match()]
    logger.info(f"Matched {len(good_matches)} vacancies")
    
    # 3. Отправить ответы
    for match in good_matches:
        if responder.respond(match.vacancy.id):
            logger.info(f"✅ Responded to {match.vacancy.title}")
```

---

## 📁 Структура файлов

```
hh-jobs/
├── src/
│   ├── main.py              ← Entry point (уже есть)
│   ├── hh_parser.py         ← СОЗДАТЬ: парсер
│   ├── matcher.py           ← СОЗДАТЬ: матчер
│   └── responder.py         ← СОЗДАТЬ: ответчик
├── tests/
│   ├── test_parser.py       ← Тесты парсера (опционально для MVP)
│   └── test_matcher.py      ← Тесты матчера (опционально для MVP)
├── data/
│   └── hh.db               ← БД (создаётся при первом запуске)
├── logs/
│   └── hh-jobs.log         ← Логи (создаются при запуске)
├── .env.example            ← Есть
├── requirements.txt        ← Есть
└── MVP.md                  ← Этот файл
```

---

## ⚙️ Конфигурация (.env)

**УЖЕ ГОТОВО** в `.env` - все параметры установлены:

```env
# Профиль: IT Infrastructure Engineer (19 лет опыта)
# Зарплата: $4,500-6,000 net
# Позиции: IT Manager, Head of IT, System Administrator, Network Engineer, etc.

SEARCH_KEYWORDS=IT Infrastructure Engineer,Senior System Administrator,IT Manager,Head of IT...
MIN_SALARY=45000000  # ~$4,500 USD в узбекских сумах
EXPERIENCE_LEVEL=moreThan6
MIN_MATCH_SCORE=0.70

MY_SKILLS=VMware,Hyper-V,Proxmox,Microsoft 365,Active Directory,Zabbix,Servers,Networking...
EXCLUDE_KEYWORDS=government,procurement,tender,госструктура

AUTO_RESPOND_ENABLED=true
PREFERRED_LOCATION=Tashkent
```

---

## 📊 Зависимости

Обновить `requirements.txt`:
```
requests==2.31.0
python-dotenv==1.0.0
pandas==2.0.3  # опционально, для удобства
```

---

## ✅ Критерии завершения MVP

- [ ] `hh_parser.py` парсит хотя бы 10 вакансий
- [ ] `matcher.py` считает score корректно (тест: perfect match = 1.0, no match = 0.0)
- [ ] `responder.py` может отправить ответ (или мокировать в тестах)
- [ ] `main.py` запускается без ошибок
- [ ] Логи пишутся в файл и консоль
- [ ] БД сохраняет вакансии (можно проверить `sqlite3 data/hh.db`)

---

## 🔍 Как тестировать локально

```bash
cd hh-jobs

# 1. Создать .env
cp .env.example .env
# Заполнить HH_USER_ID и другие параметры

# 2. Установить зависимости
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Запустить
python src/main.py

# 4. Проверить результаты
ls -la data/hh.db    # БД
tail logs/hh-jobs.log  # Логи
sqlite3 data/hh.db "SELECT * FROM vacancies LIMIT 5;"  # Данные
```

---

## 📝 Notes for Hermes

- Используй `shared/db.py` для БД (уже готово)
- Используй `shared/models.py` (класс Vacancy уже определён)
- Документация HH API: https://dev.hh.uz/ или просто гугли tashkent.hh.uz API
- Если API закрыт - можно использовать веб-скрейпинг (но API проще)
- Не усложняй MVP - фокус на core функционалу
- Коммитись в git: `git add -A && git commit -m "feat: implement hh parser"`

---

## 🚀 После MVP

Потом добавим:
- Telegram интеграция (уведомления)
- Cover letters (генерация писем)
- Продвинутые фильтры
- Scheduler (работает раз в час)
- И т.д.

**Сейчас:** Просто work!

---

**Версия:** 0.1  
**Дата:** 2026-07-26  
**Статус:** Ready for implementation
