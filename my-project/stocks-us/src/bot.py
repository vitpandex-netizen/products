"""Telegram-бот stocks-us — команды, апрув, ручной запуск, дашборд."""
import logging, asyncio, os, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.vault import get as vault_get
from shared.net import force_ipv4

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

db = None
def _init_db():
    global db
    if db is None:
        from db import DB
        db = DB()

class StocksBot:
    def __init__(self, token: str, chat_id: str, thread_id: Optional[str] = None):
        self.token = token
        self.chat_id = chat_id
        self.thread_id = thread_id
        self.app = None

    def start(self):
        force_ipv4()
        self.app = Application.builder().token(self.token).build()
        # Thread filter — отвечаем только на сообщения из своего топика
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
        self.app.add_handler(CommandHandler("start", self.cmd_start, filters=topic))
        self.app.add_handler(CommandHandler("menu", self.cmd_start, filters=topic))
        self.app.add_handler(CommandHandler("scan", self.cmd_scan, filters=topic))
        self.app.add_handler(CommandHandler("ideas", self.cmd_ideas, filters=topic))
        self.app.add_handler(CommandHandler("portfolio", self.cmd_portfolio, filters=topic))
        self.app.add_handler(CommandHandler("price", self.cmd_price, filters=topic))
        self.app.add_handler(CommandHandler("pl", self.cmd_pl, filters=topic))
        self.app.add_handler(CommandHandler("dca", self.cmd_dca, filters=topic))
        self.app.add_handler(CommandHandler("history", self.cmd_history, filters=topic))
        self.app.add_handler(CommandHandler("help", self.cmd_help, filters=topic))
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))
        # Also add a topic filter for all messages (prevents responding to wrong topic)
        self.app.add_handler(MessageHandler(topic & ~tg_filters.COMMAND, self._silent_ignore))
        logger.info("🤖 Stocks-US bot polling started")
        self.app.run_polling(drop_pending_updates=True)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🔍 Сканировать рынок сейчас", callback_data="scan_now")],
            [InlineKeyboardButton("💡 Идеи на апрув", callback_data="show_ideas"),
             InlineKeyboardButton("📊 Портфель", callback_data="show_portfolio")],
            [InlineKeyboardButton("💰 P&L", callback_data="show_pl"),
             InlineKeyboardButton("📅 DCA", callback_data="show_dca")],
        ]
        await update.message.reply_text(
            "📈 <b>Stocks-US Agent</b> — умный помощник по рынку США\n\n"
            "Команды:\n"
            "/scan — запустить скрининг рынка сейчас\n"
            "/ideas — посмотреть идеи на апрув\n"
            "/portfolio — портфель и P&L\n"
            "/price TICKER — цена и анализ\n"
            "/pl — прибыль/убыток\n"
            "/dca — DCA расписание\n"
            "/history — история идей\n"
            "/help — помощь",
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.cmd_start(update, context)

    # ─── Сканирование рынка ───
    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = await update.message.reply_text("🔍 <b>Запускаю скрининг рынка...</b>\nЭто займёт 1–2 минуты", parse_mode='HTML')
        asyncio.create_task(self._run_scan(update, msg))

    async def _run_scan(self, update: Update, status_msg):
        from market import screen_market
        try:
            results = screen_market(min_score=55)
            if not results:
                await status_msg.edit_text("🔍 Скрининг завершён. Ничего не найдено (все ниже порога).", parse_mode='HTML')
                return
            # Топ-15 результатов
            lines = [f"🔍 <b>Скрининг рынка — {len(results)} кандидатов</b>\n"]
            for r in results[:15]:
                emoji = r.get('signals', '➖') or '➖'
                line = f"{emoji} <b>{r['ticker']}</b> ${r.get('price', 0):.2f} | Счёт: {r.get('score', 0)}/100"
                if r.get('day_change') is not None:
                    line += f" | {r['day_change']:+.2f}%"
                if r.get('rsi_14'):
                    line += f" | RSI: {r['rsi_14']:.0f}"
                if r.get('pe_ratio') and r['pe_ratio'] > 0:
                    line += f" | P/E: {r['pe_ratio']:.1f}"
                lines.append(line)
            # Кнопки: обновить или сгенерировать идеи
            keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="scan_now")]]
            if results:
                keyboard.append([InlineKeyboardButton("💡 Сгенерировать идеи из топ-5", callback_data=f"gen_ideas_{results[0]['ticker']}_{results[1]['ticker'] if len(results)>1 else ''}")])
            await status_msg.edit_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка скрининга: {e}", parse_mode='HTML')

    # ─── Идеи ───
    async def cmd_ideas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _init_db()
        ideas = db.get_pending_ideas()
        if not ideas:
            keyboard = [[InlineKeyboardButton("🔍 Сначала просканировать рынок", callback_data="scan_now")]]
            await update.message.reply_text("✅ Нет ожидающих идей", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return
        for idea in ideas:
            text = (
                f"💡 <b>Идея #{idea['id']}</b>\n"
                f"Тикер: {idea['ticker']} | {'🟢 ПОКУПКА' if idea['direction']=='buy' else '🔴 ПРОДАЖА' if idea['direction']=='sell' else '⚪ ДЕРЖАТЬ'}\n"
                f"Цена: ${idea['price']:.2f} | Цель: {'$'+str(idea['target_price']) if idea['target_price'] else '—'}\n"
                f"Стоп: {'$'+str(idea['stop_price']) if idea['stop_price'] else '—'}\n"
                f"Счёт: {idea['score']}/100 | Риск: {idea['risk_level']}\n"
                f"Обоснование: {idea['rationale']}\n"
                f"Создана: {idea['created_at'][:16]}"
            )
            keyboard = [
                [InlineKeyboardButton("✅ Апрув", callback_data=f"approve_{idea['id']}"),
                 InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{idea['id']}")]
            ]
            await update.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    # ─── Портфель ───
    async def cmd_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _init_db()
        summary = db.get_portfolio_summary()
        if not summary['positions']:
            keyboard = [[InlineKeyboardButton("📋 Как добавить позиции", callback_data="help_add")]]
            await update.message.reply_text("📭 Портфель пуст.\n\nДобавьте позиции вручную в БД или дождитесь генерации идей с апрувом.", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return
        lines = [f"📊 <b>Портфель stocks-us</b>\n"]
        for p in summary['positions']:
            emoji = '🟢' if p['pl_pct'] >= 0 else '🔴'
            target_pct = p.get('target_pct')
            target_str = f" | Цель: {target_pct:+.0f}%" if target_pct else ""
            lines.append(
                f"{emoji} <b>{p['ticker']}</b>  {p['shares']} шт × ${p['current_price']:.2f}\n"
                f"   Средняя: ${p['avg_price']:.2f} | P&L: ${p['pl']:+.2f} ({p['pl_pct']:+.2f}%){target_str}"
            )
        lines.append(f"\n💰 <b>Всего:</b> ${summary['total_value']:,.2f}  |  P&L: ${summary['total_pl']:+,.2f} ({summary['total_pl_pct']:+.2f}%)")
        # Кнопки обновления
        keyboard = [[InlineKeyboardButton("🔄 Обновить цены", callback_data="refresh_prices")]]
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    # ─── Цена ───
    async def cmd_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Использование: /price TICKER\nПример: /price NVDA\n\nИли нажми кнопку для быстрого просмотра:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("NVDA", callback_data="price_NVDA"),
                     InlineKeyboardButton("AAPL", callback_data="price_AAPL"),
                     InlineKeyboardButton("TSLA", callback_data="price_TSLA")],
                    [InlineKeyboardButton("SPY", callback_data="price_SPY"),
                     InlineKeyboardButton("MSTR", callback_data="price_MSTR"),
                     InlineKeyboardButton("GLD", callback_data="price_GLD")],
                ])
            )
            return
        ticker = context.args[0].upper()
        await self._show_price(update, ticker)

    async def _show_price(self, update: Update, ticker: str):
        from market import analyze_ticker
        msg = await update.message.reply_text(f"⏳ Анализирую {ticker}...", parse_mode='HTML')
        a = analyze_ticker(ticker)
        if a.get('error'):
            await msg.edit_text(f"❌ {ticker}: {a['error']}", parse_mode='HTML')
            return
        lines = [
            f"📈 <b>{ticker}</b> — ${a.get('price', 0):.2f}",
            f"Изм.: {a.get('day_change', 0):+.2f}% | Счёт: {a.get('score', 50)}/100 {a.get('signals', '')}",
        ]
        if a.get('rsi_14'):
            lines.append(f"RSI(14): {a['rsi_14']:.0f} | SMA20: ${a.get('sma_20', 0):.2f} | SMA50: ${a.get('sma_50', 0):.2f}")
        if a.get('pe_ratio') and a['pe_ratio'] > 0:
            lines.append(f"P/E: {a['pe_ratio']:.1f} | P/B: {a.get('pb_ratio', 0):.1f} | EPS: ${a.get('eps_ttm', 0):.2f}")
        if a.get('div_yield'):
            lines.append(f"Див.: {a['div_yield']:.2f}%")
        if a.get('high_52w_pct') is not None:
            lines.append(f"52W: ${a.get('low_52w', 0):.2f} ← ${a.get('price', 0):.2f} → ${a.get('high_52w', 0):.2f}")
            lines.append(f"От high: {a['high_52w_pct']:+.1f}% | От low: {a.get('low_52w_pct', 0):+.1f}%")
        if a.get('signal_detail'):
            lines.append(f"Сигналы: {', '.join(a['signal_detail'])}")
        # Быстрые действия
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"price_{ticker}"),
             InlineKeyboardButton(f"💡 Идея по {ticker}", callback_data=f"quick_idea_{ticker}")],
            [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_menu")],
        ]
        await msg.edit_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    # ─── P&L ───
    async def cmd_pl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _init_db()
        summary = db.get_portfolio_summary()
        if not summary['positions']:
            await update.message.reply_text("📭 Портфель пуст", parse_mode='HTML')
            return
        lines = [f"💰 <b>P&L отчёт</b>\n"]
        winners = [p for p in summary['positions'] if p['pl'] > 0]
        losers = [p for p in summary['positions'] if p['pl'] <= 0]
        if winners:
            lines.append(f"🟢 <b>В плюсе ({len(winners)}):</b>")
            for p in sorted(winners, key=lambda x: x['pl'], reverse=True)[:5]:
                lines.append(f"  {p['ticker']}: ${p['pl']:+.2f} ({p['pl_pct']:+.2f}%)")
        if losers:
            lines.append(f"\n🔴 <b>В минусе ({len(losers)}):</b>")
            for p in sorted(losers, key=lambda x: x['pl'])[:5]:
                lines.append(f"  {p['ticker']}: ${p['pl']:+.2f} ({p['pl_pct']:+.2f}%)")
        lines.append(f"\n<b>Итого:</b> ${summary['total_pl']:+,.2f} ({summary['total_pl_pct']:+.2f}%)")
        keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="show_pl")]]
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    # ─── DCA ───
    async def cmd_dca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _init_db()
        schedule = db.get_dca_schedule()
        days_map = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс']
        if not schedule:
            keyboard = [[InlineKeyboardButton("⚙️ Настроить DCA", callback_data="setup_dca")]]
            await update.message.reply_text(
                "📅 DCA расписание не настроено.\n\n"
                "По умолчанию: Пн/Чт → AAPL, Вт/Пт → SPY (при просадке 2%+)\n"
                "Настройте через /add_dca или отредактируйте БД.",
                parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return
        lines = [f"📅 <b>DCA расписание</b>\n"]
        for s in schedule:
            dow = days_map[s['day_of_week']] if s['day_of_week'] < 7 else '?'
            lines.append(f"  {s['ticker']} — {dow} в {s['time_of_day']}, порог {s['threshold_pct']:+.1f}%")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    # ─── История ───
    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _init_db()
        ideas = db.get_idea_history(limit=15)
        if not ideas:
            await update.message.reply_text("📭 История идей пуста", parse_mode='HTML')
            return
        status_emoji = {'approved': '✅', 'rejected': '❌', 'pending': '⏳', 'executed': '💰'}
        lines = [f"📋 <b>История идей</b>\n"]
        for idea in ideas:
            emoji = status_emoji.get(idea['status'], '❓')
            lines.append(f"{emoji} #{idea['id']} {idea['ticker']} {idea['direction'].upper()} "
                         f"${idea['price']:.2f} | Счёт: {idea['score']}/100 | {idea['status']}")
        await update.message.reply_text('\n'.join(lines), parse_mode='HTML')

    # ─── Callback handler ───
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Check thread for callback queries
        if self.thread_id and update.callback_query and update.callback_query.message:
            actual = getattr(update.callback_query.message, 'message_thread_id', None)
            if actual != int(self.thread_id):
                await update.callback_query.answer()
                return
        query = update.callback_query
        await query.answer()
        _init_db()
        data = query.data

        # Навигация
        if data == "back_menu":
            keyboard = [
                [InlineKeyboardButton("🔍 Сканировать рынок сейчас", callback_data="scan_now")],
                [InlineKeyboardButton("💡 Идеи на апрув", callback_data="show_ideas"),
                 InlineKeyboardButton("📊 Портфель", callback_data="show_portfolio")],
                [InlineKeyboardButton("💰 P&L", callback_data="show_pl"),
                 InlineKeyboardButton("📅 DCA", callback_data="show_dca")],
            ]
            await query.edit_message_text(
                "📈 <b>Stocks-US Agent</b>\n\nВыберите действие:",
                parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # Сканирование
        if data == "scan_now":
            msg = await query.edit_message_text("🔍 <b>Запускаю скрининг...</b>", parse_mode='HTML')
            # Перезапускаем через _run_scan_inline
            asyncio.create_task(self._run_scan_inline(query, msg))
            return

        # Показ идей
        if data == "show_ideas":
            ideas = db.get_pending_ideas()
            if not ideas:
                keyboard = [[InlineKeyboardButton("🔍 Сканировать", callback_data="scan_now")]]
                await query.edit_message_text("✅ Нет ожидающих идей", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
                return
            # Показываем первую идею
            idea = ideas[0]
            keyboard = [[InlineKeyboardButton("✅ Апрув", callback_data=f"approve_{idea['id']}"),
                         InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{idea['id']}")]]
            if len(ideas) > 1:
                keyboard.append([InlineKeyboardButton(f"Далее ({len(ideas)-1} ещё)", callback_data=f"show_idea_{ideas[1]['id']}")])
            text = (
                f"💡 <b>Идея #{idea['id']}</b>\n"
                f"Тикер: {idea['ticker']} | {'🟢 ПОКУПКА' if idea['direction']=='buy' else '🔴 ПРОДАЖА' if idea['direction']=='sell' else '⚪ ДЕРЖАТЬ'}\n"
                f"Цена: ${idea['price']:.2f} | Цель: {'$'+str(idea['target_price']) if idea['target_price'] else '—'}\n"
                f"Стоп: {'$'+str(idea['stop_price']) if idea['stop_price'] else '—'}\n"
                f"Счёт: {idea['score']}/100 | Риск: {idea['risk_level']}\n"
                f"Обоснование: {idea['rationale']}"
            )
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        # Показ портфеля
        if data == "show_portfolio":
            summary = db.get_portfolio_summary()
            if not summary['positions']:
                await query.edit_message_text("📭 Портфель пуст", parse_mode='HTML')
                return
            lines = [f"📊 <b>Портфель stocks-us</b>\n"]
            for p in summary['positions']:
                emoji = '🟢' if p['pl_pct'] >= 0 else '🔴'
                lines.append(f"{emoji} <b>{p['ticker']}</b> {p['shares']} шт × ${p['current_price']:.2f} | P&L: {p['pl_pct']:+.2f}%")
            lines.append(f"\n💰 <b>Всего:</b> ${summary['total_value']:,.2f} | P&L: ${summary['total_pl']:+,.2f} ({summary['total_pl_pct']:+.2f}%)")
            keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="show_portfolio"), InlineKeyboardButton("◀️ Назад", callback_data="back_menu")]]
            await query.edit_message_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        # P&L
        if data == "show_pl":
            summary = db.get_portfolio_summary()
            lines = [f"💰 <b>P&L</b>\n"]
            for p in summary['positions']:
                lines.append(f"{'🟢' if p['pl']>=0 else '🔴'} {p['ticker']}: ${p['pl']:+.2f} ({p['pl_pct']:+.2f}%)")
            lines.append(f"\n<b>Итого:</b> ${summary['total_pl']:+,.2f}")
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_menu")]]
            await query.edit_message_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data == "show_dca":
            schedule = db.get_dca_schedule()
            days_map = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс']
            if not schedule:
                await query.edit_message_text("📅 DCA не настроено", parse_mode='HTML')
                return
            lines = [f"📅 <b>DCA</b>\n"]
            for s in schedule:
                lines.append(f"  {s['ticker']} — {days_map[s['day_of_week']]} {s['time_of_day']}, порог {s['threshold_pct']:+.1f}%")
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_menu")]]
            await query.edit_message_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        # Апрув/отклонение
        if data.startswith('approve_'):
            idea_id = int(data.split('_')[1])
            db.decide_idea(idea_id, 'approved')
            await query.edit_message_text(text=query.message.text + "\n\n✅ <b>АПРУВЛЕНО</b>", parse_mode='HTML')
            return
        if data.startswith('reject_'):
            idea_id = int(data.split('_')[1])
            db.decide_idea(idea_id, 'rejected')
            await query.edit_message_text(text=query.message.text + "\n\n❌ <b>ОТКЛОНЕНО</b>", parse_mode='HTML')
            return

        # Показ следующей идеи
        if data.startswith('show_idea_'):
            idea_id = int(data.split('_')[2])
            idea = db.conn.execute("SELECT * FROM ideas WHERE id=?", (idea_id,)).fetchone()
            if not idea:
                await query.edit_message_text("❌ Идея не найдена", parse_mode='HTML')
                return
            idea = dict(idea)
            remaining = db.conn.execute("SELECT COUNT(*) FROM ideas WHERE status='pending' AND id > ?", (idea_id,)).fetchone()[0]
            keyboard = [[InlineKeyboardButton("✅ Апрув", callback_data=f"approve_{idea['id']}"),
                         InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{idea['id']}")]]
            if remaining:
                keyboard.append([InlineKeyboardButton(f"Далее ({remaining})", callback_data=f"show_idea_{idea_id+1}")])
            text = (
                f"💡 <b>Идея #{idea['id']}</b>\n"
                f"Тикер: {idea['ticker']} | {'🟢 ПОКУПКА' if idea['direction']=='buy' else '🔴 ПРОДАЖА'}\n"
                f"Цена: ${idea['price']:.2f} | Цель: {'$'+str(idea['target_price']) if idea['target_price'] else '—'}\n"
                f"Стоп: {'$'+str(idea['stop_price']) if idea['stop_price'] else '—'}\n"
                f"Счёт: {idea['score']}/100 | Риск: {idea['risk_level']}\n"
                f"Обоснование: {idea['rationale']}"
            )
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        # Быстрый просмотр цены
        if data.startswith('price_'):
            ticker = data.split('_')[1]
            from market import analyze_ticker
            a = analyze_ticker(ticker)
            if a.get('error'):
                await query.edit_message_text(f"❌ {ticker}: {a['error']}", parse_mode='HTML')
                return
            lines = [
                f"📈 <b>{ticker}</b> — ${a.get('price', 0):.2f}",
                f"Изм.: {a.get('day_change', 0):+.2f}% | Счёт: {a.get('score', 50)}/100 {a.get('signals', '')}",
            ]
            if a.get('rsi_14'):
                lines.append(f"RSI(14): {a['rsi_14']:.0f}")
            if a.get('pe_ratio') and a['pe_ratio'] > 0:
                lines.append(f"P/E: {a['pe_ratio']:.1f}")
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data=f"price_{ticker}"),
                 InlineKeyboardButton(f"💡 Идея", callback_data=f"quick_idea_{ticker}")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")],
            ]
            await query.edit_message_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data.startswith('quick_idea_'):
            ticker = data.split('_')[2]
            await query.edit_message_text(f"💡 Генерирую идею по {ticker}...", parse_mode='HTML')
            asyncio.create_task(self._gen_idea_for_ticker(query, ticker))

    async def _run_scan_inline(self, query, msg):
        from market import screen_market
        try:
            results = screen_market(min_score=55)
            if not results:
                keyboard = [[InlineKeyboardButton("🔄 Попробовать ещё", callback_data="scan_now")]]
                await msg.edit_text("🔍 Скрининг завершён. Ничего не найдено.", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
                return
            lines = [f"🔍 <b>Скрининг — {len(results)} кандидатов</b>\n"]
            for r in results[:12]:
                emoji = r.get('signals', '➖') or '➖'
                line = f"{emoji} <b>{r['ticker']}</b> ${r.get('price', 0):.2f} | {r.get('score', 0)}/100"
                if r.get('day_change') is not None:
                    line += f" | {r['day_change']:+.2f}%"
                lines.append(line)
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="scan_now")],
                [InlineKeyboardButton("💡 Сгенерировать идеи из топ-5", callback_data="gen_ideas_top5")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")],
            ]
            await msg.edit_text('\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка: {e}", parse_mode='HTML')

    async def _gen_idea_for_ticker(self, query, ticker: str):
        _init_db()
        from market import analyze_ticker
        a = analyze_ticker(ticker)
        if a.get('error'):
            await query.edit_message_text(f"❌ {ticker}: {a['error']}", parse_mode='HTML')
            return
        score = a.get('score', 50)
        price = a.get('price', 0)
        direction = 'buy' if score >= 60 else 'sell' if score <= 35 else 'hold'
        target = round(price * 1.15, 2) if direction == 'buy' else round(price * 0.85, 2)
        stop = round(price * 0.9, 2) if direction == 'buy' else round(price * 1.1, 2)
        rationale_parts = a.get('signal_detail', [])
        if a.get('pe_ratio') and a['pe_ratio'] < 15:
            rationale_parts.append('низкий P/E')
        if a.get('rsi_14') and a['rsi_14'] < 35:
            rationale_parts.append('перепроданность по RSI')
        rationale = ', '.join(rationale_parts) if rationale_parts else f"Счёт {score}/100"
        risk = 'low' if score >= 70 else 'medium' if score >= 45 else 'high'
        idea_id = db.save_idea(ticker, direction, price, target, stop, score, rationale, risk)
        text = (
            f"💡 <b>Новая идея #{idea_id}</b>\n"
            f"Тикер: {ticker} | {'🟢 ПОКУПКА' if direction=='buy' else '🔴 ПРОДАЖА' if direction=='sell' else '⚪ ДЕРЖАТЬ'}\n"
            f"Цена: ${price:.2f} | Цель: ${target:.2f} | Стоп: ${stop:.2f}\n"
            f"Счёт: {score}/100 | Риск: {risk}\n"
            f"Обоснование: {rationale}\n\n"
            f"Требуется апрув."
        )
        keyboard = [[InlineKeyboardButton("✅ Апрув", callback_data=f"approve_{idea_id}"),
                     InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{idea_id}")]]
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    async def _silent_ignore(self, update, ctx):
        pass

    # ─── Отправка отчётов без поллинга (для cron) ───
    def send_report(self, text: str) -> bool:
        import requests
        force_ipv4()
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        if self.thread_id:
            payload['message_thread_id'] = int(self.thread_id)
        try:
            r = requests.post(url, json=payload, timeout=15)
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Send report failed: {e}")
            return False

    def send_idea_notification(self, ticker: str, direction: str, price: float, target: float,
                                stop: float, score: int, rationale: str, risk: str, idea_id: int) -> bool:
        import requests
        force_ipv4()
        text = (
            f"💡 <b>Новая идея #{idea_id}</b>\n"
            f"Тикер: {ticker} | {'🟢 ПОКУПКА' if direction=='buy' else '🔴 ПРОДАЖА' if direction=='sell' else '⚪ ДЕРЖАТЬ'}\n"
            f"Цена: ${price:.2f} | Цель: {'$'+str(target) if target else '—'}\n"
            f"Стоп: {'$'+str(stop) if stop else '—'}\n"
            f"Счёт: {score}/100 | Риск: {risk}\n"
            f"Обоснование: {rationale}\n"
        )
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '✅ Апрув', 'callback_data': f'approve_{idea_id}'},
                     {'text': '❌ Отклонить', 'callback_data': f'reject_{idea_id}'}]
                ]
            }
        }
        if self.thread_id:
            payload['message_thread_id'] = int(self.thread_id)
        try:
            r = requests.post(url, json=payload, timeout=15)
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Send idea failed: {e}")
            return False
