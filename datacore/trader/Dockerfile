FROM python:3.12-slim

RUN pip install --no-cache-dir httpx asyncpg redis eth-account

WORKDIR /app

CMD ["python3", "/app/polymarket_trader.py"]