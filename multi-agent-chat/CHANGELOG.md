# Changelog — Multi-Agent Chat

## [1.0.0] — 2026-08-13

### Добавлено
- **Multi-agent engine**: 6 AI-агентов с единым batch-вызовом OpenRouter
- **WebSocket чат**: real-time общение с агентами (stagger-вывод по 400ms)
- **Аутентификация**: JWT (access + refresh token), bcrypt (12 раундов)
- **2FA**: TOTP-аутентификация через speakeasy + QR-коды
- **E2E Encryption**: сквозное шифрование на основе публичных ключей
- **Rate Limiting**: 5r/m на login, 30r/m на API
- **Безопасность**: Helmet, CORS, XSS-защита
- **Session management**: создание, приглашение, управление сессиями
- **SQLite (sql.js)**: in-memory БД с персистентностью в файл
- **Infrastructure Portal**: дашборд состояния сервисов
- **Docker**: мультистейдж-сборка, self-signed TLS
- **Production deploy**: Nginx + Let's Encrypt + deploy-скрипт
- **Fallback engine**: работа без OpenRouter API (ключевые слова + шаблоны)
- **Авто-инициализация**: setup.js создаёт БД и admin-пользователя

### Безопасность
- JWT_SECRET по умолчанию `dev-secret-change-in-production` (⚠️ требуется замена)
- Refresh token: 64 байта случайных данных, SHA256 хеш
- Пароли: bcrypt с 12 раундами
- CORS: по умолчанию '*' (рекомендуется ограничить в production)

### Технический долг
- Нет unit-тестов
- Нет e2e-тестов WebSocket
- Self-signed сертификаты в Docker (не для production)
- Нет миграций БД (схема создаётся при первом запуске)
- Нет structured logging