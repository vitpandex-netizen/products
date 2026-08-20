"""
FinAnalytics — API Core (PostgreSQL + Redis)
Запуск: python main.py
"""
import os, sys, json, logging, asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

import asyncpg
import redis.asyncio as redis

TASHKENT = timezone(timedelta(hours=5))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("finanalytics-api")

# ─── Config ───
DB_DSN = os.getenv("DATABASE_URL", "postgresql://finanalytics:finanalytics_pass@100.84.223.96:5432/finanalytics")
REDIS_URL = os.getenv("REDIS_URL", "redis://100.84.223.96:6379/1")
API_PORT = int(os.getenv("API_PORT", 8000))

class FinDB:
    """PostgreSQL адаптер — вместо sqlite3"""
    def __init__(self, dsn: str = DB_DSN):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=5)
        await self._ensure_tables()
        logger.info("PostgreSQL connected")

    async def _ensure_tables(self):
        async with self.pool.acquire() as c:
            await c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL CHECK(code IN ('M','B','C')),
                    name TEXT, telegram_id BIGINT UNIQUE,
                    is_admin INTEGER DEFAULT 0
                );
                INSERT INTO users (code,name,is_admin) VALUES
                    ('M','Муж',0),('B','Виталий',1),('C','Семья',0)
                ON CONFLICT (code) DO NOTHING;
            """)
            await c.execute("""
                CREATE TABLE IF NOT EXISTS credits (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    priority TEXT CHECK(priority IN ('M','B','C')),
                    bank_name TEXT NOT NULL,
                    monthly_payment REAL DEFAULT 0,
                    amount_paid REAL DEFAULT 0,
                    remaining REAL DEFAULT 0,
                    interest_rate REAL DEFAULT 0,
                    debit_date TEXT,
                    contract_amount REAL DEFAULT 0,
                    remaining_principal REAL DEFAULT 0,
                    total_overpayment REAL DEFAULT 0,
                    debt_start REAL DEFAULT 0,
                    debt_end REAL DEFAULT 0,
                    term_months INTEGER DEFAULT 0,
                    issue_date TEXT,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active','closed','overdue')),
                    category TEXT DEFAULT 'consumer',
                    note TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            await c.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    monthly_budget REAL DEFAULT 0,
                    type TEXT DEFAULT 'expense' CHECK(type IN ('expense','income')),
                    icon TEXT DEFAULT '📦',
                    sort_order INTEGER DEFAULT 0
                );
            """)
            await c.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_code TEXT CHECK(user_code IN ('M','B','C')),
                    category_id INTEGER REFERENCES categories(id),
                    amount REAL NOT NULL,
                    payment_source TEXT,
                    type TEXT NOT NULL CHECK(type IN ('expense','income')),
                    date DATE NOT NULL,
                    note TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            await c.execute("""
                CREATE TABLE IF NOT EXISTS payment_calendar (
                    id SERIAL PRIMARY KEY,
                    credit_id INTEGER REFERENCES credits(id),
                    due_day INTEGER NOT NULL,
                    due_period TEXT CHECK(due_period IN ('1','10','15','30')),
                    amount REAL NOT NULL
                );
            """)
            await c.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    credit_id INTEGER REFERENCES credits(id),
                    days_before INTEGER DEFAULT 3,
                    enabled BOOLEAN DEFAULT TRUE,
                    last_sent DATE
                );
            """)
            # Default categories
            defaults = [
                ('Cash','💰',0,0), ('Гаджеты и техника','📱',1,0),
                ('Дом','🏠',2,0), ('Коммуналка','💡',3,500000),
                ('Красота','💄',4,0), ('Медицина','🏥',5,0),
                ('Образование','📚',6,0), ('Обязательные платежи','📋',7,0),
                ('Одежда','👕',8,0), ('Онлайн покупки','🛒',9,0),
                ('Питание вне дома','🍕',10,0), ('Подарки','🎁',11,0),
                ('Покупки','🛍️',12,0), ('Продукты для дома','🛒',13,0),
                ('Путешествия','✈️',14,0), ('Развлечения','🎮',15,0),
                ('Сбережения','💰',16,0), ('Связь и подписки','📡',17,0),
                ('Транспорт','🚗',18,500000), ('Хобби','🎨',19,0),
                ('Корзинка','🧺',20,4000000), ('Обед','🍽️',21,3000000),
                ('Посиделки','🍻',22,1000000), ('Культурные мероприятия','🎭',23,1000000),
                ('Дорожные расходы','🚀',24,1320000),
            ]
            for name, icon, so, budget in defaults:
                await c.execute(
                    "INSERT INTO categories (name,icon,sort_order,monthly_budget) VALUES ($1,$2,$3,$4) ON CONFLICT (name) DO NOTHING",
                    name, icon, so, budget
                )
            await c.execute("CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date)")
            await c.execute("CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_code)")

    # ─── Credits ───
    async def get_credit_summary(self) -> dict:
        async with self.pool.acquire() as c:
            rows = await c.fetch("SELECT * FROM credits WHERE status='active' ORDER BY priority, bank_name")
            total_monthly = sum(r['monthly_payment'] or 0 for r in rows)
            total_paid = sum(r['amount_paid'] or 0 for r in rows)
            total_remaining = sum(r['remaining'] or 0 for r in rows)
            total_contract = sum(r['contract_amount'] or 0 for r in rows)
            total_principal = sum(r['remaining_principal'] or 0 for r in rows)
            total_overpayment = sum(r['total_overpayment'] or 0 for r in rows)
            total_debt = sum(r['debt_end'] or 0 for r in rows)
            rates = [r['interest_rate'] for r in rows if r['interest_rate'] and r['interest_rate'] > 0]
            avg_rate = sum(rates) / len(rates) if rates else 0
            return {
                'count': len(rows), 'total_monthly': total_monthly, 'total_paid': total_paid,
                'total_remaining': total_remaining, 'total_contract': total_contract,
                'total_principal': total_principal, 'total_overpayment': total_overpayment,
                'total_debt': total_debt, 'avg_rate': avg_rate,
                'credits': [dict(r) for r in rows],
            }

    async def get_payment_calendar(self) -> dict:
        async with self.pool.acquire() as c:
            rows = await c.fetch("SELECT * FROM credits WHERE status='active'")
            periods = {'1': [], '10': [], '15': [], '30': []}
            for r in rows:
                dd = (r['debit_date'] or '').strip()
                due = '30'
                if dd.startswith('1'): due = '1'
                elif dd.startswith('10'): due = '10'
                elif dd.startswith('1') and '5' in dd: due = '15'
                elif dd.startswith('2') or dd.startswith('20'): due = '30'
                periods[due].append({
                    'bank': r['bank_name'], 'amount': r['monthly_payment'] or 0,
                    'priority': r['priority'], 'credit_id': r['id']
                })
            return periods

    async def get_budget_report(self, month: str = None, category: str = None) -> dict:
        if month is None:
            month = datetime.now(TASHKENT).strftime('%Y-%m')
        async with self.pool.acquire() as c:
            cats = await c.fetch("SELECT * FROM categories ORDER BY sort_order")
            # Income
            income = await c.fetchval(
                "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND to_char(date,'YYYY-MM')=$1", month
            )
            # Expenses
            expense = await c.fetchval(
                "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND to_char(date,'YYYY-MM')=$1", month
            )
            cat_data = []
            for cat in cats:
                fact = await c.fetchval(
                    "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE category_id=$1 AND type='expense' AND to_char(date,'YYYY-MM')=$2",
                    cat['id'], month
                )
                cat_data.append({
                    'name': cat['name'], 'icon': cat['icon'],
                    'budget': cat['monthly_budget'] or 0,
                    'fact': fact,
                })
            return {
                'month': month, 'income_total': income, 'expense_total': expense,
                'balance': income - expense, 'categories': cat_data,
            }

    async def add_transaction(self, user_code, category_name, amount, source="", type='expense', date=None, note=""):
        if date is None:
            date = datetime.now(TASHKENT).strftime('%Y-%m-%d')
        async with self.pool.acquire() as c:
            cat = await c.fetchval("SELECT id FROM categories WHERE name=$1", category_name)
            cat_id = cat or 1
            await c.execute(
                "INSERT INTO transactions (user_code,category_id,amount,payment_source,type,date,note) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                user_code, cat_id, amount, source, type, date, note
            )

    async def add_income(self, user_code, inc_type, amount, note=""):
        date = datetime.now(TASHKENT).strftime('%Y-%m-%d')
        async with self.pool.acquire() as c:
            cat = await c.fetchval("SELECT id FROM categories WHERE name='Зарплатные платежи'")
            await c.execute(
                "INSERT INTO transactions (user_code,category_id,amount,payment_source,type,date,note) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                user_code, cat or 1, amount, '', 'income', date, note
            )

    async def get_reminders(self) -> list:
        """Проверка: какие напоминания нужно отправить сегодня"""
        async with self.pool.acquire() as c:
            rows = await c.fetch("""
                SELECT r.*, c.bank_name, c.monthly_payment, c.debit_date, c.priority
                FROM reminders r JOIN credits c ON r.credit_id=c.id
                WHERE r.enabled=TRUE AND c.status='active'
            """)
            today = datetime.now(TASHKENT).date()
            results = []
            for r in rows:
                dd = (r['debit_date'] or '').strip()
                day = 1
                if dd.startswith('10'): day = 10
                elif dd.startswith('1') and '5' in dd: day = 15
                elif dd.startswith('2') or dd.startswith('20'): day = 30
                elif dd.startswith('1'): day = 1
                remind_day = day - (r['days_before'] or 3)
                if remind_day <= 0:
                    remind_day += 30  # прошлый месяц
                if today.day == remind_day and (r['last_sent'] is None or r['last_sent'] < today):
                    results.append(dict(r))
                    await c.execute("UPDATE reminders SET last_sent=$1 WHERE id=$2", today, r['id'])
            return results

    async def close(self):
        if self.pool:
            await self.pool.close()


