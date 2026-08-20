#!/usr/bin/env bash
# vault.sh — encrypted secrets vault for transcribe-bot
#
# Secrets are stored in secrets.vault (AES-256-CBC via openssl).
# The master password lives in macOS Keychain — set once, used automatically.
#
# Usage:
#   ./vault.sh init              — first-time setup: set master password
#   ./vault.sh set KEY VALUE     — add or update a secret
#   ./vault.sh get KEY           — print one secret value
#   ./vault.sh list              — list all secret keys (values hidden)
#   ./vault.sh env               — print all secrets as KEY=VALUE (for piping)
#   ./vault.sh start             — decrypt → docker-compose up -d, then shred temp file
#   ./vault.sh edit              — open decrypted secrets in $EDITOR, re-encrypt on save

set -euo pipefail

VAULT_FILE="$(dirname "$0")/secrets.vault"
KEYCHAIN_SERVICE="transcribe-bot-vault"
KEYCHAIN_ACCOUNT="vault"

# ── helpers ───────────────────────────────────────────────────────────────────

_get_password() {
    security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null \
        || { echo "ERROR: vault not initialised. Run: ./vault.sh init" >&2; exit 1; }
}

_decrypt() {
    local pass
    pass=$(_get_password)
    openssl enc -aes-256-cbc -d -pbkdf2 -iter 600000 \
        -pass pass:"$pass" -in "$VAULT_FILE" 2>/dev/null \
        || { echo "ERROR: wrong password or corrupt vault" >&2; exit 1; }
}

_encrypt() {
    local pass
    pass=$(_get_password)
    openssl enc -aes-256-cbc -pbkdf2 -iter 600000 \
        -pass pass:"$pass" -out "$VAULT_FILE"
    chmod 600 "$VAULT_FILE"
}

_shred() {
    # Securely wipe a temp file (overwrite + delete)
    local f="$1"
    [ -f "$f" ] || return 0
    dd if=/dev/urandom of="$f" bs=1k count=4 2>/dev/null || true
    rm -f "$f"
}

# ── commands ──────────────────────────────────────────────────────────────────

cmd_init() {
    echo "Setting master password for the vault."
    echo "It will be saved in macOS Keychain under '$KEYCHAIN_SERVICE'."
    echo -n "Choose master password: "
    read -rs PASS; echo
    echo -n "Confirm: "
    read -rs PASS2; echo
    [ "$PASS" = "$PASS2" ] || { echo "Passwords do not match." >&2; exit 1; }
    [ ${#PASS} -ge 12 ] || { echo "Password must be at least 12 characters." >&2; exit 1; }

    security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" \
        -w "$PASS" -U 2>/dev/null \
        && echo "Password saved in Keychain." \
        || { echo "ERROR: could not save to Keychain." >&2; exit 1; }

    if [ ! -f "$VAULT_FILE" ]; then
        echo "{}" | _encrypt
        echo "Vault created: secrets.vault"
    else
        echo "Vault already exists, password updated."
    fi
}

cmd_set() {
    local key="${1:-}" val="${2:-}"
    [ -n "$key" ] || { echo "Usage: vault.sh set KEY VALUE" >&2; exit 1; }
    [ -n "$val" ] || { echo "Usage: vault.sh set KEY VALUE" >&2; exit 1; }

    local json
    json=$(_decrypt)
    json=$(echo "$json" | python3 -c "
import json, sys
d = json.load(sys.stdin)
d['$key'] = '$val'
print(json.dumps(d, indent=2))
")
    echo "$json" | _encrypt
    echo "Set: $key"
}

cmd_get() {
    local key="${1:-}"
    [ -n "$key" ] || { echo "Usage: vault.sh get KEY" >&2; exit 1; }
    _decrypt | python3 -c "
import json, sys
d = json.load(sys.stdin)
val = d.get('$key')
if val is None:
    print('ERROR: key not found: $key', file=sys.stderr)
    sys.exit(1)
print(val)
"
}

cmd_list() {
    echo "Secrets in vault (keys only):"
    _decrypt | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k in sorted(d):
    print(f'  {k}')
"
}

cmd_env() {
    _decrypt | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k, v in d.items():
    print(f'{k}={v}')
"
}

cmd_start() {
    local tmpenv
    tmpenv=$(mktemp /tmp/.vault_env.XXXXXX)
    chmod 600 "$tmpenv"
    trap "_shred '$tmpenv'" EXIT

    cmd_env > "$tmpenv"
    echo "[vault] Secrets decrypted to temp file (will be wiped after start)."

    # Merge vault secrets with .env if it exists (vault takes precedence)
    local compose_dir
    compose_dir="$(dirname "$0")"
    cd "$compose_dir"

    docker-compose --env-file "$tmpenv" up -d --build
    echo "[vault] Container started."
}

cmd_edit() {
    local tmp
    tmp=$(mktemp /tmp/.vault_edit.XXXXXX.json)
    chmod 600 "$tmp"
    trap "_shred '$tmp'" EXIT

    _decrypt > "$tmp"
    "${EDITOR:-nano}" "$tmp"
    # Validate JSON before re-encrypting
    python3 -c "import json; json.load(open('$tmp'))" \
        || { echo "ERROR: invalid JSON — vault NOT updated." >&2; exit 1; }
    _encrypt < "$tmp"
    echo "Vault updated."
}

# ── dispatch ──────────────────────────────────────────────────────────────────

CMD="${1:-}"
shift || true

case "$CMD" in
    init)  cmd_init ;;
    set)   cmd_set "$@" ;;
    get)   cmd_get "$@" ;;
    list)  cmd_list ;;
    env)   cmd_env ;;
    start) cmd_start ;;
    edit)  cmd_edit ;;
    *)
        echo "vault.sh — encrypted secrets manager"
        echo ""
        echo "Commands:"
        echo "  init              First-time setup (creates vault, saves password in Keychain)"
        echo "  set KEY VALUE     Add or update a secret"
        echo "  get KEY           Print one secret value"
        echo "  list              List all secret keys (values hidden)"
        echo "  env               Print all secrets as KEY=VALUE"
        echo "  start             Decrypt + docker-compose up -d (temp file wiped after)"
        echo "  edit              Open decrypted vault in \$EDITOR, re-encrypt on save"
        ;;
esac
