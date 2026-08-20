"""
FinAnalytics — Telegram Bot (PostgreSQL)
"""
import os, sys, logging, asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

import httpx

TASHKENT = timezone(timedelta(hours=5))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("finanalytics-bot")

API_URL = os.getenv("API_URL", "http://api:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "-1004297012607")
THREAD_ID = int(os.getenv("THREAD_ID", "239"))

class FinBot:
    def __init__(self, token: str):
        self.token = token
        self.api = API_URL

    async def _api(self, path: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{self.api}{path}")
            return r.json() if r.status_code == 200 else {}

    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        kb = [
            [InlineKeyboardButton("📊 Дашборд", callback_data="dash"),
             InlineKeyboardButton("💰 Долги", callback_data="debt")],
            [InlineKeyboardButton("📅 Календарь", callback_data="cal"),
             InlineKeyboardButton("📈 Бюджет", callback_data="budget")],
            [InlineKeyboardButton("➕ Расход", callback_data="add_e"),
             InlineKeyboardButton("💵 Доход", callback_data="add_i")],
        ]
        await update.message.reply_text(
            "🏦 <b>FinAnalytics</b>\n\n"
            "Команды:\n/e сумма категория — расход\n/i сумма — доход\n/debt — долги\n"
            "/budget — бюджет\n/calendar — календарь\n/dashboard — дашборд\n/report — отчёт",
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb)
        )

    async def debt(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        data = await self._api("/api/debt")
        lines = [f"💰 <b>Кредиты — {data.get('count',0)} активных</b>\n"]
        lines.append(f"Ежем.платёж: <b>{data.get('total_monthly',0):,.0f}</b> сум")
        lines.append(f"Оплачено: {data.get('total_paid',0):,.0f} сум")
        lines.append(f"Остаток: {data.get('total_remaining',0):,.0f} сум")
        lines.append(f"Общий долг: <b>{data.get('total_debt',0):,.0f}</b> сум")
        lines.append(f"Средняя ставка: {data.get('avg_rate',0):.1f}%")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    async def budget(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        data = await self._api("/api/budget")
        lines = [f"📈 <b>Бюджет — {data.get('month','')}</b>\n"]
        lines.append(f"Поступления: <b>{data.get('income_total',0):,.0f}</b> сум")
        lines.append(f"Расходы: <b>{data.get('expense_total',0):,.0f}</b> сум")
        lines.append(f"Баланс: <b>{data.get('balance',0):+,.0f}</b> сум\n")
        for c in sorted(data.get('categories',[]), key=lambda x: x['fact'], reverse=True):
            if c['fact'] == 0: continue
            pct = (c['fact'] / c['budget'] * 100) if c['budget'] > 0 else 0
            bar = '█' * min(int(pct/10), 10) + '░' * max(10-min(int(pct/10),10), 0)
            emoji = '🟢' if pct <= 100 else '🔴'
            lines.append(f"{emoji} {c['icon']} {c['name']}: {c['fact']:,.0f}")
            if c['budget'] > 0:
                lines.append(f"   {bar} {pct:.0f}% от {c['budget']:,.0f}")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    async def calendar(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        data = await self._api("/api/calendar")
        lines = ["📅 <b>Платёжный календарь</b>\n"]
        periods = {'1': 'До 1-го', '10': 'До 10-го', '15': 'До 15-го', '30': 'До 30-го'}
        for p in ['1','10','15','30']:
            payments = data.get(p, [])
            if payments:
                total = sum(p['amount'] for p in payments)
                lines.append(f"<b>{periods[p]} — {total:,.0f} сум</b>")
                for pym in payments:
                    lines.append(f"  {pym['priority']} {pym['bank']}: {pym['amount']:,.0f} сум")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    async def dashboard(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        data = await self._api("/api/data")
        b = data.get('budget', {})
        d = data.get('debt', {})
        text = (
            f"📊 <b>FinAnalytics — {data.get('month','')}</b>\n\n"
            f"💰 Доходы: {b.get('income_total',0):,.0f} сум\n"
            f"💸 Расходы: {b.get('expense_total',0):,.0f} сум\n"
            f"⚖️ Баланс: {b.get('balance',0):+,.0f} сум\n\n"
            f"📋 Долги: {d.get('count',0)} кредитов\n"
            f"📅 Ежем.платёж: {d.get('total_monthly',0):,.0f} сум\n"
            f"⚠️ Общий долг: {d.get('total_debt',0):,.0f} сум"
        )
        await update.message.reply_text(text, parse_mode='HTML')

    async def report(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        b = await self._api("/api/budget")
        d = await self._api("/api/debt")
        text = (
            f"📊 <b>FinAnalytics — Отчёт</b>\n\n"
            f"💰 Долги: {d.get('count',0)} кредитов | {d.get('total_monthly',0):,.0f} сум/мес\n"
            f"📈 Доходы: {b.get('income_total',0):,.0f} | "
            f"Расходы: {b.get('expense_total',0):,.0f} | "
            f"Баланс: {b.get('balance',0):+,.0f}\n"
            f"📅 Общий долг: {d.get('total_debt',0):,.0f} сум"
        )
        await update.message.reply_text(text, parse_mode='HTML')

    async def callback(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        cmd = q.data
        if cmd == "dash": await self.dashboard(q, ctx)
        elif cmd == "debt": await self.debt(q, ctx)
        elif cmd == "cal": await self.calendar(q, ctx)
        elif cmd == "budget": await self.budget(q, ctx)
        elif cmd == "add_e": await q.message.reply_text("Формат: /e 50000 продукты")
        elif cmd == "add_i": await q.message.reply_text("Формат: /i 10000000")

    def run(self):
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("menu", self.start))
        app.add_handler(CommandHandler("debt", self.debt))
        app.add_handler(CommandHandler("budget", self.budget))
        app.add_handler(CommandHandler("calendar", self.calendar))
        app.add_handler(CommandHandler("dashboard", self.dashboard))
        app.add_handler(CommandHandler("report", self.report))
        app.add_handler(CallbackQueryHandler(self.callback))
        logger.info("FinBot started")
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    token = BOT_TOKEN or os.getenv("FINANALYTICS_BOT_TOKEN", "")
    if not token:
        logger.error("BOT_TOKEN not set")
        sys.exit(1)
    FinBot(token).run()