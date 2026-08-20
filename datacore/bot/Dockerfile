FROM python:3.12-slim

RUN pip install --no-cache-dir httpx asyncpg redis

WORKDIR /app

CMD ["python3", "/app/bot.py", "--schedule"]