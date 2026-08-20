#!/bin/sh
# Polymarket Trader entrypoint
# Запускает трейдера, опционально с private key
ARGS="--db postgresql://${PG_USER:-datacore}:${PG_PASSWORD:-datacore_secret}@postgres:5432/datacore --interval 300 --max-stake 25"

if [ -n "$POLY_PRIVATE_KEY" ]; then
    exec python3 /app/polymarket_trader.py $ARGS --private-key "$POLY_PRIVATE_KEY"
else
    exec python3 /app/polymarket_trader.py $ARGS
fi