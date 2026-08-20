"""FinAnalytics Telegram Bot — inline-кнопки, ввод, отчёты, дашборд."""
import logging, os, sys, asyncio, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE.parent))
from shared.vault import get as vault_get
from shared.net import force_ipv4

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

db = None
def _init_db():
    global db
    if db is None:
        from db import FinDB
        db = FinDB()

class FinBot:
    async def _silent_ignore(self, update, ctx): pass
    def __init__(self, token: str, chat_id: str, thread_id: str = None):
        self.token = token
        self.chat_id = chat_id
        self.thread_id = thread_id

    def start(self):
        force_ipv4()
        from telegram.ext import filters as tg_filters
        class TopicFilter(tg_filters.MessageFilter):
            def __init__(self, thread_id):
                super().__init__()
                self.thread_id = int(thread_id) if thread_id else None
            def filter(self, message):
                if self.thread_id is None:
                    return True
                if message.chat.type in ('group', 'supergroup'):
                    return getattr(message, 'message_thread_id', None) == self.thread_id
                return True

        topic = TopicFilter(self.thread_id)
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.cmd_start, filters=topic))
        app.add_handler(CommandHandler("menu", self.cmd_start, filters=topic))
        app.add_handler(CommandHandler("e", self.cmd_expense, filters=topic))
        app.add_handler(CommandHandler("expense", self.cmd_expense, filters=topic))
        app.add_handler(CommandHandler("i", self.cmd_income, filters=topic))
        app.add_handler(CommandHandler("income", self.cmd_income, filters=topic))
        app.add_handler(CommandHandler("debt", self.cmd_debt, filters=topic))
        app.add_handler(CommandHandler("budget", self.cmd_budget, filters=topic))
        app.add_handler(CommandHandler("calendar", self.cmd_calendar, filters=topic))
        app.add_handler(CommandHandler("report", self.cmd_report, filters=topic))
        app.add_handler(CommandHandler("dashboard", self.cmd_dashboard, filters=topic))
        app.add_handler(CommandHandler("help", self.cmd_help, filters=topic))
        app.add_handler(CallbackQueryHandler(self.callback_handler))
        app.add_handler(MessageHandler(topic & ~tg_filters.COMMAND, self._silent_ignore))
        logger.info("FinBot started")
        app.run_polling(drop_pending_updates=True)

    async def cmd_start(self, update: Update, ctx):
        kb = [
            [InlineKeyboardButton("➕ Расход", callback_data="add_expense"),
             InlineKeyboardButton("💵 Доход", callback_data="add_income")],
            [InlineKeyboardButton("📊 Дашборд", callback_data="show_dashboard"),
             InlineKeyboardButton("💰 Долги", callback_data="show_debt")],
            [InlineKeyboardButton("📅 Календарь", callback_data="show_calendar"),
             InlineKeyboardButton("📈 Бюджет", callback_data="show_budget")],
        ]
        await update.message.reply_text(
            "🏦 <b>FinAnalytics</b> — @finanalytics_ai_bot\n\n"
            "Команды:\n"
            "/e сумма категория карта — добавить расход\n"
            "/i сумма тип — добавить доход\n"
            "/debt — сводка по кредитам\n"
            "/budget — план/факт\n"
            "/calendar — платёжный календарь\n"
            "/report — полный отчёт\n"
            "/dashboard — открыть дашборд\n"
            "/help — помощь",
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb)
        )

    async def cmd_help(self, update: Update, ctx):
        await self.cmd_start(update, ctx)

    # ─── Расход ───
    async def cmd_expense(self, update: Update, ctx):
        args = ctx.args
        if len(args) < 2:
            # Show category selection
            _init_db()
            cats = db.conn.execute("SELECT name, icon FROM categories WHERE type='expense' ORDER BY sort_order").fetchall()
            kb = []
            row = []
            for i, c in enumerate(cats):
                row.append(InlineKeyboardButton(f"{c['icon']} {c['name']}", callback_data=f"exp_cat_{c['name']}"))
                if len(row) >= 3:
                    kb.append(row); row = []
            if row: kb.append(row)
            await update.message.reply_text("Выбери категорию расхода:", reply_markup=InlineKeyboardMarkup(kb))
            return
        # Quick parse: /e 50000 продукты tbc
        amount = args[0].replace(' ','').replace(',','.')
        try:
            amount = float(amount)
        except:
            await update.message.reply_text("Ошибка: сумма должна быть числом")
            return
        category = args[1] if len(args) > 1 else ""
        source = args[2] if len(args) > 2 else ""
        _init_db()
        db.add_transaction('B', category, amount, source, 'expense')
        # Get budget status
        budget = db.get_budget_report()
        cat_info = next((c for c in budget['categories'] if c['name'].lower() == category.lower()), None)
        msg = f"✅ Расход {amount:,.0f} сум — {category}"
        if source: msg += f" ({source})"
        if cat_info and cat_info['budget'] > 0:
            pct = (cat_info['fact'] / cat_info['budget']) * 100
            msg += f"\n📊 Бюджет {category}: {cat_info['fact']:,.0f} / {cat_info['budget']:,.0f} сум ({pct:.0f}%)"
        await update.message.reply_text(msg)

    # ─── Доход ───
    async def cmd_income(self, update: Update, ctx):
        args = ctx.args
        if len(args) < 2:
            kb = [
                [InlineKeyboardButton("💵 Зарплата", callback_data="inc_salary"),
                 InlineKeyboardButton("💸 Аванс", callback_data="inc_advance")],
                [InlineKeyboardButton("💱 Exchange", callback_data="inc_exchange"),
                 InlineKeyboardButton("Другое", callback_data="inc_other")],
            ]
            await update.message.reply_text("Тип дохода:", reply_markup=InlineKeyboardMarkup(kb))
            return
        amount = args[0].replace(' ','').replace(',','.')
        try:
            amount = float(amount)
        except:
            await update.message.reply_text("Ошибка: сумма должна быть числом")
            return
        inc_type = args[1] if len(args) > 1 else "other"
        _init_db()
        db.add_income('B', inc_type, amount, note=args[2] if len(args) > 2 else "")
        await update.message.reply_text(f"✅ Доход {amount:,.0f} сум — {inc_type}")

    # ─── Долги ───
    async def cmd_debt(self, update: Update, ctx):
        _init_db()
        summary = db.get_credit_summary()
        lines = [f"💰 <b>Кредиты — {summary['count']} активных</b>\n"]
        lines.append(f"Ежем.платёж: <b>{summary['total_monthly']:,.0f}</b> сум")
        lines.append(f"Оплачено: {summary['total_paid']:,.0f} сум")
        lines.append(f"Остаток к оплате: {summary['total_remaining']:,.0f} сум")
        lines.append(f"Сумма договоров: {summary['total_contract']:,.0f} сум")
        lines.append(f"Остаток долга: {summary['total_principal']:,.0f} сум")
        lines.append(f"Переплата: {summary['total_overpayment']:,.0f} сум")
        lines.append(f"Общий долг: <b>{summary['total_debt']:,.0f}</b> сум")
        lines.append(f"Средняя ставка: {summary['avg_rate']:.1f}%\n")
        # By priority
        for p in ['M','B','C']:
            p_credits = [c for c in summary['credits'] if c['priority'] == p]
            if p_credits:
                total = sum(c['monthly_payment'] or 0 for c in p_credits)
                debt = sum(c['debt_end'] or 0 for c in p_credits)
                lines.append(f"<b>{p}</b> — {total:,.0f} сум/мес | долг {debt:,.0f} сум")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    # ─── Бюджет ───
    async def cmd_budget(self, update: Update, ctx):
            _init_db()
            args = ctx.args or []
            category = ' '.join(args).strip() if args else None
            budget = db.get_budget_report(category=category)
            lines = [f"📈 <b>Бюджет{f' [{category}]' if category else ''} — {budget['month']}</b>\\n"]
            lines.append(f"Поступления: <b>{budget['income_total']:,.0f}</b> сум")
            lines.append(f"Расходы: <b>{budget['expense_total']:,.0f}</b> сум")
            lines.append(f"Баланс: <b>{budget['balance']:+,.0f}</b> сум\\n")
            if not category:
                lines.append("<b>По категориям:</b>")
                for c in sorted(budget['categories'], key=lambda x: x['fact'], reverse=True):
                    if c['fact'] == 0: continue
                    pct = (c['fact'] / c['budget'] * 100) if c['budget'] > 0 else 0
                    bar = '█' * min(int(pct / 10), 10) + '░' * max(10 - min(int(pct / 10), 10), 0)
                    emoji = '🟢' if pct <= 100 else '🔴'
                    lines.append(f"{emoji} {c['icon']} {c['name']}: {c['fact']:,.0f}")
                    if c['budget'] > 0:
                        lines.append(f"   {bar} {pct:.0f}% от {c['budget']:,.0f}")
            else:
                for c in budget['categories']:
                    pct = (c['fact'] / c['budget'] * 100) if c['budget'] > 0 else 0
                    lines.append(f"{c['icon']} {c['name']}: {c['fact']:,.0f} ({pct:.0f}%)")
            await update.message.reply_text('\\n'.join(lines), parse_mode='HTML')

    # ─── Календарь ───
    async def cmd_calendar(self, update: Update, ctx):
        _init_db()
        cal = db.get_payment_calendar()
        lines = [f"📅 <b>Платёжный календарь</b>\n"]
        period_names = {'1': 'До 1-го числа', '10': 'До 10-го числа', '15': 'До 15-го числа', '30': 'До 30-го числа'}
        for period in ['1','10','15','30']:
            payments = cal.get(period, [])
            if payments:
                total = sum(p['amount'] for p in payments)
                lines.append(f"<b>{period_names[period]} — {total:,.0f} сум</b>")
                for p in payments:
                    lines.append(f"  {p['priority']} {p['bank']}: {p['amount']:,.0f} сум")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    # ─── Отчёт ───
    async def cmd_report(self, update: Update, ctx):
        _init_db()
        debt = db.get_credit_summary()
        budget = db.get_budget_report()
        lines = [f"📊 <b>FinAnalytics — {budget['month']}</b>\n"]
        lines.append(f"💰 Долги: {debt['count']} кредитов | {debt['total_monthly']:,.0f} сум/мес")
        lines.append(f"📈 Доходы: {budget['income_total']:,.0f} | Расходы: {budget['expense_total']:,.0f} | Баланс: {budget['balance']:+,.0f}")
        lines.append(f"📅 Общий долг: {debt['total_debt']:,.0f} сум")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    # ─── Dashboard ───
    async def cmd_dashboard(self, update: Update, ctx):
        _init_db()
        # Generate chart
        budget = db.get_budget_report()
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        plt.rcParams['font.family'] = 'DejaVu Sans'
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Pie chart — expenses by category
        cats = sorted(budget['categories'], key=lambda x: x['fact'], reverse=True)
        labels = [f"{c['name']}" for c in cats if c['fact'] > 0]
        sizes = [c['fact'] for c in cats if c['fact'] > 0]
        colors = plt.cm.Pastel1(range(len(labels)))
        if sizes:
            ax1.pie(sizes, labels=labels, autopct='', colors=colors, startangle=90)
            ax1.set_title(f"Расходы {budget['month']}: {budget['expense_total']:,.0f} сум", fontsize=10)

        # Bar chart — budget vs actual
        top = cats[:8]
        names = [c['name'] for c in top]
        facts = [c['fact'] for c in top]
        plans = [c['budget'] for c in top]
        x = range(len(names))
        ax2.bar(x, facts, 0.35, label='Факт', color='#2196F3')
        ax2.bar([i+0.35 for i in x], plans, 0.35, label='План', color='#FF9800', alpha=0.7)
        ax2.set_xticks([i+0.17 for i in x])
        ax2.set_xticklabels(names, rotation=45, ha='right', fontsize=8)
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        ax2.legend(fontsize=8)
        ax2.set_title("Бюджет: план vs факт", fontsize=10)

        plt.tight_layout()
        chart_path = str(BASE / "data" / "chart.png")
        plt.savefig(chart_path, dpi=120, bbox_inches='tight')
        plt.close()

        from telegram import InputFile
        with open(chart_path, 'rb') as f:
            await update.message.reply_photo(InputFile(f, filename='dashboard.png'),
                caption=f"📊 <b>FinAnalytics — {budget['month']}</b>\n"
                        f"Доходы: {budget['income_total']:,.0f} | Расходы: {budget['expense_total']:,.0f} | Баланс: {budget['balance']:+,.0f}",
                parse_mode='HTML')

    # ─── Callbacks ───
    async def callback_handler(self, update: Update, ctx):
        q = update.callback_query
        # Check thread
        if self.thread_id and q.message:
            actual = getattr(q.message, 'message_thread_id', None)
            if actual != int(self.thread_id):
                await q.answer()
                return
        await q.answer()
        data = q.data
        _init_db()

        if data == "show_dashboard":
            await self.cmd_dashboard(update, ctx)
            return
        if data == "show_debt":
            await self.cmd_debt(update, ctx)
            return
        if data == "show_calendar":
            await self.cmd_calendar(update, ctx)
            return
        if data == "show_budget":
            await self.cmd_budget(update, ctx)
            return
        if data.startswith("exp_cat_"):
            cat = data.replace("exp_cat_", "")
            # Show payment sources
            src = db.conn.execute("SELECT name, icon FROM payment_sources").fetchall()
            kb = []
            row = []
            for s in src:
                row.append(InlineKeyboardButton(f"{s['icon']} {s['name']}", callback_data=f"exp_src_{cat}|{s['name']}"))
                if len(row) >= 3:
                    kb.append(row); row = []
            if row: kb.append(row)
            await q.edit_message_text(f"Категория: {cat}\nВыбери карту/источник:", reply_markup=InlineKeyboardMarkup(kb))
            return
        if data.startswith("exp_src_"):
            rest = data.replace("exp_src_", "")
            cat, src = rest.split('|', 1)
            await q.edit_message_text(f"Категория: {cat}\nКарта: {src}\n\nВведи сумму цифрами:\n/e СУММА {cat} {src}")
            return
        if data.startswith("inc_"):
            inc_type = data.replace("inc_", "")
            await q.edit_message_text(f"Введи сумму:\n/i СУММА {inc_type}")
            return

    # ─── Send report (for cron) ───
    def send_report(self, text: str) -> bool:
        import requests
        force_ipv4()
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        if self.thread_id: payload['message_thread_id'] = int(self.thread_id)
        try:
            r = requests.post(url, json=payload, timeout=15)
            return r.status_code == 200
        except: return False
