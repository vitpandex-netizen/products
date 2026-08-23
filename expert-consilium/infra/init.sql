-- Expert Consilium — инициализация БД

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Запросы
CREATE TABLE IF NOT EXISTS requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    username TEXT,
    question TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'basic',
    complexity_score FLOAT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Ответы экспертов
CREATE TABLE IF NOT EXISTS expert_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    model TEXT NOT NULL,
    response_text TEXT NOT NULL,
    tokens_in INT DEFAULT 0,
    tokens_out INT DEFAULT 0,
    cost DECIMAL(10,6) DEFAULT 0,
    latency_ms INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Фидбек пользователя
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id) ON DELETE CASCADE,
    user_id BIGINT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_expert_responses_request_id ON expert_responses(request_id);
CREATE INDEX IF NOT EXISTS idx_feedback_request_id ON feedback(request_id);