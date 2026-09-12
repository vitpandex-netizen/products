import sys
sys.path.insert(0, '/Volumes/External/dev/uz-market-bot')

with open('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', 'r') as f:
    code = f.read()

# Find the run method and replace it entirely
old_run = '''    def run(self):
        app = Application.builder().token(self.token).build()
        
        # Group message handler
        async def _group_handler(self, update: Update, context):
            """Обрабатывает сообщения из группы в топике"""
            if not update.message or not update.message.text:
                return
            chat = update.message.chat
            if chat.type in ("group", "supergroup") and str(chat.id) == str(self.config.get("telegram_chat_id", "")):
                thread = self.config.get("telegram_thread_id")
                if thread and update.message.message_thread_id == thread:
                    session = self.get_or_create_session(update.effective_user.id)
                    session["query"] = update.message.text
                    session["history"] = []
                    await update.message.reply_text("🔍 Ищу лучшие предложения...")
                    await self._do_search(update, context, session)
    
    def run(self):
        app = Application.builder().token(self.token).build()
        
        # Group message handler
        async def _group_handler(self, update: Update, context):
            """Обрабатывает сообщения из группы в топике"""
            if not update.message or not update.message.text:
                return
            chat = update.message.chat
            if chat.type in ("group", "supergroup") and str(chat.id) == str(self.config.get("telegram_chat_id", "")):
                thread = self.config.get("telegram_thread_id")
                if thread and update.message.message_thread_id == thread:
                    session = self.get_or_create_session(update.effective_user.id)
                    session["query"] = update.message.text
                    session["history"] = []
                    await update.message.reply_text("🔍 Ищу лучшие предложения...")
                    await self._do_search(update, context, session)
    
    def run(self):
        app = Application.builder().token(self.token).build()'''

new_run = '''    def run(self):
        app = Application.builder().token(self.token).build()'''

# Remove all occurrences of _group_handler
while '_group_handler' in code:
    # Find the method definition
    start = code.find('    async def _group_handler')
    if start == -1:
        break
    end = code.find('\n    def run(self):', start)
    if end == -1:
        end = code.find('\n    async def ', start + 1)
    if end == -1:
        end = len(code)
    code = code[:start] + code[end:]

# Remove the duplicate run methods
# Find the first run(self) method - keep it
first_run = code.find('    def run(self):')
second_run = code.find('    def run(self):', first_run + 20)
if second_run != -1:
    code = code[:first_run] + code[first_run:second_run] + '\n' + code[code.find('\n        app = Application.builder().token(self.token).build()', second_run):]

# Find the last run method and add proper handler
last_run = code.rfind('    def run(self):')
after_run = code[last_run:]

# Find app.build() line
build_pos = after_run.find('app = Application.builder().token(self.token).build()')
if build_pos != -1:
    # Find where to insert group handler
    insert_pos = after_run.find('\n        conv_handler = ConversationHandler(', build_pos)
    if insert_pos == -1:
        insert_pos = after_run.find('\n        app.add_handler(conv_handler)', build_pos)
    
    # Add group handler function
    handler_code = '''
        # Group handler - отдельный обработчик для сообщений в топике
        async def group_text(update, context):
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
                        msg = await update.message.reply_text("🔍 Ищу лучшие предложения...")
                        await self._do_search(update, context, session)
                        return
        
        # Register group handler FIRST (low group number = higher priority)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            group_text
        ), group=0)
        
'''
    
    after_run = after_run[:insert_pos] + handler_code + after_run[insert_pos:]

code = code[:last_run] + after_run

with open('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', 'w') as f:
    f.write(code)

import py_compile
py_compile.compile('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', doraise=True)
print('✅ OK')
