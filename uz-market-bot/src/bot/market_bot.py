"""Telegram бот — поиск лучших предложений на рынке Узбекистана"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters,
)

from src.parsers.olx_uz import OLXParser
from src.utils.llm_client import LLMClient
from src.utils.aggregator import Aggregator, SearchCriteria, UnifiedOffer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Состояния ConversationHandler
QUERY, CLARIFYING, CITIES, SORT, RESULT = range(5)

# Путь к конфигу
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
CONFIG_DIR.mkdir(exist_ok=True)


class MarketBot:
    def __init__(self, token: str, openrouter_key: str, config: dict = None):
        self.token = token
        self.llm = LLMClient(api_key=openrouter_key)
        self.olx = OLXParser()
        self.agg = Aggregator()
        self.config = config or {}
        
        # Хранилище сессий пользователей (в памяти)
        self.sessions: dict[int, dict] = {}
    
    def get_or_create_session(self, user_id: int) -> dict:
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "query": "",
                "criteria": {},
                "history": [],
                "results": [],
                "state": "idle",
            }
        return self.sessions[user_id]
    
    async def start(self, update: Update, context):
        user = update.effective_user
        session = self.get_or_create_session(user.id)
        session["state"] = "idle"
        
        welcome = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"Я — *MarketBot UZ* 🏪\n"
            f"Помогаю найти лучшие предложения на рынке Узбекистана.\n\n"
            f"Просто напиши, что ищешь. Например:\n"
            f"• \"iPhone 15 до 500$\"\n"
            f"• \"ноутбук для работы в Ташкенте\"\n"
            f"• \"холодильник недорого б/у\"\n\n"
            f"Я задам пару уточняющих вопросов и найду лучшие варианты! 🚀"
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")
        return QUERY
    
    async def handle_query(self, update: Update, context):
        """Обрабатываем начальный запрос пользователя"""
        user_id = update.effective_user.id
        session = self.get_or_create_session(user_id)
        session["query"] = update.message.text
        session["history"] = []
        
        await update.message.reply_text(
            "⏳ Анализирую запрос...",
        )
        
        try:
            response = self.llm.generate_questions(session["query"])
        except Exception as e:
            logger.error(f"LLM error: {e}")
            response = "ГОТОВО_К_ПОИСКУ"
        
        if "ГОТОВО_К_ПОИСКУ" in response:
            session["state"] = "ready"
            return await self._do_search(update, context, session)
        
        session["state"] = "clarifying"
        session["history"].append({"role": "assistant", "content": response})
        
        # Убираем "ГОТОВО_К_ПОИСКУ" если есть лишнее
        clean_response = response.replace("ГОТОВО_К_ПОИСКУ", "").strip()
        if clean_response:
            await update.message.reply_text(clean_response)
        else:
            # Если LLM сразу сказала ГОТОВО_К_ПОИСКУ без вопросов
            return await self._do_search(update, context, session)
        
        return CLARIFYING
    
    async def handle_clarifying(self, update: Update, context):
        """Обрабатываем ответы на уточняющие вопросы"""
        user_id = update.effective_user.id
        session = self.get_or_create_session(user_id)
        user_answer = update.message.text
        
        session["history"].append({"role": "user", "content": user_answer})
        
        await update.message.reply_text("⏳ Думаю...")
        
        try:
            response = self.llm.generate_questions(
                user_answer, 
                history=session["history"]
            )
        except Exception as e:
            logger.error(f"LLM error: {e}")
            response = "ГОТОВО_К_ПОИСКУ"
        
        if "ГОТОВО_К_ПОИСКУ" in response:
            session["state"] = "ready"
            return await self._do_search(update, context, session)
        
        session["history"].append({"role": "assistant", "content": response})
        clean_response = response.replace("ГОТОВО_К_ПОИСКУ", "").strip()
        if clean_response:
            await update.message.reply_text(clean_response)
        else:
            return await self._do_search(update, context, session)
        
        return CLARIFYING
    
    def _extract_criteria(self, query: str, history: list[dict]) -> SearchCriteria:
        """Извлекает критерии поиска из запроса и истории"""
        full_text = query + "\n" + "\n".join(
            m["content"] for m in history if m["role"] in ("user", "assistant")
        )
        
        max_price = None
        city = None
        condition = None
        
        # Пытаемся извлечь цену
        price_patterns = [
            r'(?:до|не дороже|макс|max|в пределах)\s*(\d+[\.\d]*(?:\s*\$)?)',
            r'(\d+[\.\d]*)\s*(?:сум|сумов|usd|\$|у\.е)',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(" ", "").replace("$", "")
                try:
                    max_price = float(price_str)
                except ValueError:
                    pass
                break
        
        # Город
        cities = ["ташкент", "самарканд", "бухара", "андижан", "фергана", 
                  "наманган", "нукус", "карши", "ургенч", "джизак", "термез",
                  "навои", "гулистан", "tashkent", "samarkand"]
        for c in cities:
            if c.lower() in full_text.lower():
                city = c.capitalize()
                break
        
        # Состояние
        if any(w in full_text.lower() for w in ["новый", "новое", "новая", "new"]):
            condition = "new"
        elif any(w in full_text.lower() for w in ["б/у", "бу", "бэушн", "бушн", "used"]):
            condition = "used"
        
        return SearchCriteria(
            query=query,
            max_price=max_price,
            city=city,
            condition=condition,
        )
    
    async def _do_search(self, update: Update, context, session: dict):
        """Выполняет поиск по всем площадкам"""
        user_id = update.effective_user.id
        query = session["query"]
        
        criteria = self._extract_criteria(query, session.get("history", []))
        session["criteria"] = criteria
        
        status_msg = await update.message.reply_text(
            f"🔍 Ищу лучшие предложения по \"{query}\"...\n"
            f"📡 OLX.uz — проверяю..."
        )
        
        all_offers = []
        
        # 1. OLX
        try:
            logger.info(f"Searching OLX: {query}")
            olx_result = self.olx.search(
                query=query,
                limit=25,
                max_price=criteria.max_price,
                city=criteria.city,
            )
            
            for offer in olx_result.offers:
                all_offers.append(UnifiedOffer(
                    title=offer.title,
                    price_label=offer.price_label,
                    price_value=offer.price_value,
                    currency=offer.currency,
                    url=offer.url,
                    photo_url=offer.photo_url,
                    city=offer.city,
                    source="OLX",
                    condition=offer.state,
                    seller=offer.seller_name,
                    created=offer.created_time,
                ))
            
            logger.info(f"OLX found {len(olx_result.offers)} offers")
        except Exception as e:
            logger.error(f"OLX error: {e}")
        
        # 2. Анализ через LLM
        analysis = None
        if all_offers:
            try:
                offers_for_llm = []
                for o in all_offers[:20]:
                    offers_for_llm.append({
                        "title": o.title,
                        "price_label": o.price_label,
                        "price_value": o.price_value,
                        "city": o.city,
                        "source": o.source,
                    })
                
                analysis = self.llm.analyze_results(
                    query=query,
                    criteria={
                        "max_price": criteria.max_price,
                        "city": criteria.city,
                        "condition": criteria.condition,
                    },
                    results=offers_for_llm,
                )
            except Exception as e:
                logger.error(f"Analysis error: {e}")
        
        # 3. Сортировка
        ranked = self.agg.merge_and_rank(all_offers, criteria)
        
        # 4. Форматирование ответа
        answer = self.agg.format_summary(
            ranked, 
            total_found=len(all_offers),
            analysis=analysis,
        )
        
        await status_msg.edit_text(answer, parse_mode="Markdown", disable_web_page_preview=True)
        
        # Кнопка для нового поиска
        keyboard = [[InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search")]]
        await update.message.reply_text(
            "Можешь начать новый поиск или уточнить запрос ⬇️",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        
        session["state"] = "idle"
        try:
            return ConversationHandler.END
        except:
            return None
    
    async def new_search(self, update: Update, context):
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("Напиши, что ищешь:")
        return QUERY
    
    async def cancel(self, update: Update, context):
        await update.message.reply_text("👋 До встречи! Напиши /start когда захочешь снова.")
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context):
        help_text = (
            "🤖 *MarketBot UZ* — поиск лучших предложений\n\n"
            "*/start* — начать диалог\n"
            "*/help* — эта справка\n"
            "*/cancel* — отменить поиск\n\n"
            "*Примеры запросов:*\n"
            "• \"iPhone 15 Pro Max\"\n"
            "• \"ноутбук для работы до 500$ Ташкент\"\n"
            "• \"холодильник Samsung б/у\"\n\n"
            "*Поддерживаемые площадки:*\n"
            "• OLX.uz\n"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    def send_to_group(self, query: str, results: list, analysis: str = None):
        """Отправляет результаты поиска в группу AI Assistant — Family"""
        import asyncio
        from telegram import Bot
        
        bot = Bot(token=self.token)
        chat_id = self.config.get('telegram_chat_id')
        thread_id = self.config.get('telegram_thread_id')
        
        if not chat_id:
            logger.warning('telegram_chat_id не задан, пропускаю отправку в группу')
            return
        
        text = self.agg.format_summary(results, len(results), analysis)
        
        kwargs = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True,
        }
        if thread_id:
            kwargs['message_thread_id'] = thread_id
        
        try:
            asyncio.run(bot.send_message(**kwargs))
            logger.info(f'Результаты отправлены в группу {chat_id}')
        except Exception as e:
            logger.error(f'Ошибка отправки в группу: {e}')

    def send_to_group(self, query: str, results: list, analysis: str = None):
        """Отправляет результаты поиска в группу AI Assistant - Family"""
        import asyncio
        from telegram import Bot
        
        bot = Bot(token=self.token)
        chat_id = self.config.get('telegram_chat_id')
        thread_id = self.config.get('telegram_thread_id')
        
        if not chat_id:
            return
        
        text = self.agg.format_summary(results, len(results), analysis)
        
        kwargs = {
            'chat_id': chat_id,
            'text': text,
            'disable_web_page_preview': True,
        }
        if thread_id:
            kwargs['message_thread_id'] = thread_id
        
        try:
            asyncio.run(bot.send_message(**kwargs))
            logger.info(f'Results sent to group {chat_id}')
        except Exception as e:
            logger.error(f'Group send error: {e}')


    def run(self):
        app = Application.builder().token(self.token).build()
        
        # Group handler - отдельный обработчик для сообщений в топике
        async def group_text(update, context):
            if not update.message or not update.message.text:
                return
            chat = update.message.chat
            gid = str(chat.id)
            cfg_id = str(self.config.get("telegram_chat_id", ""))
            if gid != cfg_id:
                return
            thread = self.config.get("telegram_thread_id")
            text = update.message.text
            is_in_thread = thread and update.message.message_thread_id == thread
            is_mentioned = f"@{context.bot.username}" in text.lower()
            if is_in_thread or is_mentioned:
                clean_text = text.replace(f"@{context.bot.username}", "", 1).strip()
                if not clean_text:
                    return
                session = self.get_or_create_session(update.effective_user.id)
                session["query"] = clean_text
                session["history"] = []
                msg = await update.message.reply_text("🔍 Ищу лучшие предложения...")
                await self._do_search(update, context, session)
                return
        
        # Register group handler in its own group (lower priority, only for groups)
        app.add_handler(MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            group_text
        ), group=1)
        

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_query)],
                CLARIFYING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_clarifying)],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CommandHandler("help", self.help_command),
            ],
        )
        
        # Private chat handler - реагируем на любой текст в ЛС (даже без /start)
        async def private_text(update, context):
            if not update.message or not update.message.text:
                return
            chat = update.message.chat
            if chat.type == "private":
                # Если это /start - передаём ConversationHandler
                if update.message.text.startswith('/'):
                    return
                # Иначе - сразу начинаем поиск
                session = self.get_or_create_session(update.effective_user.id)
                session["query"] = update.message.text
                session["history"] = []
                await update.message.reply_text("🔍 Ищу лучшие предложения...")
                await self._do_search(update, context, session)
        
        app.add_handler(MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            private_text
        ), group=2)
        
        app.add_handler(conv_handler)
        app.add_handler(CallbackQueryHandler(self.new_search, pattern="new_search"))
        app.add_handler(CommandHandler("help", self.help_command))
        
        logger.info("🤖 MarketBot UZ запущен!")
        app.run_polling(allowed_updates=[Update.MESSAGE, Update.CALLBACK_QUERY, Update.MY_CHAT_MEMBER])


if __name__ == "__main__":
    # Загружаем конфиг
    config_path = CONFIG_DIR / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        # Fallback на переменные окружения
        config = {
            "telegram_token": os.environ.get("TELEGRAM_MARKET_BOT_TOKEN", ""),
            "openrouter_key": os.environ.get("OPENROUTER_API_KEY", ""),
        }
    
    if not config.get("telegram_token"):
        logger.error("❌ TELEGRAM_MARKET_BOT_TOKEN не задан!")
        print("ERROR: Укажите TELEGRAM_MARKET_BOT_TOKEN в config/config.json или .env")
        exit(1)
    
    if not config.get("openrouter_key"):
        logger.error("❌ OPENROUTER_API_KEY не задан!")
        print("ERROR: Укажите OPENROUTER_API_KEY в config/config.json или .env")
        exit(1)
    
    bot = MarketBot(
        token=config["telegram_token"],
        openrouter_key=config["openrouter_key"],
    )
    bot.run()
