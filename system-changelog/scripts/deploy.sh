#!/usr/bin/env bash
# Deploy: System Change Log + DataCore Query Agent
# Запускать с Mac: bash deploy.sh

set -euo pipefail

US="us@100.84.223.96"
# Цвета
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; exit 1; }

# 1. Создаём директории на US Server
info "Creating directories on US Server..."
ssh "$US" "mkdir -p ~/services/system-changelog/app ~/services/system-changelog/data"
ssh "$US" "mkdir -p ~/services/datacore-query-agent/app ~/services/datacore-query-agent/scripts"

# 2. Копируем файлы System Change Log
info "Copying System Change Log..."
scp -r /Users/vitaliyr/dev/system-changelog/app/* "$US:~/services/system-changelog/app/"
scp /Users/vitaliyr/dev/system-changelog/requirements.txt "$US:~/services/system-changelog/"
scp /Users/vitaliyr/dev/system-changelog/Dockerfile "$US:~/services/system-changelog/"

# 3. Копируем файлы DataCore Query Agent
info "Copying DataCore Query Agent..."
scp -r /Users/vitaliyr/dev/datacore/query-agent/app/* "$US:~/services/datacore-query-agent/app/"
scp /Users/vitaliyr/dev/datacore/query-agent/requirements.txt "$US:~/services/datacore-query-agent/"
scp /Users/vitaliyr/dev/datacore/query-agent/Dockerfile "$US:~/services/datacore-query-agent/"

# 4. Создаём docker-compose для новых сервисов
info "Creating docker-compose on US Server..."
ssh "$US" 'cat > ~/services/docker-compose.new.yml << '"'"'DOCKERCOMPOSE'"'"'
version: "3.8"

services:
  changelog:
    build: ./system-changelog
    container_name: system-changelog
    ports:
      - "8300:8300"
    environment:
      - MESSAGE_BUS_URL=http://100.84.223.96:8200
    volumes:
      - ./system-changelog/data:/app/data
    restart: unless-stopped
    networks:
      - datacore-net

  query-agent:
    build: ./datacore-query-agent
    container_name: datacore-query-agent
    ports:
      - "8400:8400"
    environment:
      - DATACORE_DATABASE_URL=postgresql://datacore_reader:reader_pass@postgres:5432/datacore
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - QUERY_MODEL=qwen/qwen3.7-flash
      - QUERY_PRO_MODEL=deepseek/deepseek-v4-pro-0813
      - QUERY_TIMEOUT_SECONDS=30
      - QUERY_MAX_ROWS=500
    restart: unless-stopped
    networks:
      - datacore-net

networks:
  datacore-net:
    external: true
DOCKERCOMPOSE
'

# 5. Создаём read-only пользователя в PostgreSQL DataCore
info "Creating read-only PostgreSQL user..."
ssh "$US" 'docker exec datacore-pg psql -U datacore -d datacore -c "
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '\''datacore_reader'\'') THEN
      CREATE ROLE datacore_reader WITH LOGIN PASSWORD '\''reader_pass'\'' NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
  END
  \$\$;
  GRANT CONNECT ON DATABASE datacore TO datacore_reader;
  GRANT USAGE ON SCHEMA public TO datacore_reader;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO datacore_reader;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO datacore_reader;
" 2>&1'

# 6. Обновляем Caddy gateway (datacore-gateway)
info "Updating Caddy config..."
ssh "$US" 'cat > ~/datacore/gateway/Caddyfile << '"'"'CADDYCONF'"'"'
{
  admin off
  log {
    output file /data/access.log
    level info
  }
}

:80 {
  @health {
    path /health
  }
  handle @health {
    respond `{"status":"ok","services":["core-api","admin","query-agent","changelog","redis","postgres","collector-pm","collector-yh","collector-bg","collector-news","analytics","trader-pm","bot"]}` 200 {
      header Content-Type application/json
    }
  }

  # Core API
  handle_path /api/v1/* {
    reverse_proxy core-api:8000 {
      health_uri /health
      health_interval 30s
      health_timeout 3s
    }
  }

  # Query Agent (Tool Calling)
  handle_path /query/* {
    reverse_proxy query-agent:8400 {
      health_uri /health
      health_interval 30s
    }
  }

  # Change Log
  handle_path /changelog/* {
    reverse_proxy changelog:8300 {
      health_uri /health
      health_interval 30s
    }
  }

  # Admin UI
  handle_path /admin/* {
    reverse_proxy admin:8080 {
      health_uri /health
      health_interval 30s
    }
  }

  handle {
    reverse_proxy admin:8080
  }
}

:9090 {
  handle /metrics {
    reverse_proxy node-exporter:9100
  }
}
CADDYCONF
'

# 7. Собираем и запускаем
info "Building and starting containers..."
ssh "$US" "cd ~/services && docker compose -f docker-compose.new.yml build --no-cache 2>&1 | tail -10"
ssh "$US" "cd ~/services && docker compose -f docker-compose.new.yml up -d 2>&1"

# 8. Ждём запуска
info "Waiting for containers to start..."
sleep 5
ssh "$US" "docker ps --filter name='system-changelog|datacore-query-agent' --format 'table {{.Names}}\t{{.Status}}'"

# 9. Рестарт Caddy gateway
info "Restarting Caddy gateway..."
ssh "$US" "docker compose -f ~/datacore/docker-compose.yml restart gateway 2>&1 || docker restart datacore-gateway 2>&1"

# 10. Проверка
info "=== Health checks ==="
sleep 3
echo "--- Change Log ---"
curl -s http://100.84.223.96:8300/health 2>&1 || echo "FAILED"
echo ""
echo "--- Query Agent ---"
curl -s http://100.84.223.96:8400/health 2>&1 || echo "FAILED"
echo ""
echo "--- Gateway: Change Log ---"
curl -s http://100.84.223.96:8083/changelog/health 2>&1 || echo "FAILED"
echo ""

info "=== Deploy complete! ==="
echo ""
echo "System Change Log:  http://100.84.223.96:8300"
echo "  - POST /changes    (create entry)"
echo "  - GET /changes     (list entries)"
echo "  - GET /health      (health check)"
echo "  - Gateway: :8083/changelog/*"
echo ""
echo "DataCore Query Agent:  http://100.84.223.96:8400"
echo "  - POST /describe   (schema)  "
echo "  - POST /execute    (SQL)     "
echo "  - POST /query      (NL query)"
echo "  - GET /health      (health)  "
echo "  - Gateway: :8083/query/*"
echo ""
echo "CLI:"
echo "  python3 ~/dev/system-changelog/scripts/cli.py -a hermes -p infra -t deploy -s '...' -r '...'"