# ─── HTTP API (Flask-like через aiohttp или uvicorn) ───
# Используем FastAPI/uvicorn для простоты
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="FinAnalytics API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

db: Optional[FinDB] = None
r: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup():
    global db, r
    db = FinDB()
    await db.connect()
    r = redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("API ready on :%d", API_PORT)

@app.on_event("shutdown")
async def shutdown():
    if db: await db.close()
    if r: await r.aclose()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "finanalytics-api"}

@app.get("/api/data")
async def api_data():
    budget = await db.get_budget_report()
    debt = await db.get_credit_summary()
    cal = await db.get_payment_calendar()
    return {"budget": budget, "debt": debt, "calendar": cal, "month": datetime.now(TASHKENT).strftime('%B %Y')}

@app.get("/api/debt")
async def api_debt():
    return await db.get_credit_summary()

@app.get("/api/budget")
async def api_budget(month: str = None, category: str = None):
    return await db.get_budget_report(month=month, category=category)

@app.get("/api/calendar")
async def api_calendar():
    return await db.get_payment_calendar()

@app.get("/api/analytics")
async def api_analytics():
    budget = await db.get_budget_report()
    debt = await db.get_credit_summary()
    now = datetime.now(TASHKENT)
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    prev = await db.get_budget_report(month=last_month)

    insights = []
    diff = 0
    if prev and prev.get('expense_total', 0) > 0:
        diff = budget['expense_total'] - prev['expense_total']
        pct = (diff / prev['expense_total']) * 100
        if pct > 10: insights.append(f"🔴 Расходы выросли на {pct:.0f}% vs прошлый месяц")
        elif pct < -10: insights.append(f"🟢 Расходы снизились на {abs(pct):.0f}% vs прошлый месяц")
        else: insights.append(f"⚪ Расходы стабильны ({pct:+.0f}%)")

    for c in budget['categories']:
        if c['budget'] > 0 and c['fact'] > c['budget'] * 1.2:
            insights.append(f"🔴 {c['name']}: превышение на {((c['fact']/c['budget'])-1)*100:.0f}%")

    if budget['income_total'] > 0:
        dti = (debt['total_monthly'] / budget['income_total']) * 100
        if dti > 40: insights.append(f"🔴 Критическая долговая нагрузка: {dti:.0f}% от дохода")
        elif dti > 25: insights.append(f"🟡 Высокая долговая нагрузка: {dti:.0f}%")

    return {
        "month": now.strftime('%B %Y'),
        "insights": insights,
        "expense_trend": {
            "current": budget['expense_total'],
            "previous": prev.get('expense_total', 0) if prev else 0,
            "diff": diff,
        },
        "debt_metrics": {
            "total": debt['total_debt'], "monthly": debt['total_monthly'],
            "avg_rate": debt['avg_rate'], "count": debt['count'],
        }
    }

@app.post("/api/expense")
async def api_expense(user_code: str = "B", category: str = "", amount: float = 0, source: str = "", note: str = ""):
    await db.add_transaction(user_code, category, amount, source, 'expense', note=note)
    return {"status": "ok", "amount": amount, "category": category}

@app.post("/api/income")
async def api_income(user_code: str = "B", amount: float = 0, inc_type: str = "other", note: str = ""):
    await db.add_income(user_code, inc_type, amount, note=note)
    return {"status": "ok", "amount": amount, "type": inc_type}

@app.get("/api/reminders")
async def api_reminders():
    return await db.get_reminders()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)