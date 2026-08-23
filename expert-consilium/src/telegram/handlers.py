from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.config import settings
from src.db.repository import ExpertResponseRepository, RequestRepository
from src.db.session import async_session_factory
from src.redis_client import TaskQueue, get_redis
from src.core.openrouter import OpenRouterClient, EXPERT_CONFIGS
from src.core.schemas import ExpertResponseSchema
from src.core.smart_mode import determine_mode, calculate_complexity_score
from src.core.synthesizer import build_synthesizer_prompt, parse_synthesized_response, SYNTHESIZER_SYSTEM_PROMPT
from src.telegram.keyboards import EXPERT_INFO, get_mode_keyboard, get_panel_keyboard, bot
from src.telegram.messages import (
    HELP_MESSAGE, WELCOME_MESSAGE,
    build_analysis_message, build_expert_info_text,
    build_final_message, build_history_message,
    build_mode_message, build_progress_message,
)

logger = logging.getLogger(__name__)
router = Router()

# User state: mode (basic/premium)
_user_mode: dict[int, str] = {}

# Active requests: user_id -> {"message": Message, "request_id": UUID, "results": [...], "total": 5}
_active_requests: dict[int, dict] = {}


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user_id = message.from_user.id
    _user_mode[user_id] = settings.default_mode
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_mode_keyboard(settings.default_mode),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(HELP_MESSAGE)


@router.message(Command("deep"))
async def cmd_deep(message: Message) -> None:
    """Enable premium mode for next question."""
    user_id = message.from_user.id
    _user_mode[user_id] = "premium"
    await message.answer(
        "🌟 *Премиум-режим активирован!*\n\n"
        "Следующий вопрос будет обработан топовыми моделями.",
        reply_markup=get_mode_keyboard("premium"),
    )


@router.message(Command("mode"))
async def cmd_mode(message: Message) -> None:
    """Show current mode."""
    user_id = message.from_user.id
    current = _user_mode.get(user_id, settings.default_mode)
    await message.answer(build_mode_message(current))


@router.message(Command("panel"))
async def cmd_panel(message: Message) -> None:
    """Show expert panel."""
    await message.answer(
        "👥 *Состав Консилиума Экспертов*\n\n"
        "Нажми на эксперта, чтобы узнать подробнее:",
        reply_markup=get_panel_keyboard(),
    )


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    """Show recent requests."""
    user_id = message.from_user.id
    async with async_session_factory() as session:
        repo = RequestRepository(session)
        requests = await repo.list_recent(limit=5)
        # Filter by user
        user_requests = [r for r in requests if r.user_id == user_id]
    
    history_data = [
        {
            "question": r.question,
            "mode": r.mode,
            "created_at": r.created_at,
            "status": r.status,
        }
        for r in user_requests
    ]
    await message.answer(build_history_message(history_data))


@router.message(F.text & ~F.command())
async def handle_question(message: Message) -> None:
    """Handle user question."""
    user_id = message.from_user.id
    username = message.from_user.username
    question = message.text.strip()
    logger.info(f"Received message from user={user_id}: {question[:50]}...")

    if not question:
        return

    if len(question) > settings.max_question_length:
        await message.answer(f"❌ Вопрос слишком длинный. Максимум {settings.max_question_length} символов.")
        return

    # Determine mode
    user_forced_mode = _user_mode.get(user_id)
    mode = determine_mode(question, user_forced_mode)
    complexity = calculate_complexity_score(question)

    # Reset user mode after use
    if user_forced_mode == "premium":
        _user_mode[user_id] = settings.default_mode

    # Send initial analysis message
    analysis_msg = await message.answer(
        build_analysis_message(question, mode),
        reply_markup=get_mode_keyboard(mode),
    )

    try:
        # Create request in DB
        async with async_session_factory() as session:
            repo = RequestRepository(session)
            request = await repo.create(
                user_id=user_id,
                question=question,
                mode=mode,
                username=username,
                complexity_score=complexity,
            )
            request_id = request.id

        # Push task to Redis queue
        redis = await get_redis()
        task_queue = TaskQueue(redis)
        await task_queue.push_task({
            "request_id": str(request_id),
            "question": question,
            "mode": mode,
            "user_id": user_id,
            "message_id": analysis_msg.message_id,
            "chat_id": message.chat.id,
            "topic_id": message.message_thread_id or settings.telegram_topic_id,
        })

        # Wait for results via Redis Pub/Sub
        # We'll poll the DB for completion
        _active_requests[user_id] = {
            "message": analysis_msg,
            "request_id": request_id,
            "results": [],
            "total": len(EXPERT_CONFIGS),
            "mode": mode,
        }

        # Poll for results
        await poll_for_results(user_id, request_id, analysis_msg, mode)

    except Exception as e:
        logger.exception("Error processing question")
        await analysis_msg.edit_text(
            f"❌ *Ошибка при анализе*\n\n{str(e)[:200]}"
        )


