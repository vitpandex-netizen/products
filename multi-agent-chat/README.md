# Multi-Agent Chat

> **Защищённый веб-чат с 6 AI-агентами**

Multi-Agent Chat — это веб-приложение для одновременного общения с шестью AI-агентами через единый интерфейс. Один API-запрос к OpenRouter генерирует ответы сразу от всех агентов. Поддерживает аутентификацию, 2FA, сквозное шифрование и готов к production-развёртыванию.

## Агенты

| # | Агент | Эмодзи | Роль |
|---|-------|--------|------|
| 1 | **Interpreter** | 🧠 | Координатор, отвечает на общие вопросы, подводит итоги |
| 2 | **Тестировщик** | 🔍 | QA-инженер: баги, тест-кейсы, качество кода |
| 3 | **Claude** | 🤖 | Архитектор: рефакторинг, best practices, дизайн системы |
| 4 | **Hermes** | ⚡ | Оптимизатор: производительность, CI/CD, DevOps, метрики |
| 5 | **Cursor** | 🖱️ | Code-reviewer: ревью кода, тесты, автодополнение |
| 6 | **OpenClaw** | 🦞 | Security/Data: безопасность, данные, мониторинг, дашборды |

## Стек

| Компонент | Технология |
|-----------|-----------|
| Backend | Node.js 22 (Express, WebSocket) |
| Frontend | Vanilla JS, HTML, CSS (SPA) |
| База данных | SQLite (через sql.js, in-memory + file) |
| AI | OpenRouter API (gpt-4o-mini / deepseek-chat) |
| Аутентификация | JWT (access + refresh tokens) |
| 2FA | TOTP (speakeasy + QR-коды) |
| Шифрование | Сквозное (E2E, public key) |
| Rate Limiting | express-rate-limit |
| Безопасность | Helmet, CORS, bcrypt (12 rounds) |
| Развёртывание | Docker, Nginx, Let's Encrypt |

## Быстрый старт

### Локальный запуск

```bash
# 1. Установка зависимостей
npm install

# 2. Создать .env
cp .env.example .env
# Указать OPENROUTER_API_KEY

# 3. Запуск (автосоздание БД + admin пользователя)
npm run setup && npm start
```

Приложение будет доступно на `http://localhost:5555`.

### Docker

```bash
docker compose up -d --build
```

### Production (Oracle VPS)

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh chat.yourdomain.com
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход (с поддержкой 2FA) |
| POST | `/api/auth/refresh` | Обновление токена |
| POST | `/api/auth/logout` | Выход |
| POST | `/api/auth/setup-2fa` | Настройка 2FA |
| GET | `/api/sessions` | Список сессий |
| POST | `/api/sessions` | Создать сессию |
| GET | `/api/sessions/:id` | Детали сессии + сообщения |
| POST | `/api/sessions/:id/join` | Присоединиться к сессии |
| POST | `/api/sessions/:id/invite` | Пригласить пользователя |
| POST | `/api/sessions/update-key` | Обновить публичный ключ |
| WS | `/ws?token=...` | WebSocket для чата |

## Архитектура

```
                    ┌──────────────┐
                    │   Browser    │
                    │  (SPA SPA)   │
                    └──────┬───────┘
                           │ HTTPS / WSS
                    ┌──────┴───────┐
                    │    Nginx     │ (production)
                    │  (reverse)   │
                    └──────┬───────┘
                    ┌──────┴───────┐
                    │   Express    │
                    │   (HTTP)     │
                    └──────┬───────┘
                    ┌──────┴───────┐
                    │   WebSocket  │
                    │   (chat)     │
                    └──────┬───────┘
                    ┌──────┴───────┐
                    │  OpenRouter  │
                    │  (1 вызов → 6 ответов) │
                    └──────────────┘
```

## Структура проекта

```
multi-agent-chat/
├── server/                 # Серверная часть
│   ├── index.js           # Точка входа, Express + HTTPS
│   ├── ws.js              # WebSocket обработчик
│   ├── auth.js            # JWT, bcrypt
│   ├── db.js              # SQLite (sql.js) — все запросы
│   ├── setup.js           # Инициализация БД + admin
│   ├── rateLimit.js       # Rate limiting
│   ├── portal.js          # Infrastructure portal API
│   ├── routes/
│   │   ├── auth.js        # Auth routes (register, login, 2FA)
│   │   └── sessions.js    # Session CRUD
│   └── agents/
│       ├── index.js       # OpenRouter API: batch-вызов агентов
│       └── prompts.js     # Определения 6 агентов
├── public/                 # Фронтенд
│   ├── index.html         # Chat SPA
│   ├── chat/index.html    # Альтернативный чат
│   ├── portal.html        # Infrastructure portal
│   ├── app.js             # Основной клиент (604 строки)
│   ├── crypto.js          # E2E шифрование
│   └── styles.css         # Стили
├── deploy/                 # Production
│   ├── deploy.sh          # Deploy-скрипт
│   └── nginx.conf         # Nginx конфигурация
├── Dockerfile
├── docker-compose.yml
├── package.json
└── certs/                  # TLS сертификаты
```

## Безопасность

- **JWT**: access token (1 час) + refresh token (30 дней)
- **2FA**: TOTP на основе speakeasy + QR-код
- **E2E**: сквозное шифрование сообщений через публичные ключи
- **Rate Limiting**: 5 попыток входа в минуту, 30 API-запросов в минуту
- **Helmet**: security headers
- **bcrypt**: 12 раундов хеширования паролей
- **Nginx**: HSTS, TLS 1.2/1.3, запрет доступа к .env/.git