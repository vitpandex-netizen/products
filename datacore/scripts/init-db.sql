-- DataCore — Initial Database Schema
-- Схемы: market_data, analytics, core

CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS core;

-- ============================================
-- CORE: источники данных и конфигурация
-- ============================================
CREATE TABLE IF NOT EXISTS core.data_sources (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(64) NOT NULL UNIQUE,   -- yahoo, polymarket, bitget, hyperliquid
    label       VARCHAR(128) NOT NULL,
    enabled     BOOLEAN NOT NULL DEFAULT true,
    config      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS core.symbols (
    id          SERIAL PRIMARY KEY,
    source_id   INTEGER REFERENCES core.data_sources(id),
    symbol      VARCHAR(64) NOT NULL,          -- BTC-USD, ETH-USD, etc.
    asset_type  VARCHAR(32) NOT NULL,          -- crypto, stock, index, prediction
    meta        JSONB,
    active      BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_id, symbol)
);

-- ============================================
-- MARKET DATA: временные ряды цен
-- ============================================
CREATE TABLE IF NOT EXISTS market_data.prices (
    id          BIGSERIAL,
    symbol_id   INTEGER NOT NULL REFERENCES core.symbols(id),
    source      VARCHAR(64) NOT NULL,
    price       NUMERIC(20, 8) NOT NULL,
    bid         NUMERIC(20, 8),
    ask         NUMERIC(20, 8),
    volume      NUMERIC(20, 4),
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (symbol_id, ts, id)
);

-- Индексы для быстрых запросов
CREATE INDEX IF NOT EXISTS idx_prices_source_ts
    ON market_data.prices (source, ts DESC);

CREATE INDEX IF NOT EXISTS idx_prices_symbol_ts
    ON market_data.prices (symbol_id, ts DESC);

-- ============================================
-- MARKET DATA: Prediction Markets (Polymarket)
-- ============================================
CREATE TABLE IF NOT EXISTS market_data.prediction_markets (
    id              SERIAL PRIMARY KEY,
    condition_id    VARCHAR(128) NOT NULL UNIQUE,
    question        TEXT NOT NULL,
    event_title     VARCHAR(256),
    event_slug      VARCHAR(128),
    category        VARCHAR(64),
    outcome_yes     NUMERIC(10, 6) NOT NULL,
    outcome_no      NUMERIC(10, 6) NOT NULL,
    volume          NUMERIC(20, 4),
    liquidity       NUMERIC(20, 4),
    open_interest   NUMERIC(20, 4),
    active          BOOLEAN NOT NULL DEFAULT true,
    closed          BOOLEAN NOT NULL DEFAULT false,
    end_date        TIMESTAMPTZ,
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prediction_active
    ON market_data.prediction_markets (active, volume DESC);

CREATE TABLE IF NOT EXISTS market_data.prediction_history (
    id              BIGSERIAL,
    market_id       INTEGER NOT NULL REFERENCES market_data.prediction_markets(id),
    outcome_yes     NUMERIC(10, 6) NOT NULL,
    outcome_no      NUMERIC(10, 6) NOT NULL,
    volume          NUMERIC(20, 4),
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (market_id, ts, id)
);

CREATE INDEX IF NOT EXISTS idx_prediction_history_market_ts
    ON market_data.prediction_history (market_id, ts DESC);

-- ============================================
-- MARKET DATA: Orderbook Snapshots
-- ============================================
CREATE TABLE IF NOT EXISTS market_data.orderbook_snapshots (
    id          BIGSERIAL,
    symbol_id   INTEGER NOT NULL REFERENCES core.symbols(id),
    source      VARCHAR(64) NOT NULL,
    bids        JSONB,       -- [{price, size}, ...]
    asks        JSONB,       -- [{price, size}, ...]
    spread      NUMERIC(10, 6),
    mid_price   NUMERIC(20, 8),
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (symbol_id, ts, id)
);

CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_ts
    ON market_data.orderbook_snapshots (symbol_id, ts DESC);

-- ============================================
-- ANALYTICS: Сигналы и алерты
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.signals (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(64) NOT NULL,
    signal_type     VARCHAR(64) NOT NULL,   -- price_anomaly, curve_mispricing, momentum_break
    symbol          VARCHAR(64),
    direction       VARCHAR(8),              -- buy, sell, neutral
    strength        NUMERIC(5, 2),           -- 0.0 to 1.0
    price_at_signal NUMERIC(20, 8),
    target_price    NUMERIC(20, 8),
    reason          TEXT,
    meta            JSONB,
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_ts
    ON analytics.signals (ts DESC);

CREATE INDEX IF NOT EXISTS idx_signals_type
    ON analytics.signals (signal_type, ts DESC);

-- ============================================
-- ANALYTICS: Сделки всех ботов
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.trades (
    id              BIGSERIAL PRIMARY KEY,
    bot_name        VARCHAR(64) NOT NULL,    -- bitget-bot, hyperliquid-bot, polymarket-bot
    symbol          VARCHAR(64) NOT NULL,
    side            VARCHAR(8) NOT NULL,     -- buy, sell
    quantity        NUMERIC(20, 8) NOT NULL,
    price           NUMERIC(20, 8) NOT NULL,
    value_usd       NUMERIC(20, 4),
    fee             NUMERIC(20, 8),
    pnl             NUMERIC(20, 8),
    signal_id       BIGINT REFERENCES analytics.signals(id),
    meta            JSONB,
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_bot_ts
    ON analytics.trades (bot_name, ts DESC);

-- ============================================
-- CORE: Логи работы сборщиков
-- ============================================
CREATE TABLE IF NOT EXISTS core.collector_logs (
    id          BIGSERIAL PRIMARY KEY,
    collector   VARCHAR(64) NOT NULL,
    status      VARCHAR(16) NOT NULL,        -- success, error, timeout
    duration_ms INTEGER,
    items_count INTEGER,
    error_msg   TEXT,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collector_logs_ts
    ON core.collector_logs (collector, ts DESC);

-- ============================================
-- Начальные данные: источники
-- ============================================
INSERT INTO core.data_sources (name, label) VALUES
    ('yahoo', 'Yahoo Finance'),
    ('polymarket', 'Polymarket Prediction Markets'),
    ('bitget', 'Bitget Exchange'),
    ('hyperliquid', 'Hyperliquid DEX')
ON CONFLICT (name) DO NOTHING;