async def poll_for_results(user_id: int, request_id: UUID,
                           analysis_msg: Message, mode: str) -> None:
    """Poll DB until all expert responses are ready."""
    max_attempts = 60  # 60 * 2s = 120s max wait
    completed = 0
    total = len(EXPERT_CONFIGS)
    reported = set()

    for attempt in range(max_attempts):
        await asyncio.sleep(2)

        # Check DB for complete responses
        async with async_session_factory() as session:
            repo = RequestRepository(session)
            request = await repo.get_with_responses(request_id)

        if not request:
            break

        current_responses = [r for r in request.responses if r.role != "synthesizer"]
        completed = len(current_responses)
        synthesizer_responses = [r for r in request.responses if r.role == "synthesizer"]
        is_done = request.status == "completed" and synthesizer_responses

        # Update progress every 2 responses
        if completed > 0 and completed != len(reported):
            reported.add(completed)
            try:
                results_data = [
                    {"label": f"✅ {r.role}", "role": r.role}
                    for r in current_responses
                ]
                # Only update every 2 responses or at completion
                if completed % 2 == 0 or completed == total or is_done:
                    await analysis_msg.edit_text(
                        build_progress_message(completed, total, results_data),
                        reply_markup=get_mode_keyboard(mode),
                    )
            except Exception:
                pass

        if is_done:
            # Get final result
            synth = synthesizer_responses[0]

            # Calculate total cost
            total_cost = sum(
                (r.cost or 0.0) for r in current_responses
            ) + (synth.cost or 0.0)

            # Parse synthesized response
            synthesized = parse_synthesized_response(synth.response_text)

            # Send final message
            await analysis_msg.edit_text(
                build_final_message(
                    request.question, synthesized, mode, total_cost
                ),
                reply_markup=get_mode_keyboard(mode),
            )

            # Clean up
            _active_requests.pop(user_id, None)
            return

    # Timeout
    _active_requests.pop(user_id, None)
    try:
        await analysis_msg.edit_text(
            "⏱ *Таймаут*\n\n"
            "Не удалось получить ответы от всех экспертов вовремя. "
            "Попробуй ещё раз или используй более короткий вопрос."
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("expert_"))
async def callback_expert_info(callback: CallbackQuery) -> None:
    """Show expert info."""
    role = callback.data.replace("expert_", "")
    text = build_expert_info_text(role)
    await callback.message.edit_text(text, reply_markup=get_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "panel")
async def callback_panel(callback: CallbackQuery) -> None:
    """Show panel."""
    await callback.message.edit_text(
        "👥 *Состав Консилиума Экспертов*\n\n"
        "Нажми на эксперта, чтобы узнать подробнее:",
        reply_markup=get_panel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def callback_back(callback: CallbackQuery) -> None:
    """Back to main."""
    user_id = callback.from_user.id
    mode = _user_mode.get(user_id, settings.default_mode)
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=get_mode_keyboard(mode),
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_mode")
async def callback_toggle_mode(callback: CallbackQuery) -> None:
    """Toggle between basic and premium mode."""
    user_id = callback.from_user.id
    current = _user_mode.get(user_id, settings.default_mode)
    new_mode = "premium" if current == "basic" else "basic"
    _user_mode[user_id] = new_mode
    await callback.message.edit_text(
        build_mode_message(new_mode),
        reply_markup=get_mode_keyboard(new_mode),
    )
    await callback.answer()