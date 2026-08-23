FROM python:3.12-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir beautifulsoup4 lxml

# Код
COPY . .

# Здоровье — для core сервиса проверяется через API /api/v1/health
# Для collector healthcheck не нужен (worker без HTTP)

EXPOSE 8005

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8005"]