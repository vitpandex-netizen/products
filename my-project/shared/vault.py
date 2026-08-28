"""Shared vault client — все проекты читают секреты из AES-256-CBC vault."""
import subprocess, os, logging

VAULT_SCRIPT = os.path.expanduser('~/.secure/vault.py')
VAULT_PYTHON = '/usr/bin/python3'

logger = logging.getLogger(__name__)

def get(key: str):
    try:
        r = subprocess.run([VAULT_PYTHON, VAULT_SCRIPT, 'get', key],
                          capture_output=True, text=True, timeout=5)
        val = r.stdout.strip()
        return val if val else None
    except Exception as e:
        logger.error(f'Vault read error ({key}): {e}')
        return None
