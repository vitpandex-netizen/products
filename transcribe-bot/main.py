import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

import admin_panel
import json
import state
from bot_api import (
    API,
    TELEGRAM_DOWNLOAD_LIMIT,
    FileTooLarge,
    download_file,
    scrub,
    send_document,
    send_message,
    set_my_commands,
)

load_dotenv()

CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
THREAD_ID = int(os.environ["TELEGRAM_THREAD_ID"])
ADMIN_THREAD_ID = int(os.environ["ADMIN_THREAD_ID"])
TRANSCRIBE_URL = os.environ.get("TRANSCRIBE_SERVICE_URL", "http://transcribe-service:8000")
MEETING_SERVICE_URL = os.environ.get("MEETING_SERVICE_URL", "http://localhost:8001")
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("transcribe-bot")

BOT_USERNAME: str | None = None


def fetch_bot_username() -> None:
    global BOT_USERNAME
    resp = requests.get(f"{API}/getMe", timeout=15)
    resp.raise_for_status()
    BOT_USERNAME = resp.json()["result"]["username"]


def transcribe(path: Path) -> tuple[str, list]:
    with open(path, "rb") as f:
        resp = requests.post(
            f"{TRANSCRIBE_URL}/transcribe",
            files={"file": (path.name, f)},
            timeout=3600,
        )
    resp.raise_for_status()
    data = resp.json()
    return data["text"], data.get("segments", [])


def extract_audio(msg: dict) -> dict | None:
    audio = msg.get("voice") or msg.get("audio") or msg.get("video_note")
    if audio:
        return audio
    doc = msg.get("document")
    if doc and doc.get("mime_type", "").split("/")[0] in ("audio", "video"):
        return doc
    return None


def handle_admin_message(msg: dict) -> None:
    actor_id = msg.get("from", {}).get("id")
    text = (msg.get("text") or "").strip()

    if not state.is_admin(actor_id):
        admin_panel.cancel_pending(actor_id)
        send_message(
            f"Недостаточно прав. Ваш Telegram ID: <code>{actor_id}</code>.",
            chat_id=CHAT_ID,
            thread_id=ADMIN_THREAD_ID,
        )
        return

    if text == "/whoami":
        admin_panel.cancel_pending(actor_id)
        send_message(f"Ваш Telegram ID: <code>{actor_id}</code>", chat_id=CHAT_ID, thread_id=ADMIN_THREAD_ID)
        return

    if admin_panel.is_awaiting_input(actor_id):
        admin_panel.handle_add_user_input(msg, CHAT_ID, ADMIN_THREAD_ID, actor_id)
        return

    # /menu, /start, or anything unrecognized opens the button-driven panel.
    admin_panel.show_main_menu(CHAT_ID, ADMIN_THREAD_ID)


def handle_private_message(msg: dict) -> None:
    chat_id = msg["chat"]["id"]
    user = msg.get("from", {})
    user_id = user.get("id")
    username = user.get("username")
    first_name = user.get("first_name")

    if not state.has_scope(user_id, state.SCOPE_TRANSCRIBE):
        is_new = state.request_access(user_id, username, first_name)
        send_message(
            "Спасибо! Заявка отправлена администраторам, дождитесь подтверждения.",
            chat_id=chat_id,
        )
        if is_new:
            admin_panel.notify_admins_new_request(CHAT_ID, ADMIN_THREAD_ID, user_id, username, first_name)
        return

    if msg.get("text") == "/start":
        send_message("Привет! Пришлите голосовое или аудиофайл — расшифрую.", chat_id=chat_id)
        return

    process_audio(msg, chat_id=chat_id, thread_id=None)


def handle_group_topic_message(msg: dict) -> None:
    # Transcriptions moved to private chat only (2026-08-04): a group topic
    # is visible to every member, so replies here would leak other people's
    # transcripts. Redirect instead of processing.
    if not extract_audio(msg):
        return
    kb = None
    if BOT_USERNAME:
        kb = {"inline_keyboard": [[{"text": "✉️ Написать боту в личку", "url": f"https://t.me/{BOT_USERNAME}"}]]}
    send_message(
        "Транскрибация теперь работает только в личных сообщениях — так расшифровку "
        "видите только вы, а не вся группа. Напишите мне напрямую.",
        chat_id=CHAT_ID,
        thread_id=THREAD_ID,
        reply_to=msg["message_id"],
        reply_markup=kb,
    )


