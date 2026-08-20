#!/usr/bin/env python3
"""
meeting_service.py — HTTP-сервис для пайплайна встреч
POST /process-audio   — аудиофайл → транскрипция → DeepSeek → Notion
POST /process-text    — текст транскрипта → DeepSeek → Notion
GET  /health          — health check

Используется:
- transcribe-bot (Telegram) вызывает после транскрипции
- watch-режим вызывает для новых файлов
- curl / Postman для ручной обработки
"""

import json
import uuid
import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("meeting-service")

# === Config ===
VAULT_SCRIPT = os.path.expanduser("~/.secure/vault.py")
NOTION_DATA_SOURCE = "e3fb4445-2bd8-47ce-ae00-f8247dd9b145"
TRANSCRIBE_SERVICE = os.environ.get("TRANSCRIBE_SERVICE_URL", "http://transcribe-service:8000")
WHISPER_MODEL = "small"
OPENROUTER_MODEL = "deepseek/deepseek-v4-flash"
OUTPUT_DIR = Path("/tmp/meeting_pipeline")
PORT = int(os.environ.get("MEETING_SERVICE_PORT", "8001"))


def get_openrouter_key():
    result = subprocess.run(
        ["python3", VAULT_SCRIPT, "get", "OPENROUTER_API_KEY"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def transcribe_audio(audio_path: Path) -> str:
    """Transcribe via builtin-transcribe (local Whisper)"""
    output_path = OUTPUT_DIR / f"{audio_path.stem}_transcript.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = subprocess.run(
        ["interpreter-app", "tools", "builtin-transcribe", "transcribe_audio", "--json",
         json.dumps({
             "audioPath": str(audio_path.resolve()),
             "model": WHISPER_MODEL,
             "outputPath": str(output_path)
         })],
        capture_output=True, text=True, timeout=900
    )
    
    if not output_path.exists():
        raise RuntimeError(f"Transcription failed: {result.stderr[:500]}")
    
    return output_path.read_text(encoding='utf-8', errors='replace')


def analyze_with_deepseek(transcript: str, title: str = "") -> dict:
    """Send transcript to DeepSeek for structured analysis"""
    api_key = get_openrouter_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found")
    
    # Truncate if too long
    if len(transcript) > 15000:
        transcript = transcript[:15000] + "\n\n[...транскрипт обрезан до 15000 символов]"
    
    prompt = f"""Ты — AI-ассистент для обработки встреч. Прочитай транскрипт и составь структурированный отчёт.

Название встречи: {title or 'Не указано'}

Ответь строго в формате JSON (без markdown-обёртки, без лишнего текста):
{{
  "summary": "Краткое саммари (3-5 предложений, на русском)",
  "extended_summary": "Подробное саммари с основными темами (до 1500 символов)",
  "bullet_notes": "- Ключевой тезис 1\\n- Ключевой тезис 2\\n...",
  "action_items": "- **Имя**: Задача\\n- **Имя**: Задача\\n...",
  "participants_guessed": ["Имя1", "Имя2"],
  "type_guessed": "Внутренняя/Внешняя/1:1/Собеседование/Вебинар",
  "tags_guessed": ["важное", "решения", "проект", "клиент"]
}}

Правила:
- Если экшен-айтемов нет → "action_items": "Нет конкретных задач"
- Если участники не ясны → пустой массив
- type_guessed — один из разрешённых вариантов
- tags_guessed — только из списка: важное, клиент, проект, решения

--- ТРАНСКРИПТ ---
{transcript}"""

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 3000
    }
    
    result = subprocess.run(
        ["curl", "-s", "https://openrouter.ai/api/v1/chat/completions",
         "-H", f"Authorization: Bearer {api_key}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=120
    )
    
    resp = json.loads(result.stdout)
    content = resp['choices'][0]['message']['content']
    
    # Remove markdown code block if present
    if content.strip().startswith('```'):
        lines = content.strip().split('\n')
        content = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
    
    return json.loads(content.strip())


def save_to_notion(analysis: dict, title: str = "", audio_path: str = "",
                   transcript_path: str = "", host: str = "",
                   meeting_type: str = "", participants: list = None,
                   tags: list = None, chat_id: int = None) -> dict:
    """Save meeting analysis to Notion queue file (processed by agent)"""
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    
    final_type = meeting_type or analysis.get('type_guessed', '')
    final_tags = tags or analysis.get('tags_guessed', [])
    final_ppl = participants or analysis.get('participants_guessed', [])
    
    # Build properties
    properties = {
        'Meeting Title': title or Path(audio_path).stem if audio_path else 'Untitled Meeting',
        'date:Date & Time:start': now,
        'date:Date & Time:is_datetime': 1,
        'Summary': analysis.get('summary', ''),
        'Extended Summary': analysis.get('extended_summary', ''),
        'Bullet Notes': analysis.get('bullet_notes', ''),
        'Action Items': analysis.get('action_items', ''),
        'Status': 'Новая'
    }
    
    if host:
        properties['Meeting Host'] = host
    if final_type:
        properties['Type'] = final_type
    if final_ppl:
        properties['Participants'] = final_ppl
    if final_tags:
        properties['Tags'] = final_tags
    if transcript_path:
        properties['Transcript Link'] = f"file://{transcript_path}"
    
    page_payload = {
        'parent': {'data_source_id': NOTION_DATA_SOURCE},
        'pages': [{'properties': properties}]
    }
    
    # Save to queue file for agent processing
    queue_dir = OUTPUT_DIR / "notion_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_file = queue_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}.json"
    queue_file.write_text(json.dumps(page_payload, ensure_ascii=False, indent=2), encoding='utf-8')
    
    log.info(f"Notion payload saved to queue: {queue_file.name}")
    return {"pages": [{"url": f"queue://{queue_file.name}"}]}


def process_audio_file(audio_path: str, title: str = "", host: str = "", 
                       meeting_type: str = "", participants: list = None,
                       tags: list = None) -> dict:
    """Full pipeline: audio → transcribe → analyze → Notion"""
    log.info(f"Processing audio: {audio_path}")
    
    # Step 1: Transcribe
    transcript = transcribe_audio(Path(audio_path))
    log.info(f"Transcription done: {len(transcript)} chars")
    
    # Save transcript
    transcript_path = OUTPUT_DIR / f"{Path(audio_path).stem}_transcript.txt"
    transcript_path.write_text(transcript, encoding='utf-8')
    
    # Step 2: Analyze
    analysis = analyze_with_deepseek(transcript, title)
    log.info(f"Analysis done: {analysis.get('summary', '')[:100]}")
    
    # Save analysis
    analysis_path = OUTPUT_DIR / f"{Path(audio_path).stem}_analysis.json"
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # Step 3: Save to Notion
    notion_result = save_to_notion(
        analysis, title=title, audio_path=audio_path,
        transcript_path=str(transcript_path),
        host=host, meeting_type=meeting_type,
        participants=participants, tags=tags
    )
    log.info(f"Notion: {notion_result.get('pages', [{}])[0].get('url', 'done')}")
    
    return {
        "status": "ok",
        "title": title or Path(audio_path).stem,
        "transcript_length": len(transcript),
        "summary": analysis.get("summary", ""),
        "action_items": analysis.get("action_items", ""),
        "notion_url": notion_result.get("pages", [{}])[0].get("url", ""),
        "analysis": analysis
    }


def process_text(transcript: str, title: str = "", host: str = "",
                 meeting_type: str = "", participants: list = None,
                 tags: list = None) -> dict:
    """Pipeline: text → analyze → Notion (for already-transcribed texts)"""
    log.info(f"Processing text: {title or 'untitled'}")
    
    # Step 1: Analyze
    analysis = analyze_with_deepseek(transcript, title)
    log.info(f"Analysis done: {analysis.get('summary', '')[:100]}")
    
    # Save transcript and analysis
    safe_name = title or f"meeting_{datetime.now():%Y%m%d_%H%M%S}"
    transcript_path = OUTPUT_DIR / f"{safe_name}_transcript.txt"
    transcript_path.write_text(transcript, encoding='utf-8')
    
    analysis_path = OUTPUT_DIR / f"{safe_name}_analysis.json"
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # Step 2: Save to Notion
    notion_result = save_to_notion(
        analysis, title=title, transcript_path=str(transcript_path),
        host=host, meeting_type=meeting_type,
        participants=participants, tags=tags
    )
    
    return {
        "status": "ok",
        "title": title or safe_name,
        "summary": analysis.get("summary", ""),
        "action_items": analysis.get("action_items", ""),
        "notion_url": notion_result.get("pages", [{}])[0].get("url", ""),
        "analysis": analysis
    }


class MeetingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok", "service": "meeting-pipeline",
                "whisper_model": WHISPER_MODEL, "ai_model": OPENROUTER_MODEL
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b'{}'
        
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return
        
        try:
            if parsed.path == '/process-audio':
                result = process_audio_file(
                    data.get('audio_path', ''),
                    title=data.get('title', ''),
                    host=data.get('host', ''),
                    meeting_type=data.get('type', ''),
                    participants=data.get('participants'),
                    tags=data.get('tags')
                )
            elif parsed.path == '/process-text':
                result = process_text(
                    data.get('transcript', ''),
                    title=data.get('title', ''),
                    host=data.get('host', ''),
                    meeting_type=data.get('type', ''),
                    participants=data.get('participants'),
                    tags=data.get('tags')
                )
            else:
                self._send_error(404, "Not found")
                return
            
            self._send_json(200, result)
        except Exception as e:
            log.exception("Processing failed")
            self._send_error(500, str(e))
    
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def _send_error(self, status, message):
        self._send_json(status, {"status": "error", "message": message})
    
    def log_message(self, format, *args):
        log.info(format, *args)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(('0.0.0.0', PORT), MeetingHandler)
    log.info(f"🤖 Meeting Pipeline Service running on port {PORT}")
    log.info(f"   POST /process-audio  — аудио → транскрипция → DeepSeek → Notion")
    log.info(f"   POST /process-text   — текст → DeepSeek → Notion")
    log.info(f"   GET  /health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")


if __name__ == '__main__':
    main()
