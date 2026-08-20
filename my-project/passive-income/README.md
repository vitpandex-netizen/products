# Passive Income Researcher

Исследовательский агент для поиска и оценки идей пассивного дохода.

## Структура

```
passive-income/
├── src/
│   ├── db.py          # SQLite-слой на shared.db
│   ├── researcher.py  # Поиск + оценка идей
│   └── telegram.py    # Отправка в @famaly_helper_bot
├── research/          # Ручные исследования
├── data/              # SQLite БД (в .gitignore)
├── logs/              # Логи (в .gitignore)
├── .env               # Секреты (в .gitignore)
├── .env.example       # Шаблон
└── .gitignore
```

## Использование

```bash
cd /Volumes/External/dev/my-project
python passive-income/src/researcher.py
```

## Telegram

- Бот: `@famaly_helper_bot`
- Группа: AI Assistant — Family
- Топик: passive-income

## Git

git@github.com:vitpandex-netizen/my-project.git
