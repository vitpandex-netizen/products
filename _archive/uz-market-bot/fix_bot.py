import sys
sys.path.insert(0, '/Volumes/External/dev/uz-market-bot')

with open('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', 'r') as f:
    code = f.read()

# 1. Fix format_summary — remove markdown
old_format = '''    def format_summary(self, offers: list[UnifiedOffer], total_found: int, analysis: str = None) -> str:
        """Форматирует итоговый ответ"""
        if not offers:
            return "😕 Ничего не найдено по вашему запросу. Попробуйте изменить критерии."
        
        text = f"📊 *Найдено {total_found} предложений*\\n"
        text += f"Показано топ-{min(len(offers), 10)}\\n\\n"'''

new_format = '''    def format_summary(self, offers: list[UnifiedOffer], total_found: int, analysis: str = None) -> str:
        """Форматирует итоговый ответ (без Markdown)"""
        if not offers:
            return "😕 Ничего не найдено по вашему запросу. Попробуйте изменить критерии."
        
        text = f"📊 Найдено {total_found} предложений\\n"
        text += f"Показано топ-{min(len(offers), 10)}\\n\\n"'''

code = code.replace(old_format, new_format)

# Remove bold markdown in list items
code = code.replace(
    'text += f"{i}. *{offer.title}*\\n"',
    'text += f"{i}. {offer.title}\\n"'
)

# Remove bold markdown in analysis section
code = code.replace(
    'text += f"━━━━━━━━━━━━━━━━\\n*🧠 Анализ:*\\n{analysis}\\n"',
    'text += "━" * 20 + "\\n🧠 Анализ:\\n" + analysis + "\\n"'
)

# 2. Add group message handler
old_run_start = '''    def run(self):
        app = Application.builder().token(self.token).build()'''

new_run_start = '''    def run(self):
        app = Application.builder().token(self.token).build()
        
        # Group message handler
        async def group_handler(update, context):
            if not update.message or not update.message.text:
                return
            chat = update.message.chat
            if chat.type in ("group", "supergroup"):
                gid = str(chat.id)
                cfg_id = str(self.config.get("telegram_chat_id", ""))
                if gid == cfg_id:
                    thread = self.config.get("telegram_thread_id")
                    if thread and update.message.message_thread_id == thread:
                        session = self.get_or_create_session(update.effective_user.id)
                        session["query"] = update.message.text
                        session["history"] = []
                        await update.message.reply_text("🔍 Ищу...")
                        return await self._do_search(update, context, session)
            return
        
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Command(), group_handler), group=1)'''

code = code.replace(old_run_start, new_run_start)

with open('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', 'w') as f:
    f.write(code)
print('✅ market_bot.py обновлён')
