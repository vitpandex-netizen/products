#!/usr/bin/env python3
"""Entrypoint — запускает бота из корня проекта, читает секреты из vault"""
import sys, os, subprocess, logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force IPv4 для Telegram API (на macOS DNS выдаёт AAAA без маршрута)
import socket
# Устанавливаем socket.AF_INET как предпочтительный
original_getaddrinfo = socket.getaddrinfo
def _force_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _force_ipv4

from src.bot.market_bot import MarketBot

def vault(key):
    try:
        r = subprocess.run(
            ['/usr/bin/python3', os.path.expanduser('~/.secure/vault.py'), 'get', key],
            capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip()
    except Exception as e:
        logging.error(f"Vault read error ({key}): {e}")
        return None

# Пробуем vault, затем .env, затем config.json (fallback)
token = (vault('UZ_MARKET_TELEGRAM_TOKEN')
         or os.environ.get('UZ_MARKET_TELEGRAM_TOKEN'))
openrouter_key = (vault('OPENROUTER_API_KEY')
                  or os.environ.get('OPENROUTER_API_KEY'))
chat_id = (vault('UZ_MARKET_CHAT_ID')
           or os.environ.get('UZ_MARKET_CHAT_ID', '-1004297012607'))
thread_id = (vault('UZ_MARKET_THREAD_ID')
             or os.environ.get('UZ_MARKET_THREAD_ID', '251'))

if not token or not openrouter_key:
    logging.error("❌ Secrets not found in vault or env")
    sys.exit(1)

config = {
    "telegram_token": token,
    "openrouter_key": openrouter_key,
    "telegram_chat_id": chat_id,
    "telegram_thread_id": int(thread_id) if thread_id and thread_id != '__VAULT__' else None,
}

bot = MarketBot(
    token=token,
    openrouter_key=openrouter_key,
    config=config,
)
bot.run()
