"""Telegram-bot stocks-uz."""

import logging, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.vault import get as vault_get
from shared.net import force_ipv4

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

logger = logging.getLogger(__name__)

db = None
def _init_db():
    global db
    if db is None:
        from db import DB
        db = DB()

class StocksUZBot:
    def __init__(self, token, chat_id, thread_id=None):
        self.token = token
        self.chat_id = chat_id
        self.thread_id = thread_id

    def start(self):
        force_ipv4()
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("menu", self.cmd_start))
        app.add_handler(CommandHandler("scan", self.cmd_scan))
        app.add_handler(CommandHandler("ideas", self.cmd_ideas))
        app.add_handler(CommandHandler("portfolio", self.cmd_portfolio))
        app.add_handler(CommandHandler("price", self.cmd_price))
        app.add_handler(CommandHandler("pl", self.cmd_pl))
        app.add_handler(CommandHandler("history", self.cmd_history))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CallbackQueryHandler(self.callback_handler))
        logger.info("Bot started")
        app.run_polling(drop_pending_updates=True)

    async def cmd_start(self, update, ctx):
        kb = [
            [InlineKeyboardButton("Scan now", callback_data="scan_now")],
            [InlineKeyboardButton("Ideas", callback_data="show_ideas"),
             InlineKeyboardButton("Portfolio", callback_data="show_portfolio")],
            [InlineKeyboardButton("P&L", callback_data="show_pl")],
        ]
        await update.message.reply_text(
            "UZSE Stock Agent\n"
            "/scan - scan market\n"
            "/ideas - pending ideas\n"
            "/portfolio - portfolio\n"
            "/price TICKER - price\n"
            "/pl - profit/loss\n"
            "/history - idea history",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    async def cmd_help(self, update, ctx):
        await self.cmd_start(update, ctx)

    async def cmd_scan(self, update, ctx):
        msg = await update.message.reply_text("Scanning UZSE...")
        _init_db()
        try:
            from market import screen_market
            results = screen_market(min_score=40)
            for r in results:
                price = r.get('price', 0) or 0
                score = r.get('score', 50)
                direction = 'buy' if score >= 55 else 'hold'
                target = round(price * 1.1, 2) if direction == 'buy' else None
                stop = round(price * 0.85, 2) if direction == 'buy' else None
                rationale = ', '.join(r.get('signal_detail', [])) or f"Score {score}/100"
                risk = 'low' if score >= 70 else 'medium' if score >= 45 else 'high'
                db.save_idea(r['ticker'], direction, price, target, stop, score, rationale, risk)
            lines = [f"UZSE: {len(results)} candidates\n"]
            for r in results[:9]:
                s = r.get('signals', '') or ''
                lines.append(f"{s} {r['ticker']}: {r.get('price',0):.2f} | {r.get('score',0)}/100")
            await msg.edit_text('\n'.join(lines))
        except Exception as e:
            await msg.edit_text(f"Error: {e}")

    async def cmd_ideas(self, update, ctx):
        _init_db()
        ideas = db.get_pending_ideas()
        if not ideas:
            await update.message.reply_text("No pending ideas")
            return
        for idea in ideas:
            text = f"Idea #{idea['id']}\n{idea['ticker']} {idea['direction'].upper()}\nPrice: {idea['price']:.2f}\nScore: {idea['score']}/100\n{idea['rationale']}"
            kb = [[InlineKeyboardButton("Approve", callback_data=f"approve_{idea['id']}"),
                    InlineKeyboardButton("Reject", callback_data=f"reject_{idea['id']}")]]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

    async def cmd_portfolio(self, update, ctx):
        _init_db()
        s = db.get_portfolio_summary()
        if not s['positions']:
            await update.message.reply_text("Portfolio empty")
            return
        lines = ["Portfolio UZSE\n"]
        for p in s['positions']:
            e = 'G' if p['pl'] >= 0 else 'R'
            lines.append(f"{e} {p['ticker']}: {p['shares']}x{p['current_price']:.2f} = {p['value']:.2f} ({p['pl_pct']:+.2f}%)")
        lines.append(f"\nTotal: {s['total_value']:,.2f} | P&L: {s['total_pl_pct']:+.2f}%")
        await update.message.reply_text('\n'.join(lines))

    async def cmd_price(self, update, ctx):
        if not ctx.args:
            await update.message.reply_text("Usage: /price TICKER")
            return
        from market import analyze_ticker
        a = analyze_ticker(ctx.args[0].upper())
        if a.get('error'):
            await update.message.reply_text(f"Error: {a['error']}")
            return
        await update.message.reply_text(
            f"{a['ticker']}: {a.get('price',0):.2f}\n"
            f"Close: {a.get('closing_price',0):.2f}\n"
            f"Change: {a.get('day_change',0):+.2f}%\n"
            f"Score: {a.get('score',50)}/100"
        )

    async def cmd_pl(self, update, ctx):
        _init_db()
        s = db.get_portfolio_summary()
        if not s['positions']:
            await update.message.reply_text("Portfolio empty")
            return
        lines = ["P&L UZSE\n"]
        for p in s['positions']:
            lines.append(f"{'G' if p['pl']>=0 else 'R'} {p['ticker']}: {p['pl']:+.2f} ({p['pl_pct']:+.2f}%)")
        lines.append(f"\nTotal: {s['total_pl']:+,.2f}")
        await update.message.reply_text('\n'.join(lines))

    async def cmd_history(self, update, ctx):
        _init_db()
        ideas = db.get_idea_history(15)
        if not ideas:
            await update.message.reply_text("No history")
            return
        lines = ["Idea history\n"]
        for i in ideas:
            em = {'approved':'OK','rejected':'XX','pending':'??'}.get(i['status'],'??')
            lines.append(f"{em} #{i['id']} {i['ticker']} {i['direction'].upper()} {i['score']}/100 {i['status']}")
        await update.message.reply_text('\n'.join(lines))

    async def callback_handler(self, update, ctx):
        q = update.callback_query
        await q.answer()
        _init_db()
        d = q.data
        if d == "scan_now":
            from market import screen_market
            results = screen_market(min_score=40)
            for r in results:
                price = r.get('price',0) or 0
                score = r.get('score',50)
                direction = 'buy' if score >= 55 else 'hold'
                target = round(price * 1.1, 2) if direction == 'buy' else None
                stop = round(price * 0.85, 2) if direction == 'buy' else None
                rationale = ', '.join(r.get('signal_detail',[])) or f"Score {score}/100"
                risk = 'low' if score >= 70 else 'medium'
                db.save_idea(r['ticker'], direction, price, target, stop, score, rationale, risk)
            lines = [f"UZSE: {len(results)} candidates\n"]
            for r in results[:9]:
                lines.append(f"{r.get('signals','')} {r['ticker']}: {r.get('price',0):.2f} | {r.get('score',0)}/100")
            await q.edit_message_text('\n'.join(lines))
        elif d.startswith('approve_'):
            db.decide_idea(int(d.split('_')[1]), 'approved')
            await q.edit_message_text(q.message.text + "\n\nAPPROVED")
        elif d.startswith('reject_'):
            db.decide_idea(int(d.split('_')[1]), 'rejected')
            await q.edit_message_text(q.message.text + "\n\nREJECTED")

    def send_report(self, text):
        import requests
        force_ipv4()
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {'chat_id': self.chat_id, 'text': text, 'disable_web_page_preview': True}
        if self.thread_id:
            payload['message_thread_id'] = int(self.thread_id)
        try:
            r = requests.post(url, json=payload, timeout=15)
            return r.status_code == 200
        except:
            return False
