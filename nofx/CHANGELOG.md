# Changelog — NOFX

## [Unreleased]

### Добавлено
- Базовая архитектура сервиса: Go backend + SQLite (GORM)
- Docker Compose конфигурация для production развёртывания
- REST API: управление AI-трейдерами, получение рыночных данных
- Интеграция с CoinAnk API для потоковых рыночных данных
- Шифрование данных (encryption service)
- JWT-аутентификация
- Веб-интерфейс (предустановленный frontend образ)
- Healthcheck endpoints
- Конфигурация CORS (dev-режим)

### Технический долг
- CORS_ALLOWED_ORIGINS не настроен для production
- Нет тестов
- auth-заглушка для публичных endpoint'ов
- API-ключи хранятся в .env без шифрования
- Нет rate limiting
- Нет автоматических миграций БД