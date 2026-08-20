"""FinAnalytics — модель данных. SQLite, полная схема по файлу август кредит.xlsx."""
import sqlite3, os, logging, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

BASE = Path(__file__).resolve().parent.parent

class FinDB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(BASE / "data" / "finanalytics.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self):
        c = self.conn
        # ─── Пользователи ───
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL CHECK(code IN ('M','B','C')),
            name TEXT, telegram_id INTEGER UNIQUE,
            is_admin INTEGER DEFAULT 0
        )""")
        c.execute("""INSERT OR IGNORE INTO users (id,code,name,is_admin) VALUES
            (1,'M','Муж',0),(2,'B','Виталий',1),(3,'C','Семья',0)""")

        # ─── Кредиты ───
        c.execute("""CREATE TABLE IF NOT EXISTS credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            priority TEXT CHECK(priority IN ('M','B','C')),
            bank_name TEXT NOT NULL,
            monthly_payment REAL,
            amount_paid REAL DEFAULT 0,
            remaining REAL,
            interest_rate REAL,
            debit_date TEXT,
            contract_amount REAL,
            remaining_principal REAL,
            total_overpayment REAL DEFAULT 0,
            debt_start REAL DEFAULT 0,
            debt_end REAL DEFAULT 0,
            term_months INTEGER,
            issue_date TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active','closed','overdue')),
            category TEXT DEFAULT 'consumer',
            note TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""")

        # ─── История платежей по кредитам ───
        c.execute("""CREATE TABLE IF NOT EXISTS credit_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_id INTEGER REFERENCES credits(id),
            amount REAL NOT NULL,
            paid_at TEXT NOT NULL,
            month TEXT NOT NULL,
            is_principal_part REAL,
            is_interest_part REAL,
            note TEXT
        )""")

        # ─── Категории расходов ───
        c.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            monthly_budget REAL DEFAULT 0,
            type TEXT DEFAULT 'expense' CHECK(type IN ('expense','income')),
            icon TEXT DEFAULT '📦',
            sort_order INTEGER DEFAULT 0
        )""")
        # Базовая загрузка категорий
        default_cats = [
            ('Cash','💰',0), ('Гаджеты и техника','📱',1), ('Дом','🏠',2),
            ('Коммуналка','💡',3,500000), ('Красота','💄',4), ('Медицина','🏥',5),
            ('Образование','📚',6), ('Обязательные платежи','📋',7),
            ('Одежда','👕',8), ('Онлайн покупки','🛒',9), ('Питание вне дома','🍕',10),
            ('Подарки','🎁',11), ('Покупки','🛍️',12), ('Продукты для дома','🛒',13),
            ('Путешествия','✈️',14), ('Развлечения','🎮',15), ('Сбережения','💰',16),
            ('Связь и подписки','📡',17), ('Транспорт','🚗',18,500000),
            ('Хобби','🎨',19), ('Корзинка','🧺',20,4000000), ('Обед','🍽️',21,3000000),
            ('Посиделки','🍻',22,1000000), ('Культурные мероприятия','🎭',23,1000000),
            ('Дорожные расходы','🚀',24,1320000), ('Зарплатные платежи','💵',25),
            ('Авансовые платежи','💸',26),
        ]
        for cat in default_cats:
            name, icon, so = cat[0], cat[1], cat[2]
            budget = cat[3] if len(cat) > 3 else 0
            c.execute("INSERT OR IGNORE INTO categories (name,icon,sort_order,monthly_budget) VALUES (?,?,?,?)",
                      (name, icon, so, budget))

        # ─── Источники оплаты (карты/наличные) ───
        c.execute("""CREATE TABLE IF NOT EXISTS payment_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT DEFAULT 'card' CHECK(type IN ('card','cash','credit_card')),
            icon TEXT DEFAULT '💳'
        )""")
        for src in [
            ('TBC','💳','card'), ('InfinCard Black','💳','card'), ('OCTO ЗП','💳','card'),
            ('AVO','💳','card'), ('Cash','💰','cash'), ('Анор кредитные','💳','credit_card'),
        ]:
            c.execute("INSERT OR IGNORE INTO payment_sources (name,icon,type) VALUES (?,?,?)", src)

        # ─── Транзакции (расходы и доходы) ───
        c.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_code TEXT CHECK(user_code IN ('M','B','C')),
            category_id INTEGER REFERENCES categories(id),
            amount REAL NOT NULL,
            payment_source_id INTEGER REFERENCES payment_sources(id),
            type TEXT NOT NULL CHECK(type IN ('expense','income')),
            date TEXT NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_code)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tx_cat ON transactions(category_id)")

        # ─── Доходы (поступления) ───
        c.execute("""CREATE TABLE IF NOT EXISTS income_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_code TEXT CHECK(user_code IN ('M','B','C')),
            type TEXT CHECK(type IN ('salary','advance','exchange','other')),
            amount_uzs REAL,
            amount_usd REAL,
            exchange_rate REAL,
            date TEXT NOT NULL,
            note TEXT
        )""")

        # ─── Платежный календарь ───
        c.execute("""CREATE TABLE IF NOT EXISTS payment_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_id INTEGER REFERENCES credits(id),
            due_day INTEGER NOT NULL,
            due_period TEXT CHECK(due_period IN ('1','10','15','30')),
            amount REAL NOT NULL
        )""")

        # ─── USD цели ───
        c.execute("""CREATE TABLE IF NOT EXISTS usd_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount_usd REAL,
            amount_uzs REAL,
            exchange_rate REAL,
            date TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','done','cancelled'))
        )""")

        # ─── Бюджет (план/факт по месяцам) ───
        c.execute("""CREATE TABLE IF NOT EXISTS monthly_budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            plan_amount REAL DEFAULT 0,
            fact_amount REAL DEFAULT 0,
            UNIQUE(month, category_id)
        )""")

        self.conn.commit()

    # ═══════════════════════════════════════════
    # CREDIT OPERATIONS
    # ═══════════════════════════════════════════

    def add_credit(self, priority, bank, monthly, paid=0, rate=0, debit_date="",
                   contract=0, principal=0, overpayment=0, debt_s=0, debt_e=0,
                   term=0, issue="", category="consumer", note=""):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        uid = {'M':1,'B':2,'C':3}.get(priority, 3)
        remaining = monthly - paid
        c = self.conn.execute(
            """INSERT INTO credits (user_id,priority,bank_name,monthly_payment,amount_paid,remaining,
               interest_rate,debit_date,contract_amount,remaining_principal,total_overpayment,
               debt_start,debt_end,term_months,issue_date,category,note,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid,priority,bank,monthly,paid,remaining,rate,debit_date,contract,principal,
             overpayment,debt_s,debt_e,term,issue,category,note,now,now))
        self.conn.commit()
        return c.lastrowid

    def get_all_credits(self) -> list:
        rows = self.conn.execute("""SELECT c.*, u.code as user_code
            FROM credits c JOIN users u ON c.user_id=u.id
            ORDER BY c.priority, c.bank_name""").fetchall()
        return [dict(r) for r in rows]

    def get_active_credits(self) -> list:
        rows = self.conn.execute("""SELECT c.*, u.code as user_code
            FROM credits c JOIN users u ON c.user_id=u.id
            WHERE c.status='active' ORDER BY c.priority, c.bank_name""").fetchall()
        return [dict(r) for r in rows]

    def get_credit_summary(self) -> dict:
        active = self.get_active_credits()
        total_monthly = sum(c['monthly_payment'] or 0 for c in active)
        total_paid = sum(c['amount_paid'] or 0 for c in active)
        total_remaining = sum(c['remaining'] or 0 for c in active)
        total_contract = sum(c['contract_amount'] or 0 for c in active)
        total_principal = sum(c['remaining_principal'] or 0 for c in active)
        total_overpayment = sum(c['total_overpayment'] or 0 for c in active)
        total_debt = sum(c['debt_end'] or 0 for c in active)
        rates = [c['interest_rate'] for c in active if c['interest_rate'] and c['interest_rate'] > 0]
        avg_rate = sum(rates) / len(rates) if rates else 0
        return {
            'count': len(active),
            'total_monthly': total_monthly,
            'total_paid': total_paid,
            'total_remaining': total_remaining,
            'total_contract': total_contract,
            'total_principal': total_principal,
            'total_overpayment': total_overpayment,
            'total_debt': total_debt,
            'avg_rate': avg_rate,
            'credits': active,
        }

    def record_payment(self, credit_id: int, amount: float, month: str, note=""):
        now = datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO credit_payments (credit_id,amount,paid_at,month,note) VALUES (?,?,?,?,?)",
            (credit_id, amount, now, month, note))
        # Update credit
        self.conn.execute(
            "UPDATE credits SET amount_paid=amount_paid+?, remaining=monthly_payment-amount_paid, updated_at=? WHERE id=?",
            (amount, now, credit_id))
        self.conn.commit()

    def get_payment_calendar(self) -> list:
        """Возвращает платежи, сгруппированные по периодам."""
        credits = self.get_active_credits()
        periods = {'1': [], '10': [], '15': [], '30': []}
        for c in credits:
            dd = (c['debit_date'] or '').strip()
            due = '30'
            if dd.startswith('1'): due = '1'
            elif dd.startswith('10'): due = '10'
            elif dd.startswith('1') and '5' in dd: due = '15'
            elif dd.startswith('2') or dd.startswith('20'): due = '30'
            amount = c['monthly_payment'] or 0
            periods[due].append({'bank': c['bank_name'], 'amount': amount,
                                  'priority': c['priority'], 'credit_id': c['id']})
        return periods

    # ═══════════════════════════════════════════
    # TRANSACTIONS
    # ═══════════════════════════════════════════

    def add_transaction(self, user_code: str, category_name: str, amount: float,
                        source_name: str = "", type: str = 'expense', date: str = None,
                        note: str = ""):
        if date is None:
            date = datetime.now(TASHKENT).strftime('%Y-%m-%d')
        # Resolve category
        cat = self.conn.execute("SELECT id FROM categories WHERE name=?", (category_name,)).fetchone()
        cat_id = cat['id'] if cat else 1
        # Resolve source
        src = None
        if source_name:
            s = self.conn.execute("SELECT id FROM payment_sources WHERE name=?", (source_name,)).fetchone()
            src = s['id'] if s else None
        self.conn.execute(
            "INSERT INTO transactions (user_code,category_id,amount,payment_source_id,type,date,note) VALUES (?,?,?,?,?,?,?)",
            (user_code, cat_id, amount, src, type, date, note))
        self.conn.commit()

    def get_monthly_expenses(self, month: str = None) -> list:
        if month is None:
            month = datetime.now(TASHKENT).strftime('%Y-%m')
        rows = self.conn.execute(
            """SELECT t.*, c.name as cat_name, c.icon as cat_icon, c.monthly_budget,
               p.name as source_name
               FROM transactions t
               LEFT JOIN categories c ON t.category_id=c.id
               LEFT JOIN payment_sources p ON t.payment_source_id=p.id
               WHERE t.type='expense' AND t.date LIKE ?
               ORDER BY t.date DESC""",
            (f'{month}%',)).fetchall()
        return [dict(r) for r in rows]

    def get_monthly_income(self, month: str = None) -> list:
        if month is None:
            month = datetime.now(TASHKENT).strftime('%Y-%m')
        rows = self.conn.execute(
            "SELECT * FROM transactions WHERE type='income' AND date LIKE ? ORDER BY date DESC",
            (f'{month}%',)).fetchall()
        return [dict(r) for r in rows]

    def get_budget_report(self, month: str = None, category: str = None) -> dict:
        if month is None:
            month = datetime.now(TASHKENT).strftime('%Y-%m')
        expenses = self.get_monthly_expenses(month)
        # Filter by category if specified
        if category:
            expenses = [e for e in expenses if e['cat_name'] and category.upper() in e['cat_name'].upper()]
        # Group by category
        cats = {}
        for e in expenses:
            name = e['cat_name'] or 'Без категории'
            if name not in cats:
                cats[name] = {'name': name, 'icon': e['cat_icon'] or '📦',
                              'budget': e['monthly_budget'] or 0, 'fact': 0, 'count': 0}
            cats[name]['fact'] += e['amount']
            cats[name]['count'] += 1
        # Get income entries
        income_entries = self.conn.execute(
            "SELECT * FROM income_entries WHERE date LIKE ?", (f'{month}%',)).fetchall()
        income_total = sum(dict(e)['amount_uzs'] or 0 for e in income_entries)
        # Also get transactions income
        tx_income = self.get_monthly_income(month)
        income_total += sum(t['amount'] for t in tx_income)
        expense_total = sum(e['amount'] for e in expenses)
        return {
            'month': month,
            'categories': list(cats.values()),
            'expense_total': expense_total,
            'income_total': income_total,
            'balance': income_total - expense_total,
        }

    # ═══════════════════════════════════════════
    # INCOME
    # ═══════════════════════════════════════════

    def add_income(self, user_code: str, type: str, amount_uzs: float,
                   amount_usd: float = 0, rate: float = 0, date: str = None, note: str = ""):
        if date is None:
            date = datetime.now(TASHKENT).strftime('%Y-%m-%d')
        self.conn.execute(
            "INSERT INTO income_entries (user_code,type,amount_uzs,amount_usd,exchange_rate,date,note) VALUES (?,?,?,?,?,?,?)",
            (user_code, type, amount_uzs, amount_usd, rate, date, note))
        self.conn.commit()

    # ═══════════════════════════════════════════
    # USD GOALS
    # ═══════════════════════════════════════════

    def add_usd_goal(self, desc: str, amount_usd: float, amount_uzs: float = 0, rate: float = 0):
        date = datetime.now(TASHKENT).strftime('%Y-%m-%d')
        self.conn.execute(
            "INSERT INTO usd_goals (description,amount_usd,amount_uzs,exchange_rate,date) VALUES (?,?,?,?,?)",
            (desc, amount_usd, amount_uzs, rate, date))
        self.conn.commit()

    def get_usd_goals(self) -> list:
        rows = self.conn.execute("SELECT * FROM usd_goals ORDER BY date DESC").fetchall()
        return [dict(r) for r in rows]

    # ═══════════════════════════════════════════
    # IMPORT FROM XLSX
    # ═══════════════════════════════════════════

    def import_credit_data(self):
        """Первичный импорт данных из август кредит.xlsx в БД."""
        existing = self.conn.execute("SELECT COUNT(*) FROM credits").fetchone()[0]
        if existing > 0:
            logger.info(f"Credits already exist ({existing}), skipping import")
            return

        credits_data = [
            # (priority, bank, monthly, paid, rate, debit, contract, principal, overpayment, debt_s, debt_e, term, issue)
            ('M','Учтепа',20000000,0,0,'20 число каждого месяца',429510000,329510000,0,169000000,169000000,22,'2024-12-09'),
            ('M','офб авто',5765000,5765000,19.9,'10 число каждого месяца',215880000,211589751,345900000,340135000,334370000,60,'2024-05-27'),
            ('B','офб',7135000,7135000,20,'10 число каждого месяца',420000000,411500000,1712400000,1705265000,1698130000,240,'2025-09-11'),
            ('B','анорбанк',1125105.5,1125105.5,33,'14 число каждого месяца',25200000,25200000,40199631.31,39074525.81,37949420.31,36,'2025-10-17'),
            ('B','анорбанк',870601.86,870601.86,33,'14 число каждого месяца',21800000,21800000,31341666.96,30471065.1,29600463.24,36,'2025-09-25'),
            ('B','анорбанк',2461582.17,2461582.17,33,'14 число каждого месяца',55000000,55000000,88616958.12,86155375.95,83693793.78,36,'2025-10-01'),
            ('B','анорбанк',2191648.74,2191648.74,33,'14 число каждого месяца',49500000,49500000,78899354.64,76707705.9,74516057.16,36,'2025-09-17'),
            ('B','анорбанк',2165555,2165555,33,'14 число каждого месяца',48500000,48500000,77959980,75794425,73628870,36,'2025-09-22'),
            ('C','даврбанк',163000.89,0,37,'16 число каждого месяца',4432033,4432033,9780053.4,9617052.51,9617052.51,60,'2025-08-31'),
            ('C','даврбанк',161171.01,161171.01,26,'2 число каждого месяца',4000000,3850000,5802156.36,5640985.35,5479814.34,36,''),
            ('C','алокабанк',373000,0,30,'21 число каждого месяца',10100000,10100000,22380000,22007000,22007000,60,'2025-08-20'),
            ('C','алокабанк',661904.44,0,30,'22 число каждого месяца',17800000,17800000,39714266.4,39052361.96,39052361.96,60,'2025-08-22'),
            ('C','алокабанк',370790.24,0,30,'22 число каждого месяца',9700000,9700000,22247414.4,21876624.16,21876624.16,60,'2025-11-02'),
            ('C','алокабанк',444829.89,0,30,'23 число каждого месяца',12000000,12000000,26689793.4,26244963.51,26244963.51,60,'2025-08-23'),
            ('C','миллий банк',1012368.22,908000,26,'10 число каждого месяца',25000000,12110699,36445255.92,35432887.7,34524887.7,36,'2023-08-04'),
        ]
        for d in credits_data:
            self.add_credit(*d)
        logger.info(f"Imported {len(credits_data)} credits")

        # Import income defaults
        income_defaults = [
            ('B','salary',31400000,0,0,'2026-08-01','ЗП'),
            ('B','advance',20900000,0,0,'2026-08-15','Аванс'),
            ('B','salary',5400000,0,0,'2026-08-01','ЗП'),
            ('B','advance',3600000,0,0,'2026-08-15','Аванс'),
            ('B','exchange',0,600,12020,'2026-08-01','Exchange'),
            ('B','exchange',0,500,12000,'2026-08-01','Exchange'),
            ('B','other',0,200,11970,'2026-08-01','Диспансеризация'),
        ]
        for d in income_defaults:
            self.add_income(d[0], d[1], d[2], d[3], d[4], d[5], d[6])
        logger.info(f"Imported {len(income_defaults)} income entries")

        # Import USD goals
        usd_goals = [
            ('Закрытие долга по тбс карте', 600, 0, 12020),
            ('Закрытие долга по тбс карте', 500, 0, 12000),
            ('Диспансеризация и расходы', 200, 0, 11970),
        ]
        for g in usd_goals:
            self.add_usd_goal(*g)
        logger.info(f"Imported {len(usd_goals)} USD goals")
