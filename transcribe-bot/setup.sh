#!/usr/bin/env bash
# First-run setup for transcribe-bot.
# Run once after cloning on a new machine before docker-compose up.
set -euo pipefail

DATA_DIR="/Volumes/External/docker-volumes/transcribe-bot/data"

echo "[setup] Creating data directory..."
mkdir -p "$DATA_DIR"
chmod 700 "$DATA_DIR"

if [ -f "$DATA_DIR/state.json" ]; then
    chmod 600 "$DATA_DIR/state.json"
fi

if [ ! -f .env ]; then
    echo "[setup] ERROR: .env not found. Copy .env.example and fill in real values."
    exit 1
fi

chmod 600 .env
echo "[setup] .env permissions: $(stat -f '%Sp' .env)"

# Verify no secrets have drifted into git
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo "[setup] CRITICAL: .env is tracked by git — remove it immediately!"
    echo "         git rm --cached .env && git commit -m 'remove .env from tracking'"
    exit 1
fi

echo "[setup] Git check OK: .env is not tracked."

# Ensure transcribe-net exists before starting the bot
if ! docker network inspect transcribe-net >/dev/null 2>&1; then
    echo "[setup] Creating docker network transcribe-net..."
    docker network create transcribe-net
fi

echo ""
echo "[setup] Done. Start the bot with:"
echo "  docker-compose up -d --build"
