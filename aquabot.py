#!/usr/bin/env python3
"""
🎙️ AquaBot — Voice-to-Text ассистент для Telegram
Принимает голосовые сообщения → Whisper транскрибация → AI очистка → чистый текст

MVP коммерческого продукта (аналог Aqua Voice)
"""
import json, logging, os, tempfile, urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("aquabot")

# Конфиг
BOT_TOKEN = os.getenv("AQUABOT_TOKEN") or ""
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004297012607")
THREAD_ID = os.getenv("AQUABOT_THREAD_ID", "397")  # DataCore Signals topic
WHISPER_API = os.getenv("WHISPER_API", "http://127.0.0.1:8000")
AQUABOT_PORT = int(os.getenv("AQUABOT_PORT", "8765"))

# === Telegram API helpers ===
def tg_url(method): return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

def send_message(text, chat_id=CHAT_ID, thread_id=THREAD_ID):
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "message_thread_id": int(thread_id) if thread_id else None,
    }).encode()
    req = urllib.request.Request(tg_url("sendMessage"), data=payload, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())

def get_file_path(file_id):
    resp = json.loads(urllib.request.urlopen(tg_url(f"getFile?file_id={file_id}"), timeout=10).read())
    return resp["result"]["file_path"]

# === Voice processing ===
def transcribe_audio(audio_path: str) -> str:
    """Send audio to Whisper service and get transcription"""
    import requests
    with open(audio_path, "rb") as f:
        resp = requests.post(f"{WHISPER_API}/transcribe", files={"file": f}, timeout=120)
    resp.raise_for_status()
    return resp.json().get("text", "")

def clean_text(raw_text: str) -> str:
    """AI cleaning: remove fillers, structure text"""
    # Simple cleaning (v1 — rule-based)
    import re
    text = raw_text.strip()
    # Remove repeated fillers
    text = re.sub(r'\b(ну|типа|как бы|ээ|мм|так сказать)\b', '', text, flags=re.IGNORECASE)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    return text

# === Webhook server ===
from http.server import HTTPServer, BaseHTTPRequestHandler

class BotHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        
        msg = body.get("message", {})
        chat_id = msg.get("chat", {}).get("id", CHAT_ID)
        thread_id = msg.get("message_thread_id", THREAD_ID)
        
        # Handle voice messages
        voice = msg.get("voice")
        if voice:
            file_id = voice["file_id"]
            try:
                file_path = get_file_path(file_id)
                audio_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                
                # Download audio
                local_path = f"/tmp/aquabot_{file_id}.ogg"
                urllib.request.urlretrieve(audio_url, local_path)
                
                # Transcribe
                raw = transcribe_audio(local_path)
                
                # Clean
                clean = clean_text(raw)
                
                # Reply
                reply = f"🎙️ <b>Распознано:</b>\n{clean}\n\n<i>Исходный текст:</i> {raw[:200]}"
                send_message(reply, chat_id, thread_id)
                log.info(f"Voice processed: {clean[:60]}...")
            except Exception as e:
                send_message(f"❌ Ошибка: {e}", chat_id, thread_id)
                log.error(f"Voice error: {e}")
            finally:
                Path(local_path).unlink(missing_ok=True)
        
        # Handle text commands
        text = msg.get("text", "")
        if text == "/start":
            send_message(
                "🎙️ <b>AquaBot — Voice to Text</b>\n\n"
                "Отправь голосовое сообщение — я превращу его в чистый текст.\n\n"
                "Команды:\n"
                "/status — проверить статус",
                chat_id, thread_id
            )
        elif text == "/status":
            send_message("✅ AquaBot работает", chat_id, thread_id)
        
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args): pass

# === Main ===
def set_webhook():
    """Register webhook with Telegram"""
    # First remove old webhook
    urllib.request.urlopen(tg_url("deleteWebhook"), timeout=10)
    
    # ngrok or direct URL needed for production
    webhook_url = f"http://127.0.0.1:{AQUABOT_PORT}"
    payload = json.dumps({"url": webhook_url}).encode()
    req = urllib.request.Request(tg_url("setWebhook"), data=payload, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    log.info(f"Webhook set: {resp}")
    return resp

def get_updates(offset=0):
    """Poll for updates (simpler than webhook for local testing)"""
    try:
        req = urllib.request.urlopen(
            tg_url(f"getUpdates?timeout=30&offset={offset}"), timeout=35
        )
        return json.loads(req.read()).get("result", [])
    except Exception as e:
        log.warning(f"Poll error: {e}")
        return []

def polling_mode():
    """Run in polling mode (no webhook needed)"""
    log.info("AquaBot started in polling mode")
    send_message("🎙️ AquaBot запущен", CHAT_ID, THREAD_ID)
    
    offset = 0
    while True:
        updates = get_updates(offset)
        for upd in updates:
            offset = upd["update_id"] + 1
            msg = upd.get("message", {})
            chat_id = msg.get("chat", {}).get("id", CHAT_ID)
            thread_id = msg.get("message_thread_id", THREAD_ID)
            
            voice = msg.get("voice")
            if voice:
                file_id = voice["file_id"]
                try:
                    file_path = get_file_path(file_id)
                    audio_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    
                    local_path = f"/tmp/aquabot_{file_id}.ogg"
                    urllib.request.urlretrieve(audio_url, local_path)
                    
                    raw = transcribe_audio(local_path)
                    clean = clean_text(raw)
                    
                    reply = f"🎙️ <b>Распознано:</b>\n{clean}\n\n┈ {raw[:150]}"
                    send_message(reply, chat_id, thread_id)
                    log.info(f"Voice: {clean[:60]}...")
                except Exception as e:
                    send_message(f"❌ Ошибка: {str(e)[:100]}", chat_id, thread_id)
                    log.error(f"Error: {e}")
                finally:
                    Path(local_path).unlink(missing_ok=True)

if __name__ == "__main__":
    import sys
    if "--webhook" in sys.argv:
        server = HTTPServer(("0.0.0.0", AQUABOT_PORT), BotHandler)
        set_webhook()
        log.info(f"Webhook server on :{AQUABOT_PORT}")
        server.serve_forever()
    else:
        polling_mode()