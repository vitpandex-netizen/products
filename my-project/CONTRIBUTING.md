# Contribution Guide

Спасибо за интерес к проекту! Вот как присоединиться и начать разработку.

## 🏁 Getting Started

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/my-project.git
cd my-project
```

### 2. Выбери проект

Посмотри список проектов в [README.md](README.md) и выбери, к какому ты хочешь присоединиться.

### 3. Настрой окружение

```bash
cd <project-name>  # например, hh-jobs
python -m venv venv
source venv/bin/activate  # macOS/Linux
# или: venv\Scripts\activate  # Windows

pip install -r requirements.txt
cp .env.example .env
```

## 🔄 Workflow

### Перед началом работы

1. **Создай ветку:**
   ```bash
   git checkout -b feature/my-awesome-feature
   # или: bugfix/issue-name
   # или: docs/update-readme
   ```

2. **Пусти тесты локально:**
   ```bash
   pytest tests/ -v
   ```

3. **Проверь код quality:**
   ```bash
   black src/
   flake8 src/
   ```

### Во время разработки

- Пиши понятный код с типами (type hints)
- Минимум комментариев — только для сложной логики
- Один коммит = одна логическая задача
- Пиши информативные commit messages:

  ```
  feat: add vacancy matching algorithm
  fix: handle empty salary field in parser
  docs: update API documentation
  ```

### Перед PR

1. **Убедись что тесты проходят:**
   ```bash
   pytest tests/ --cov=src
   ```

2. **Очисти код:**
   ```bash
   black .
   flake8 .
   ```

3. **Актуализируй .env.example** если добавил новые переменные

4. **Обнови README.md** если это был большой функционал

## 📝 Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat` — новая фича
- `fix` — исправление бага
- `docs` — изменения в документации
- `refactor` — рефакторинг без изменения функционала
- `test` — добавление или обновление тестов
- `chore` — обновление зависимостей, конфигов

**Example:**
```
feat: add automatic email sending for vacancy responses

- Implement email composer using OpenAI
- Add SMTP configuration
- Add email templates

Closes #42
```

## 🧪 Testing

Каждый новый функционал должен иметь тесты:

```python
# tests/test_matcher.py
import pytest
from src.matcher import VacancyMatcher

def test_calculate_match_score():
    matcher = VacancyMatcher(skills=["Python", "Django"])
    vacancy = {"skills": ["Python", "Django", "PostgreSQL"]}
    score = matcher.calculate_match(vacancy)
    assert score > 0.7
```

Запуск тестов:
```bash
pytest tests/ -v                    # Все тесты
pytest tests/test_matcher.py -v     # Конкретный файл
pytest tests/ -k "test_match" -v    # По имени
pytest tests/ --cov=src             # С покрытием кода
```

## 🐛 Bug Reports

Если нашёл баг:

1. Проверь что его ещё нет в Issues
2. Создай новый Issue с:
   - Описанием проблемы
   - Шагами для воспроизведения
   - Ожидаемым результатом
   - Твоей окружением (OS, Python version)

## 💬 Questions?

- Открой Discussion
- Напиши в общий чат проекта
- Сделай комментарий к PR

## 📋 Before You Submit PR

- [ ] Код протестирован локально
- [ ] Все тесты проходят
- [ ] Code style OK (black, flake8)
- [ ] README обновлён (если нужно)
- [ ] .env.example обновлён (если нужно)
- [ ] Коммиты имеют информативные messages
- [ ] Нет merge conflicts

## 🚀 PR Checklist

Когда создаёшь PR:

```markdown
## Description
Краткое описание того что делает этот PR

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Как можно протестировать эти изменения?

## Checklist
- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] .env.example updated
```

---

**Спасибо за вклад в проект! 🎉**
