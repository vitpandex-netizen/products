# Project Notes

> Система заметок и документации проектов. Хранит AGENTS.md-файлы и вспомогательные материалы для каждого проекта в `/Volumes/External/dev/`.

## 📋 Описание

Реестр проектной документации в формате Markdown. Каждый каталог внутри соответствует отдельному проекту или теме и содержит `AGENTS.md` — файл с описанием агента, его роли, инструкций и контекста для AI-ассистентов.

Проект служит «памятью» для агентов — централизованное место, где хранятся инструкции, настройки и контекст для каждого направления работы.

## 📁 Структура

```
.
├── AMMC/                # Агент: AMMC (Asset Management & Market Control)
│   └── AGENTS.md        #   Описание роли и инструкций AMMC
├── TGW/                 # Агент: TGW (Trading Gateway)
│   └── AGENTS.md        #   Описание роли и инструкций TGW
├── UZInvest/            # Агент: UZInvest (Узбекские инвестиции)
│   ├── AGENTS.md        #   Описание роли и инструкций UZInvest
│   └── Инвестиционный_план_10млн.xlsx  # Финансовая модель (20 КБ)
├── .interpreter-rules   # Правила для Open Interpreter (docs, notes)
├── .gitignore
```

## 🧰 Стек

- **Формат:** Markdown (AGENTS.md)
- **Дополнительно:** Excel (.xlsx) для финансовых моделей
- **Среда:** Любая — файлы читаются любым редактором / AI-агентом

## 📖 Проекты

| Каталог | Описание |
|---|---|
| **AMMC** | Asset Management & Market Control — управление активами и рыночный контроль |
| **TGW** | Trading Gateway — шлюз для торговых операций |
| **UZInvest** | Инвестиции в Узбекистане — финансовая модель на 10 млн сум |

## 🔧 Использование

```bash
# Посмотреть все проекты
ls /Users/vitaliyr/dev/project-notes/

# Прочитать AGENTS.md для проекта
cat /Users/vitaliyr/dev/project-notes/AMMC/AGENTS.md

# Добавить новый проект
mkdir /Users/vitaliyr/dev/project-notes/my-new-project/
touch /Users/vitaliyr/dev/project-notes/my-new-project/AGENTS.md
```

## 🎯 Назначение

- Единый источник контекста для AI-агентов (Hermes / Open Interpreter)
- Документирование ролей и инструкций каждого агента
- Хранение сопутствующих материалов (Excel, PDF, изображения) рядом с AGENTS.md