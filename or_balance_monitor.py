#!/usr/bin/env python3
"""OpenRouter balance monitor — проверяет баланс и шлёт алерт в Telegram"""
import json, os, subprocess, sys, urllib.request
from pathlib import Path
from datetime import datetime

VAULT = os.path.expanduser('~/.secure/vault.py')
THRESHOLD = 5.0  # алерт если меньше $5
TELEGRAM_CHAT = '-1004297012607'
TELEGRAM_THREAD = '203'  # мониторинг топик

def get_vault(key):
    r = subprocess.run(['/usr/bin/python3', VAULT, 'get', key], capture_output=True, text=True, timeout=5)
    return r.stdout.strip()

def send_telegram(msg):
    token = get_vault('TELEGRAM_BOT_TOKEN')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = json.dumps({
        'chat_id': TELEGRAM_CHAT,
        'text': msg,
        'parse_mode': 'HTML',
        'message_thread_id': int(TELEGRAM_THREAD),
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=10)

def main():
    api_key = get_vault('OPENROUTER_API_KEY')
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/auth/key',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    d = resp['data']
    
    limit = d['limit']
    remaining = d['limit_remaining']
    usage = d['usage_monthly']
    daily = d['usage_daily']
    
    # Save to file for dashboard
    state = {
        'limit': limit,
        'remaining': remaining,
        'usage_monthly': usage,
        'usage_daily': daily,
        'checked_at': datetime.now().isoformat(),
    }
    Path('/tmp/openrouter_balance.json').write_text(json.dumps(state, indent=2))
    
    # Alert if low
    if remaining < THRESHOLD:
        msg = (
            f'⚠️ <b>OpenRouter баланс на исходе</b>\n\n'
            f'Лимит: ${limit}/мес\n'
            f'Осталось: <b>${remaining:.2f}</b>\n'
            f'Использовано: ${usage:.2f}\n'
            f'Сегодня: ${daily:.2f}\n'
            f'Пополни: https://openrouter.ai/settings/credits'
        )
        send_telegram(msg)
        print(f'ALERT: Balance low (${remaining:.2f})')
    else:
        print(f'OK: Balance ${remaining:.2f} (${usage:.2f} used this month)')

if __name__ == '__main__':
    main()