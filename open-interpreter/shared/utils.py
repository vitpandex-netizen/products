"""Shared utilities for all services."""
import json
import sqlite3
import smtplib
import subprocess
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "interp.db"

from shared.db import get_conn, DB_PATH

def notify(service: str, title: str, body: str = "", level: str = "info"):
    """Create notification for Hermes or any messenger."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO notifications (service, title, body, level) VALUES (?, ?, ?, ?)",
        (service, title, body, level)
    )
    conn.commit()
    print(f"[NOTIFY] {service}: {title}")
    return True

def get_config(key: str, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else default

def set_config(key: str, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                 (key, json.dumps(value)))
    conn.commit()
    conn.close()

def send_hermes_message(message: str):
    """Send message to Hermes gateway for Telegram delivery."""
    try:
        import requests
        # Hermes gateway exposes API at localhost with port from config
        resp = requests.post(
            "http://localhost:20128/v1/chat/completions",
            json={
                "model": "hermes-gateway",
                "messages": [{"role": "system", "content": "Send this to user's Telegram"},
                            {"role": "user", "content": message}]
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"[WARN] Failed to send Hermes message: {e}")
        return False

def format_salary(min_s, max_s, curr="RUB"):
    if min_s and max_s:
        return f"{min_s:,.0f} - {max_s:,.0f} {curr}"
    elif min_s:
        return f"от {min_s:,.0f} {curr}"
    elif max_s:
        return f"до {max_s:,.0f} {curr}"
    return "Не указана"
