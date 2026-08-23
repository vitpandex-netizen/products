# AquaBot — Voice-to-Text коммерческий продукт

## Концепция
Аналог Aqua Voice: голосовой ввод с AI-очисткой и структурированием текста.

## Roadmap

### MVP (сегодня) — Telegram бот
- [x] Приём голосовых сообщений из Telegram
- [x] Транскрибация через Whisper (self-hosted)
- [x] AI-очистка текста (удаление мусора, структурирование)
- [ ] Возврат чистого текста

### V2 — Кроссплатформенный ввод
- Голосовой ввод в любом приложении (через системный оверлей)
- Поддержка iOS, Android, macOS, Windows
- Контекстное понимание (как Aqua Voice)

### V3 — API для бизнеса
- API для интеграции в CRM, ERP, ITSM
- Кастомные словари (IT-термины, медицинские, юридические)
- Enterprise: self-hosted, DPA, Zero Data Retention

## Технологии
- Whisper (self-hosted, faster-whisper medium)
- Hermes AI для очистки и структурирования
- Telegram Bot API как интерфейс
- Docker для изоляции

## Монетизация
- Freemium: X минут/день бесплатно
- Pro: безлимит + кастомные словари
- Enterprise: self-hosted + DPA