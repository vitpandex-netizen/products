"""
UZ IT Jobs — Модуль аутентификации и авторизации (Zero Trust / Private by Default).
Реализует строгую валидацию Telegram WebApp initData и проверку по Whitelist ALLOWED_TELEGRAM_USER_IDS.
"""

import os
import sys
import json
import hmac
import hashlib
import logging
from typing import Optional, Set
from urllib.parse import parse_qsl
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

# Подключение к Vault экосистемы
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared'))
try:
    from vault import get as vault_get
except ImportError:
    def vault_get(k):
        return None

logger = logging.getLogger("uzjobs-auth")

HEADER_INIT_DATA = APIKeyHeader(name="X-Telegram-Init-Data", auto_error=False)
HEADER_DEV_KEY = APIKeyHeader(name="X-Dev-Key", auto_error=False)


def get_bot_token() -> str:
    """Получить токен HH_JOBS_BOT_TOKEN из окружения или Vault."""
    token = os.getenv("HH_JOBS_BOT_TOKEN") or vault_get("HH_JOBS_BOT_TOKEN")
    return (token or "").strip()


def get_allowed_user_ids() -> Set[int]:
    """
    Загрузить белый список Telegram User ID.
    Приоритет: ALLOWED_TELEGRAM_USER_IDS из .env, далее TELEGRAM_USER_ID и TELEGRAM_QA_USER_ID из Vault.
    """
    allowed = set()
    raw_ids = os.getenv("ALLOWED_TELEGRAM_USER_IDS") or vault_get("ALLOWED_TELEGRAM_USER_IDS") or ""
    if raw_ids:
        for item in str(raw_ids).split(","):
            item = item.strip()
            if item.isdigit():
                allowed.add(int(item))

    # Из Vault (владелец и QA)
    owner_id = vault_get("TELEGRAM_USER_ID")
    if owner_id and str(owner_id).strip().isdigit():
        allowed.add(int(str(owner_id).strip()))

    qa_id = vault_get("TELEGRAM_QA_USER_ID")
    if qa_id and str(qa_id).strip().isdigit():
        allowed.add(int(str(qa_id).strip()))

    return allowed


def validate_telegram_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Валидация строки initData Telegram WebApp по криптографическому стандарту Telegram:
    - Парсинг key=value пар
    - Извлечение hash
    - Сортировка остальных пар через \\n
    - secret_key = HMAC_SHA256("WebAppData", bot_token)
    - calculated_hash = HMAC_SHA256(secret_key, data_check_string).hexdigest()
    - Проверка совпадения хэшей
    """
    if not init_data or not bot_token:
        return None

    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            return None

        received_hash = parsed_data.pop("hash")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("[SECURITY ALERT] Invalid Telegram HMAC signature in WebApp request")
            return None

        if "user" in parsed_data:
            parsed_data["user"] = json.loads(parsed_data["user"])

        return parsed_data
    except Exception as e:
        logger.warning(f"[SECURITY ALERT] Error parsing Telegram initData: {e}")
        return None


async def verify_authorized_user(
    request: Request,
    init_data_header: Optional[str] = Security(HEADER_INIT_DATA),
    dev_key_header: Optional[str] = Security(HEADER_DEV_KEY)
) -> dict:
    """
    FastAPI Dependency: Проверяет авторизацию пользователя.
    1. Если передан X-Dev-Key и он совпадает с DEV_ADMIN_KEY из .env — доступ разрешен.
    2. Если передан X-Telegram-Init-Data (или query param tg_init_data):
       - Валидируется HMAC через HH_JOBS_BOT_TOKEN.
       - Проверяется user.id против ALLOWED_TELEGRAM_USER_IDS.
    3. Иначе — немедленный 403 Forbidden.
    """
    dev_admin_key = os.getenv("DEV_ADMIN_KEY", "").strip()
    if dev_admin_key and dev_key_header and dev_key_header.strip() == dev_admin_key:
        return {"auth": "dev_key", "user": {"id": 0, "username": "developer"}}

    # Извлечение init_data (из заголовка или query-параметра)
    init_data = init_data_header or request.query_params.get("tg_init_data") or ""

    bot_token = get_bot_token()
    allowed_ids = get_allowed_user_ids()

    if not bot_token:
        # Если токен бота ещё не загружен в Vault / .env — блокируем доступ по умолчанию (Private by Default)
        logger.error("[SECURITY] HH_JOBS_BOT_TOKEN is not configured. Access denied.")
        raise HTTPException(
            status_code=403,
            detail="Сервис находится в закрытом режиме. Ключ авторизации не настроен."
        )

    validated = validate_telegram_init_data(init_data, bot_token)
    if not validated or "user" not in validated:
        logger.warning(f"[SECURITY ALERT] Unauthorized request to {request.url.path} from {request.client.host}")
        raise HTTPException(
            status_code=403,
            detail="Доступ ограничен. Запуск разрешен только через авторизованный Telegram Mini App."
        )

    user_info = validated["user"]
    user_id = user_info.get("id")

    if not user_id or user_id not in allowed_ids:
        logger.warning(
            f"[SECURITY ALERT] Access denied for unauthorized Telegram user: "
            f"id={user_id}, username={user_info.get('username')}, path={request.url.path}"
        )
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Ваш Telegram ID отсутствует в списке разрешенных участников."
        )

    return {"auth": "telegram", "user": user_info}
