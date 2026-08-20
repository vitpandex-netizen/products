import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("transcribe-service")

MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "medium")
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

app = FastAPI()
transcribe_lock = asyncio.Lock()
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)


def convert_to_wav(src: Path, dst: Path) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(dst)],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="ignore"))


def run_transcribe(wav_path: str):
    segments, _info = model.transcribe(wav_path, language="ru")
    segments = [
        {"start": s.start, "end": s.end, "text": s.text} for s in segments
    ]
    text = "".join(s["text"] for s in segments).strip()
    return text, segments


@app.post("/transcribe")
async def transcribe(file: UploadFile):
    filename = file.filename or "input"
    log.info("received file: %s", filename)
    with tempfile.TemporaryDirectory() as tmp:
        src_path = Path(tmp) / filename
        # Stream to disk in 1 MB chunks — avoids loading the whole file into RAM
        with open(src_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                out.write(chunk)
        size_mb = src_path.stat().st_size / 1024 / 1024
        log.info("saved %.1f MB to %s", size_mb, src_path)

        wav_path = Path(tmp) / "audio.wav"
        try:
            convert_to_wav(src_path, wav_path)
        except RuntimeError as e:
            log.error("ffmpeg failed: %s", e)
            raise HTTPException(status_code=400, detail=f"ffmpeg failed: {e}")
        log.info("converted to wav: %.1f MB", wav_path.stat().st_size / 1024 / 1024)

        try:
            async with transcribe_lock:
                log.info("transcription started")
                text, segments = await asyncio.to_thread(run_transcribe, str(wav_path))
                log.info("transcription done: %d segments, %d chars", len(segments), len(text))
        except Exception:
            log.exception("transcription failed")
            raise HTTPException(status_code=500, detail="transcription failed")

    return {"text": text, "segments": segments}


@app.get("/health")
async def health():
    return {"status": "ok"}