def process_audio(msg: dict, chat_id: int, thread_id: int | None) -> None:
    message_id = msg["message_id"]
    audio = extract_audio(msg)
    if not audio:
        return

    size = audio.get("file_size")
    if size and size > TELEGRAM_DOWNLOAD_LIMIT:
        send_message(
            f"Файл слишком большой: {size / 1024 / 1024:.0f} МБ. "
            f"Telegram отдаёт ботам максимум {TELEGRAM_DOWNLOAD_LIMIT // 1024 // 1024} МБ.\n\n"
            "Разбейте запись на части или сожмите её (например, в моно 32 kbps m4a).",
            chat_id=chat_id,
            thread_id=thread_id,
            reply_to=message_id,
        )
        return

    send_message("Принял, транскрибирую...", chat_id=chat_id, thread_id=thread_id, reply_to=message_id)

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / (audio.get("file_name") or f"{audio['file_id']}.ogg")
        try:
            download_file(audio["file_id"], src)
            text, segments = transcribe(src)
        except FileTooLarge:
            log.warning("file too large for Bot API download")
            send_message(
                f"Файл слишком большой — Telegram отдаёт ботам максимум "
                f"{TELEGRAM_DOWNLOAD_LIMIT // 1024 // 1024} МБ.\n\n"
                "Разбейте запись на части или сожмите её (например, в моно 32 kbps m4a).",
                chat_id=chat_id,
                thread_id=thread_id,
                reply_to=message_id,
            )
            return
        except Exception as e:
            # Never echo the raw exception: requests embeds the full API URL
            # (including the bot token) in its error text.
            log.exception("transcription failed: %s", scrub(e))
            send_message(
                "Не удалось расшифровать запись — техническая ошибка. Попробуйте ещё раз "
                "или сообщите администратору.",
                chat_id=chat_id,
                thread_id=thread_id,
                reply_to=message_id,
            )
            return

    state.increment_transcriptions()
    if not segments:
        send_message(text or "(пустой транскрипт)", chat_id=chat_id, thread_id=thread_id, reply_to=message_id)
        return

    def fmt_ts(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    lines = [f"[{fmt_ts(s['start'])}] {s['text']}" for s in segments]
    content = "\n".join(lines) + "\n\n---\n\nПолный текст:\n" + text
    filename = f"transcription_{datetime.now():%Y-%m-%d_%H-%M}.txt"
    send_document(
        chat_id=chat_id,
        file_bytes=content.encode("utf-8"),
        filename=filename,
        thread_id=thread_id,
        reply_to=message_id,
    )

    # --- Meeting Pipeline: DeepSeek analysis + Notion ---
    try:
        analysis_payload = {
            "transcript": text,
            "title": f"Telegram: {datetime.now():%Y-%m-%d %H:%M}",
        }
        resp = requests.post(
            f"{MEETING_SERVICE_URL}/process-text",
            json=analysis_payload,
            timeout=300,
        )
        if resp.ok:
            result = resp.json()
            if result.get("notion_url"):
                summary = (result.get('summary', '') or '')[:500]
                actions = (result.get('action_items', '') or '')[:500]
                url = result['notion_url']
                msg = (
                    "📋 <b>Саммари:</b>\n" + summary + "\n\n"
                    "✅ <b>Экшен-айтемы:</b>\n" + actions + "\n\n"
                    "📎 <a href=\"" + url + "\">Открыть в Notion</a>"
                )
                send_message(
                    msg,
                    chat_id=chat_id,
                    thread_id=thread_id,
                    reply_to=message_id,
                )
            else:
                log.info("meeting-pipeline: %s", result)
        else:
            log.warning("meeting-pipeline failed: %s", resp.text[:200])
    except Exception as e:
        log.warning("meeting-pipeline error: %s", e)
        # Non-blocking — don't interrupt the user flow


def handle_message(msg: dict) -> None:
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    is_group_topic = chat_id == CHAT_ID and msg.get("message_thread_id") == THREAD_ID
    is_admin_topic = chat_id == CHAT_ID and msg.get("message_thread_id") == ADMIN_THREAD_ID
    is_private = chat.get("type") == "private"

    if is_admin_topic:
        handle_admin_message(msg)
    elif is_private:
        handle_private_message(msg)
    elif is_group_topic:
        handle_group_topic_message(msg)


def main() -> None:
    log.info("transcribe-bot started, polling chat=%s thread=%s admin_thread=%s", CHAT_ID, THREAD_ID, ADMIN_THREAD_ID)
    set_my_commands(CHAT_ID)
    fetch_bot_username()

    offset = None
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
            if offset is not None:
                params["offset"] = offset
            resp = requests.get(f"{API}/getUpdates", params=params, timeout=40)
            resp.raise_for_status()
            updates = resp.json()["result"]
        except requests.RequestException as e:
            log.warning("getUpdates failed: %s", scrub(e))
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            try:
                if "callback_query" in update:
                    admin_panel.handle_callback(update, ADMIN_THREAD_ID, TRANSCRIBE_URL)
                elif "message" in update:
                    handle_message(update["message"])
            except Exception:
                log.exception("failed to handle update %s", update.get("update_id"))


if __name__ == "__main__":
    main()
