"""
Unified LLM router — выбор модели по типу задачи.
Ling-2.6-flash: текст, код, агенты ($0.01/$0.03 за 1M tok)
Qwen3.7 Flash: зрение, изображения ($0.03/$0.13 за 1M tok)
DeepSeek V4 Pro: сложные задачи ($0.34/$0.68 за 1M tok)
Ollama fallback: qwen3:1.7b (локально, бесплатно)
"""
import os, logging, time
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Model registry ──────────────────────────────────────────
MODELS = {
    "text":   "inclusionai/ling-2.6-flash",      # $0.01/$0.03 — дёшево, быстро
    "vision": "qwen/qwen3.7-flash",              # $0.03/$0.13 — мультимодальная
    "heavy":  "deepseek/deepseek-v4-pro",         # $0.34/$0.68 — сложные задачи
    "code":   "inclusionai/ling-2.6-flash",       # тот же — отличный для кода
    "eval":   "inclusionai/ling-2.6-flash",       # оценка/скоринг
}
FALLBACK_MODEL = "deepseek/deepseek-v4-flash"     # если что-то не так
OLLAMA_MODEL = "qwen3:1.7b"                       # локальный фоллбэк (только если нет сети)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/chat"

# ── API key ─────────────────────────────────────────────────
def _get_api_key():
    """Get OpenRouter API key from vault -> env."""
    # Vault first
    import subprocess
    try:
        r = subprocess.run(
            ['/usr/bin/python3', os.path.expanduser('~/.secure/vault.py'), 'get', 'OPENROUTER_API_KEY'],
            capture_output=True, text=True, timeout=5
        )
        val = r.stdout.strip()
        if val:
            return val
    except Exception:
        pass
    # .env fallback
    return os.getenv("OPENROUTER_API_KEY", "")


# ── Main LLM call ──────────────────────────────────────────
def llm(prompt: str,
        task: str = "text",
        model: str | None = None,
        images: list[str] | None = None,
        max_tokens: int = 800,
        temperature: float = 0.5,
        retries: int = 3,
        timeout: int = 60) -> str | None:
    """
    Unified LLM call.

    Args:
        prompt:      текстовый промпт
        task:        "text" | "vision" | "heavy" | "code" | "eval"
        model:       явная модель (переопределяет task)
        images:      список URL/base64 изображений (автоматически -> vision)
        max_tokens:  максимум токенов ответа
        temperature: температура
        retries:     число повторов
        timeout:     таймаут запроса
    Returns:
        Строка ответа или None
    """
    # Auto-detect vision
    if images and not model:
        task = "vision"

    chosen_model = model or MODELS.get(task, FALLBACK_MODEL)
    api_key = _get_api_key()

    if not api_key:
        logger.warning("No OPENROUTER_API_KEY, trying Ollama fallback")
        return _ollama_call(prompt, max_tokens, temperature)

    # Build messages
    messages = _build_messages(prompt, images)

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": chosen_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=timeout,
            )
            if r.status_code == 200:
                data = r.json()
                choices = data.get("choices", [])
                if not choices:
                    # OpenRouter может вернуть error в теле
                    err = data.get("error", {}) or data.get("error", "")
                    logger.warning(f"LLM 200 but no choices [{chosen_model}]: {err}")
                    continue
                content = choices[0].get("message", {}).get("content", "")
                if content:
                    logger.debug(f"LLM OK [{chosen_model}] {len(content)} chars")
                    return content.strip()
                else:
                    # Может быть refusal или finish_reason
                    finish = choices[0].get("finish_reason", "?")
                    refusal = choices[0].get("message", {}).get("refusal", "")
                    logger.warning(f"LLM 200 empty content [{chosen_model}] finish={finish} refusal={refusal}")
                    if refusal:
                        return f"[Refused: {refusal}]"
                    continue

            # Rate limit — подождать и повторить
            if r.status_code == 429:
                wait = min(30, 5 * attempt)
                logger.warning(f"Rate limited, wait {wait}s (attempt {attempt})")
                time.sleep(wait)
                continue

            logger.warning(f"LLM error [{chosen_model}] status={r.status_code} (attempt {attempt})")

        except requests.exceptions.Timeout:
            logger.warning(f"LLM timeout [{chosen_model}] (attempt {attempt})")
        except Exception as e:
            logger.warning(f"LLM fail [{chosen_model}] (attempt {attempt}): {e}")

        if attempt < retries:
            time.sleep(3)

    # All retries failed — DeepSeek V4 Flash fallback (через OpenRouter)
    if chosen_model != FALLBACK_MODEL:
        logger.info(f"Trying fallback model {FALLBACK_MODEL}")
        return llm(prompt, model=FALLBACK_MODEL, max_tokens=max_tokens,
                    temperature=temperature, retries=1, timeout=timeout)

    # DeepSeek V4 Flash тоже не сработал — проверяем сеть
    if not _check_network():
        logger.info("No network — trying local Ollama as last resort")
        return _ollama_call(prompt, max_tokens, temperature)

    logger.warning("All models failed, network is up")
    return None


