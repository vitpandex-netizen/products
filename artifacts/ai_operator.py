#!/usr/bin/env python3
"""AI Phone Operator — ITOPS L1 Support.
FastAPI webhook для Twilio: принимает звонки, STT → LLM → TTS.
"""
import os, json, logging, asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse, Response
import uvicorn
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Record

# --- Config ---
PORT = int(os.getenv("PORT", "3100"))
USE_CASE = os.getenv("USE_CASE", "itops")  # itops or dental
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
VAULT_SCRIPT = os.path.expanduser("~/.secure/vault.py")

# --- Logging ---
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
log = logging.getLogger("ai-operator")

# --- Vault helper ---
def vault_get(key):
    try:
        import subprocess
        r = subprocess.run(["python3", VAULT_SCRIPT, "get", key], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else None
    except: return None

# --- LLM helper ---
def call_llm(system_prompt, user_text):
    """Call LLM via OpenRouter."""
    import requests
    api_key = vault_get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "Извините, AI временно недоступен. Пожалуйста, повторите позже."
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-v4-flash",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=10,
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        log.error(f"LLM error: {e}")
        return None

# --- System prompts ---
SYSTEM_PROMPTS = {
    "itops": """Ты — AI-оператор первой линии IT-поддержки. Твои правила:
1. Узнай имя сотрудника и проблему
2. Попробуй дать простое решение (перезагрузить, проверить кабель, сменить пароль)
3. Если не можешь решить — создай тикет и скажи номер тикета
4. Говори кратко, по делу, на русском языке
5. Никогда не проси перезвонить — реши проблему сейчас
6. Если проблема критическая (сервер не работает, данные потеряны) — скажи что передаёшь срочно инженеру

Примеры решений:
- "Не работает интернет" → "Проверьте подключение кабеля, перезагрузите роутер. Если не помогло — создаю тикет."
- "Забыл пароль" → "Какой у вас email? Я отправлю ссылку для сброса."
- "Не открывается программа" → "Перезагрузите компьютер. Если не помогло — создаю тикет для администратора."
""",
    "dental": """Ты — AI-оператор стоматологической клиники. Твои правила:
1. Узнай имя пациента и что его беспокоит
2. Предложи запись на приём (ближайшее свободное время)
3. Ответь на вопросы о ценах, услугах, графике работы
4. Говори приветливо, вежливо, на русском языке
5. Если пациент в боли — предложи запись сегодня
6. Запиши контактный телефон пациента

Примеры:
- "Зуб болит" → "Запишем вас сегодня на 15:00 или завтра на 10:00?"
- "Сколько стоит чистка?" → "Профессиональная чистка — 150 000 сум. Хотите записаться?"
- "Где вы находитесь?" → "Мы на улице Амира Темура, 15. Работаем с 9:00 до 20:00."
""",
}

# --- Twilio webhook ---
app = FastAPI(title="AI Phone Operator")

@app.get("/")
async def root():
    return {"status": "ok", "use_case": USE_CASE, "port": PORT}

@app.get("/health")
async def health():
    return {"status": "ok", "use_case": USE_CASE}

@app.post("/voice", response_class=PlainTextResponse)
async def handle_voice():
    """Entry point: Twilio calls this when someone calls the number."""
    prompt = SYSTEM_PROMPTS.get(USE_CASE, SYSTEM_PROMPTS["itops"])
    resp = VoiceResponse()
    
    if USE_CASE == "itops":
        greeting = "Здравствуйте! Это AI-оператор IT-поддержки. Назовите ваше имя и опишите проблему."
    else:
        greeting = "Здравствуйте! Это стоматологическая клиника. Как я могу вам помочь?"
    
    gather = Gather(input="speech", action="/process", method="POST", speechTimeout="auto", language="ru-RU", timeout=5)
    gather.say(greeting, voice="Polina", language="ru-RU")
    resp.append(gather)
    resp.say("Извините, я вас не расслышал. Пожалуйста, повторите.", voice="Polina", language="ru-RU")
    resp.redirect("/voice")
    return str(resp)

@app.post("/process", response_class=PlainTextResponse)
async def process_speech(SpeechResult: str = Form(None), CallStatus: str = Form(None)):
    """Process the caller's speech and respond."""
    prompt = SYSTEM_PROMPTS.get(USE_CASE, SYSTEM_PROMPTS["itops"])
    resp = VoiceResponse()
    
    if not SpeechResult:
        resp.say("Извините, я вас не понял. Пожалуйста, повторите.", voice="Polina", language="ru-RU")
        resp.redirect("/voice")
        return str(resp)
    
    # Call LLM
    answer = call_llm(prompt, SpeechResult)
    
    if not answer:
        answer = "Извините, произошла техническая ошибка. Пожалуйста, перезвоните позже."
    
    log.info(f"Caller: {SpeechResult[:100]}")
    log.info(f"AI: {answer[:100]}")
    
    # Ask if they need anything else
    gather = Gather(input="speech", action="/process", method="POST", speechTimeout="auto", language="ru-RU", timeout=5)
    gather.say(answer + " Могу я ещё чем-то помочь?", voice="Polina", language="ru-RU")
    resp.append(gather)
    
    # If no response, say goodbye
    resp.say("Спасибо за обращение! Всего доброго.", voice="Polina", language="ru-RU")
    resp.hangup()
    return str(resp)

@app.post("/transcribe", response_class=PlainTextResponse)
async def transcribe_recording():
    """Webhook for recording transcription (Twilio Record verb)."""
    # This is called after a recording is made
    # Can be used to send transcript to Telegram
    return str(VoiceResponse().hangup())

if __name__ == "__main__":
    log.info(f"Starting AI Phone Operator on port {PORT}")
    log.info(f"Use case: {USE_CASE}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)