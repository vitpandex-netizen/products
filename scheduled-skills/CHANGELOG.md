# Changelog — Scheduled Skills

Все заметные изменения в этом проекте.

## 1.0.0 (2026-08-07)

### ✨ Добавлено
- Создана структура проекта с четырьмя скиллами
- `morning-market-briefing/SKILL.md` — утренний брифинг (3.7 КБ)
- `midday-market-update/SKILL.md` — дневной апдейт (2.4 КБ)
- `evening-market-summary/SKILL.md` — вечерний итог (3.2 КБ)
- `hmmt4b2-trading-monitor/SKILL.md` — мониторинг облигации HMMT4B2 (2.3 КБ)
- `.interpreter-rules` — правила для Open Interpreter (тип: automation, schedule)
- `.gitignore` — базовый gitignore

### 📝 Заметки
- Все скиллы ориентированы на часовой пояс Asia/Tashkent (UTC+5)
- Используют Yahoo Finance как источник рыночных данных
- Работают через Hermes SDK и launchd для расписания
- Интегрированы с Telegram для отправки уведомлений