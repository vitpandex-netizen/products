#!/usr/bin/env bash
# Secure input for TELEGRAM_API_ID and TELEGRAM_API_HASH.
# - Reads values with stty echo off (not visible in terminal)
# - Writes directly into .env and vault
# - Clears variables from shell memory before exit
# - Nothing is logged or printed to stdout
set -euo pipefail

ENV_FILE="$(dirname "$0")/.env"
VAULT="$(dirname "$0")/vault.sh"

trap 'unset API_ID API_HASH; echo ""; echo "[done] Shell variables cleared."' EXIT

# ── read without echo ─────────────────────────────────────────────────────────
echo "Введите TELEGRAM_API_ID (скрыто, Enter для подтверждения):"
read -rs API_ID
[ -z "$API_ID" ] && { echo "Пусто — прервано." >&2; exit 1; }

echo "Введите TELEGRAM_API_HASH (скрыто, Enter для подтверждения):"
read -rs API_HASH
[ -z "$API_HASH" ] && { echo "Пусто — прервано." >&2; exit 1; }

# ── write into .env (replace empty placeholders) ─────────────────────────────
python3 - "$API_ID" "$API_HASH" "$ENV_FILE" <<'PYEOF'
import sys, re
api_id, api_hash, path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    content = f.read()
content = re.sub(r'TELEGRAM_API_ID=.*', f'TELEGRAM_API_ID={api_id}', content)
content = re.sub(r'TELEGRAM_API_HASH=.*', f'TELEGRAM_API_HASH={api_hash}', content)
with open(path, 'w') as f:
    f.write(content)
PYEOF
chmod 600 "$ENV_FILE"

echo ""
echo "[ok] .env обновлён."

# ── write into vault if initialised ─────────────────────────────────────────
if command -v security &>/dev/null && security find-generic-password -s "transcribe-bot-vault" -a "vault" -w &>/dev/null; then
    "$VAULT" set TELEGRAM_API_ID "$API_ID"
    "$VAULT" set TELEGRAM_API_HASH "$API_HASH"
    echo "[ok] vault обновлён."
else
    echo "[skip] vault не инициализирован — только .env обновлён."
fi

echo ""
echo "Теперь запустите:"
echo "  cd $(dirname "$0") && docker-compose up -d telegram-bot-api"