# ── Message builder ─────────────────────────────────────────
def _build_messages(prompt: str, images: list[str] | None = None) -> list[dict]:
    """Build OpenRouter-compatible messages with optional images."""
    if not images:
        return [{"role": "user", "content": prompt}]

    # Vision: multimodal content
    content = [{"type": "text", "text": prompt}]
    for img in images:
        if img.startswith("data:"):
            content.append({"type": "image_url", "image_url": {"url": img}})
        elif img.startswith("http"):
            content.append({"type": "image_url", "image_url": {"url": img}})
        else:
            # Assume base64 JPEG
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    return [{"role": "user", "content": content}]


# ── Ollama fallback ─────────────────────────────────────────
def _check_network() -> bool:
    """Проверка доступности сети (OpenRouter API)."""
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=5)
        return r.status_code in (200, 401, 429)
    except Exception:
        return False


def _ollama_call(prompt: str, max_tokens: int = 800, temperature: float = 0.5) -> str | None:
    """
    Local Ollama fallback (text only).
    Ограничения для M1 Air 8GB — чтобы не вешать комп:
    - max 400 токенов вывода (обрезаем если больше)
    - контекст 4096 (не 40K)
    - 1 поток GPU (low_vram)
    - таймаут 90 сек — если завис, убиваем
    - промпт обрезается до 2000 символов
    """
    # Обрезаем промпт чтобы не раздувать контекст
    safe_prompt = prompt[:2000] if len(prompt) > 2000 else prompt
    # Ограничиваем токены вывода
    safe_tokens = min(max_tokens, 400)

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": safe_prompt}],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": safe_tokens,
                    "num_ctx": 2048,        # минимальный контекст — RAM экономия
                    "num_thread": 2,        # только 2 потока CPU
                    "num_gpu": 1,           # 1 слой на GPU — остальное на CPU
                    "low_vram": True,       # режим экономии VRAM
                },
            },
            timeout=30,
        )
        if r.status_code == 200:
            resp_content = r.json().get("message", {}).get("content", "")
            if resp_content:
                logger.info(f"Ollama OK [{OLLAMA_MODEL}] {len(resp_content)} chars (local fallback)")
                return resp_content.strip()
    except requests.exceptions.Timeout:
        logger.warning(f"Ollama timeout (30s) — модель слишком медленная, пропускаем")
    except Exception as e:
        logger.error(f"Ollama fail: {e}")
    return None


# ── Convenience wrappers ────────────────────────────────────
def ask(prompt: str, **kw) -> str | None:
    """Quick text query."""
    return llm(prompt, task="text", **kw)

def see(prompt: str, images: list[str], **kw) -> str | None:
    """Vision query — analyze images."""
    return llm(prompt, task="vision", images=images, **kw)

def think(prompt: str, **kw) -> str | None:
    """Heavy reasoning query."""
    return llm(prompt, task="heavy", **kw)

def evaluate(prompt: str, temperature: float = 0.3, **kw) -> str | None:
    """Evaluation/scoring query."""
    return llm(prompt, task="eval", temperature=temperature, **kw)
