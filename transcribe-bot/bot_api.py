import logging
import os

import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
# When TELEGRAM_API_ROOT is set the bot talks to a self-hosted telegram-bot-api
# container (lifts the download limit from 20 MB to 2000 MB). Falls back to the
# official endpoint so the bot still works without the local server.
_API_ROOT = os.environ.get("TELEGRAM_API_ROOT", "https://api.telegram.org").rstrip("/")
API = f"{_API_ROOT}/bot{BOT_TOKEN}"
_FILE_ROOT = f"{_API_ROOT}/file/bot{BOT_TOKEN}"

# In local mode the self-hosted server handles any file size; keep 20 MB only
# as the fallback limit for the official endpoint.
TELEGRAM_DOWNLOAD_LIMIT = 2000 * 1024 * 1024 if "TELEGRAM_API_ROOT" in os.environ else 20 * 1024 * 1024

log = logging.getLogger("transcribe-bot.api")


MAX_MESSAGE_LEN = 4096


class FileTooLarge(Exception):
    """Raised when a file exceeds what the Bot API will hand us."""


def scrub(text) -> str:
    """Strip the bot token out of anything user- or log-facing. requests puts
    the full request URL in its exception text, which would otherwise leak the
    token into chat messages and logs."""
    return str(text).replace(BOT_TOKEN, "<TOKEN>")


def send_message(
    text: str,
    chat_id: int,
    thread_id: int | None = None,
    reply_to: int | None = None,
    reply_markup: dict | None = None,
) -> dict | None:
    chunks = [text[i : i + MAX_MESSAGE_LEN] for i in range(0, len(text), MAX_MESSAGE_LEN)] or [""]
    last: dict | None = None
    for i, chunk in enumerate(chunks):
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"}
        if thread_id is not None:
            payload["message_thread_id"] = thread_id
        if reply_to and i == 0:
            payload["reply_to_message_id"] = reply_to
        if reply_markup is not None and i == len(chunks) - 1:
            payload["reply_markup"] = reply_markup
        resp = requests.post(f"{API}/sendMessage", json=payload, timeout=15)
        if not resp.ok:
            log.warning("sendMessage failed: %s", resp.text)
        else:
            last = resp.json().get("result")
    return last


def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    resp = requests.post(f"{API}/editMessageText", json=payload, timeout=15)
    if not resp.ok:
        log.warning("editMessageText failed: %s", resp.text)


def answer_callback(callback_query_id: str, text: str | None = None, show_alert: bool = False) -> None:
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
        payload["show_alert"] = show_alert
    requests.post(f"{API}/answerCallbackQuery", json=payload, timeout=10)


def send_document(
    chat_id: int,
    file_bytes: bytes,
    filename: str,
    caption: str | None = None,
    thread_id: int | None = None,
    reply_to: int | None = None,
) -> dict | None:
    payload: dict = {"chat_id": chat_id}
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    if reply_to is not None:
        payload["reply_to_message_id"] = reply_to
    if caption:
        payload["caption"] = caption
    files = {"document": (filename, file_bytes, "text/plain")}
    resp = requests.post(f"{API}/sendDocument", data=payload, files=files, timeout=30)
    if not resp.ok:
        log.warning("sendDocument failed: %s", resp.text)
        return None
    return resp.json().get("result")


def download_file(file_id: str, dest) -> None:
    r = requests.get(f"{API}/getFile", params={"file_id": file_id}, timeout=15)
    if r.status_code == 400:
        # The Bot API refuses getFile for anything over 20 MB, which is the
        # common case for hour-long recordings — report it as a size problem
        # rather than a raw HTTP error.
        raise FileTooLarge(r.json().get("description", "file is too big"))
    r.raise_for_status()
    file_path = r.json()["result"]["file_path"]
    # Local telegram-bot-api returns absolute paths (/var/lib/...);
    # strip the leading slash so the URL path joins cleanly.
    if file_path.startswith("/"):
        file_path = file_path.lstrip("/")
    file_url = f"{_FILE_ROOT}/{file_path}"
    with requests.get(file_url, stream=True, timeout=1800) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)


def set_my_commands(chat_id: int) -> None:
    """Registers the '/' command menu. Scoped to this one chat, so DM users
    and other chats/groups the bot might join don't see admin-only commands."""
    commands = [
        {"command": "menu", "description": "Открыть меню администратора"},
        {"command": "whoami", "description": "Мой Telegram ID"},
    ]
    resp = requests.post(
        f"{API}/setMyCommands",
        json={"commands": commands, "scope": {"type": "chat", "chat_id": chat_id}},
        timeout=15,
    )
    if not resp.ok:
        log.warning("setMyCommands (chat) failed: %s", resp.text)

    resp = requests.post(
        f"{API}/setMyCommands",
        json={
            "commands": [{"command": "start", "description": "Запросить доступ / начать"}],
            "scope": {"type": "all_private_chats"},
        },
        timeout=15,
    )
    if not resp.ok:
        log.warning("setMyCommands (private) failed: %s", resp.text)
