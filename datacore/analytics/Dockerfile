FROM python:3.12-slim

RUN pip install --no-cache-dir httpx asyncpg redis

WORKDIR /app

ENV PYTHONPATH=/app

# Analytics engine — mounted at /app/analytics/engine.py from host volume
CMD ["python3", "/app/analytics/engine.py"]