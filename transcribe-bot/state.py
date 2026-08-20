import json
import os
import threading
from pathlib import Path

STATE_PATH = Path(os.environ.get("STATE_PATH", "/data/state.json"))
_lock = threading.Lock()

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_USER = "user"

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_DENIED = "denied"

# Content scopes gate access to a specific service/section, independent of
# admin-panel access. Registry of {key: human label} — add an entry here
# when a new section/service is wired to scope checks; the admin panel
# renders one toggle button per registered scope automatically.
SCOPE_TRANSCRIBE = "transcribe"
SCOPES = {SCOPE_TRANSCRIBE: "🎙 Транскрибация"}


def _owner_ids() -> set[int]:
    return {int(uid) for uid in os.environ.get("ADMIN_USER_IDS", "").split(",") if uid.strip()}


def _blank_user(role: str = ROLE_USER, status: str = STATUS_PENDING) -> dict:
    return {
        "username": None,
        "first_name": None,
        "role": role,
        "scopes": [],
        "status": status,
        "decided_by": None,
    }


def _load() -> dict:
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    else:
        state = {"users": {}, "transcriptions": 0}

    # Env ADMIN_USER_IDS is the source of truth for owners — bootstrap and
    # re-assert on every load so an owner can never be demoted by a bug or a
    # stale state file. Owner status/role is NOT chat-mutable by design.
    changed = False
    for uid in _owner_ids():
        key = str(uid)
        u = state["users"].get(key)
        if u is None:
            state["users"][key] = _blank_user(ROLE_OWNER, STATUS_APPROVED)
            state["users"][key]["scopes"] = [SCOPE_TRANSCRIBE]
            changed = True
        elif u["role"] != ROLE_OWNER or u["status"] != STATUS_APPROVED:
            u["role"] = ROLE_OWNER
            u["status"] = STATUS_APPROVED
            if SCOPE_TRANSCRIBE not in u["scopes"]:
                u["scopes"].append(SCOPE_TRANSCRIBE)
            changed = True
    if changed:
        _save(state)
    return state


def _save(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def display_name(u: dict, user_id: str) -> str:
    if u.get("first_name"):
        return u["first_name"]
    if u.get("username"):
        return f"@{u['username']}"
    return f"id{user_id}"


def get_user(user_id: int) -> dict | None:
    with _lock:
        return _load()["users"].get(str(user_id))


def role_of(user_id: int) -> str | None:
    u = get_user(user_id)
    return u["role"] if u else None


def is_owner(user_id: int) -> bool:
    return role_of(user_id) == ROLE_OWNER


def is_admin(user_id: int) -> bool:
    return role_of(user_id) in (ROLE_OWNER, ROLE_ADMIN)


def has_scope(user_id: int, scope: str) -> bool:
    u = get_user(user_id)
    return bool(u) and u["status"] == STATUS_APPROVED and scope in u["scopes"]


def request_access(user_id: int, username: str | None, first_name: str | None) -> bool:
    """Record a private-chat access request. Returns True the first time this
    user is seen (so callers only ping admins once, not on every retry)."""
    with _lock:
        state = _load()
        key = str(user_id)
        existing = state["users"].get(key)
        if existing is not None:
            if username:
                existing["username"] = username
            if first_name:
                existing["first_name"] = first_name
            _save(state)
            return False
        u = _blank_user()
        u["username"] = username
        u["first_name"] = first_name
        state["users"][key] = u
        _save(state)
        return True


def approve(user_id: int, scope: str, decided_by: int) -> None:
    with _lock:
        state = _load()
        key = str(user_id)
        u = state["users"].setdefault(key, _blank_user())
        u["status"] = STATUS_APPROVED
        if scope not in u["scopes"]:
            u["scopes"].append(scope)
        u["decided_by"] = decided_by
        _save(state)


def deny(user_id: int, decided_by: int) -> None:
    with _lock:
        state = _load()
        key = str(user_id)
        u = state["users"].setdefault(key, _blank_user())
        if u["role"] == ROLE_OWNER:
            return
        u["status"] = STATUS_DENIED
        u["scopes"] = []
        u["decided_by"] = decided_by
        _save(state)


def revoke_scope(user_id: int, scope: str, decided_by: int) -> bool:
    with _lock:
        state = _load()
        u = state["users"].get(str(user_id))
        if not u or u["role"] == ROLE_OWNER or scope not in u["scopes"]:
            return False
        u["scopes"].remove(scope)
        if not u["scopes"]:
            u["status"] = STATUS_DENIED
        u["decided_by"] = decided_by
        _save(state)
        return True


def toggle_scope(user_id: int, scope: str, decided_by: int) -> bool:
    """Flip a single scope on/off for fine-grained per-section access.
    Returns the new state: True if the scope is now granted."""
    with _lock:
        state = _load()
        key = str(user_id)
        u = state["users"].setdefault(key, _blank_user())
        if u["role"] == ROLE_OWNER:
            return True
        if scope in u["scopes"]:
            u["scopes"].remove(scope)
            if not u["scopes"]:
                u["status"] = STATUS_DENIED
            granted = False
        else:
            u["scopes"].append(scope)
            u["status"] = STATUS_APPROVED
            granted = True
        u["decided_by"] = decided_by
        _save(state)
        return granted


def register_user(user_id: int, username: str | None, first_name: str | None) -> bool:
    """Manually add a user known to an admin (vs. request_access, which is
    triggered by the user themself). Returns True if newly created."""
    with _lock:
        state = _load()
        key = str(user_id)
        existing = state["users"].get(key)
        if existing is not None:
            if username:
                existing["username"] = username
            if first_name:
                existing["first_name"] = first_name
            _save(state)
            return False
        u = _blank_user()
        u["username"] = username
        u["first_name"] = first_name
        state["users"][key] = u
        _save(state)
        return True


def set_admin(user_id: int, make_admin: bool) -> bool:
    """Grant/revoke the admin-panel role. Caller must already have verified
    the actor is an owner — owners are the only ones who can promote."""
    with _lock:
        state = _load()
        u = state["users"].get(str(user_id))
        if not u or u["role"] == ROLE_OWNER:
            return False
        u["role"] = ROLE_ADMIN if make_admin else ROLE_USER
        _save(state)
        return True


def list_users() -> dict:
    with _lock:
        return _load()["users"]


def increment_transcriptions() -> None:
    with _lock:
        state = _load()
        state["transcriptions"] = state.get("transcriptions", 0) + 1
        _save(state)


def get_stats() -> dict:
    with _lock:
        state = _load()
        users = state["users"]
        return {
            "transcriptions": state.get("transcriptions", 0),
            "total_users": len(users),
            "approved": sum(1 for u in users.values() if u["status"] == STATUS_APPROVED),
            "pending": sum(1 for u in users.values() if u["status"] == STATUS_PENDING),
        }
