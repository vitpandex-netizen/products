"""Config — секреты из vault. Если vault недоступен -> .env fallback."""
import os, logging
from pathlib import Path
from dotenv import load_dotenv

_BASE = Path(__file__).resolve().parent.parent
load_dotenv(_BASE / '.env')

logger = logging.getLogger(__name__)

# Vault — читает из ~/.secure/vault.py
def _vault_get(key: str) -> str | None:
    import subprocess
    try:
        r = subprocess.run(
            ['/usr/bin/python3', os.path.expanduser('~/.secure/vault.py'), 'get', key],
            capture_output=True, text=True, timeout=5
        )
        val = r.stdout.strip()
        return val if val else None
    except Exception:
        return None

def get(key: str, default: str = "") -> str:
    # 1. Vault
    val = _vault_get(key)
    if val:
        return val
    # 2. .env fallback
    val = os.getenv(key)
    if val:
        return val
    return default

# Pre-defined keys
TELEGRAM_BOT_TOKEN = lambda: get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = lambda: get("TELEGRAM_CHAT_ID", "-1004297012607")
TELEGRAM_THREAD_ID = lambda: get("TELEGRAM_THREAD_ID", "127")
OPENROUTER_API_KEY = lambda: get("OPENROUTER_API_KEY")
