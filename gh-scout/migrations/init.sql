-- GH Scout — инициализация БД
-- Таблицы создаются SQLAlchemy, здесь только расширения и индексы

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";