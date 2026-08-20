FROM python:3.12-slim

RUN pip install --no-cache-dir fastapi uvicorn jinja2 httpx asyncpg redis pydantic-settings python-multipart orjson

WORKDIR /app

CMD ["uvicorn", "admin.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]