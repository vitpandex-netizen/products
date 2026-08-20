"""Database module using SQLite for all services."""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "interp.db"

def get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        title TEXT NOT NULL,
        company TEXT,
        url TEXT,
        skills TEXT,
        salary_min REAL,
        salary_max REAL,
        currency TEXT DEFAULT 'RUB',
        location TEXT,
        matched INTEGER DEFAULT 0,
        applied INTEGER DEFAULT 0,
        seen INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(service, url)
    );

    CREATE TABLE IF NOT EXISTS stock_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        exchange TEXT NOT NULL,
        price REAL NOT NULL,
        signal TEXT NOT NULL,
        reason TEXT,
        metadata TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT,
        url TEXT,
        category TEXT,
        impact TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(source, url)
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        account TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT,
        level TEXT DEFAULT 'info',
        sent INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS ai_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        skill_level TEXT,
        demand_score REAL,
        source TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    init_db()
    print(f"DB initialized at {DB_PATH}")
