# MY Project — Автоматизация для достижения целей

Монорепо для совместной разработки нескольких AI-агентов и автоматизаций.

## 📋 Проекты

| Проект | Описание | Статус |
|--------|---------|--------|
| **hh-jobs** | Мониторинг вакансий HH + автоответы | 🟢 В работе (Hermes) |
| **stocks-ru** | Анализ рынка акций РФ | 🟡 Планируется |
| **stocks-us** | Анализ рынка акций США | 🟡 Планируется |
| **market-events** | Отслеживание мировых событий | 🟡 Планируется |
| **finanalytics** | Финансовый агент | 🟡 Планируется |

## 🚀 Быстрый старт

### Требования
- Python 3.9+
- Git

### Запуск конкретного проекта

```bash
# Пример: запуск HH-проекта
cd hh-jobs
python -m venv venv
source venv/bin/activate  # macOS/Linux
# или: venv\Scripts\activate  # Windows

pip install -r requirements.txt
cp .env.example .env       # Скопировать и настроить конфиги

python src/main.py
```

**Каждый проект имеет свой README.md с полными инструкциями!**

## 📁 Структура

```
my-project/
├── hh-jobs/              ← Парсинг и автоответы вакансий
│   ├── src/
│   ├── tests/
│   ├── data/             (БД, не коммитится)
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── stocks-ru/            ← Анализ РУ рынка акций
├── stocks-us/            ← Анализ США рынка акций
├── market-events/        ← Мониторинг событий
├── finanalytics/         ← Финансовый агент
├── shared/               ← Общие утилиты, модели
├── docs/                 ← Документация
└── .github/workflows/    ← CI/CD
```

## 👥 Для новых участников

1. **Clone репо:**
   ```bash
   git clone https://github.com/your-org/my-project.git
   cd my-project
   ```

2. **Выбери проект** из списка выше

3. **Следуй README.md проекта** — там всё описано

4. **Делай PR в main** перед merge:
   ```bash
   git checkout -b feature/my-feature
   git commit -m "feat: описание"
   git push origin feature/my-feature
   # Создать PR на GitHub
   ```

## 🔄 Процесс разработки

- **Code Review:** Каждый PR требует одобрения перед merge
- **Логирование:** Используй Python logging (логи в `logs/`)
- **Данные:** БД SQLite в папке `data/` (в .gitignore)
- **Конфиги:** Секреты в `.env`, обновляй `.env.example`

## 📞 Контакты

- **Hermes** — HH-проект
- **[Твоё имя]** — Координатор, stocks-ru, finanalytics
- **[Новый участник]** — stocks-us, market-events

## 💡 Roadmap

- [ ] Q3 2026: MVP всех проектов
- [ ] Q4 2026: Интеграция между проектами (shared API)
- [ ] 2027: Монетизация (SaaS / API)

---

**Вопросы?** Открой Issue или напиши в общий чат проекта.

*Последнее обновление: 2026-07-26*
