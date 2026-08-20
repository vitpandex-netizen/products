import html

import state
from bot_api import answer_callback, edit_message, send_message

ROLE_LABEL = {state.ROLE_OWNER: "👑 Владелец", state.ROLE_ADMIN: "🛡 Админ", state.ROLE_USER: "Пользователь"}
STATUS_LABEL = {
    state.STATUS_APPROVED: "✅ Одобрен",
    state.STATUS_PENDING: "⏳ Ожидает",
    state.STATUS_DENIED: "🚫 Отклонён",
}

# Per-admin "what are we waiting for" flag while a multi-step flow (like
# adding a user by ID/forward) is in progress. In-memory only: a container
# restart mid-flow just means the admin retries, not worth persisting.
_pending_input: dict[int, str] = {}


def _esc(s) -> str:
    return html.escape(str(s))


def main_menu_kb() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "👥 Пользователи", "callback_data": "menu:users"}],
            [
                {"text": "📊 Статистика", "callback_data": "menu:stats"},
                {"text": "🩺 Статус сервиса", "callback_data": "menu:status"},
            ],
        ]
    }


def _back_kb(target: str = "menu:main") -> dict:
    return {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": target}]]}


def show_main_menu(chat_id: int, thread_id: int, message_id: int | None = None) -> None:
    text = "🛠 <b>Админ-панель transcribe-bot</b>\nВыберите раздел:"
    if message_id:
        edit_message(chat_id, message_id, text, main_menu_kb())
    else:
        send_message(text, chat_id=chat_id, thread_id=thread_id, reply_markup=main_menu_kb())


def _user_row_label(user_id: str, u: dict) -> str:
    name = state.display_name(u, user_id)
    icon = {"approved": "✅", "pending": "⏳", "denied": "🚫"}.get(u["status"], "•")
    return f"{icon} {name}"


def show_users_list(chat_id: int, thread_id: int, message_id: int) -> None:
    users = state.list_users()
    rows = [[{"text": "➕ Добавить пользователя", "callback_data": "menu:adduser"}]]

    if users:
        ordered = sorted(
            users.items(),
            key=lambda kv: ({"pending": 0, "approved": 1, "denied": 2}.get(kv[1]["status"], 9), kv[0]),
        )
        rows += [
            [{"text": _user_row_label(uid, u), "callback_data": f"user:view:{uid}"}] for uid, u in ordered
        ]

    rows.append([{"text": "⬅️ Назад", "callback_data": "menu:main"}])
    pending = sum(1 for u in users.values() if u["status"] == state.STATUS_PENDING)
    header = "👥 <b>Пользователи</b>"
    if not users:
        header += "\nПока никто не обращался к боту."
    elif pending:
        header += f"\n⏳ Ожидают решения: {pending}"
    edit_message(chat_id, message_id, header, {"inline_keyboard": rows})


def _render_user_card(target_id: str, actor_id: int) -> tuple[str, dict]:
    u = state.list_users().get(target_id)
    if not u:
        return "Пользователь не найден.", _back_kb("menu:users")

    name = _esc(state.display_name(u, target_id))
    username = f"@{_esc(u['username'])}" if u.get("username") else "—"
    text = (
        f"<b>{name}</b>\n"
        f"ID: <code>{target_id}</code>\n"
        f"Username: {username}\n"
        f"Роль: {ROLE_LABEL.get(u['role'], u['role'])}\n"
        f"Статус: {STATUS_LABEL.get(u['status'], u['status'])}\n\n"
        f"Доступ по разделам (нажмите, чтобы переключить):"
    )

    rows = []
    if u["role"] == state.ROLE_OWNER:
        rows.append([{"text": "У владельца доступ ко всему", "callback_data": "noop"}])
    else:
        for scope, label in state.SCOPES.items():
            granted = scope in u["scopes"]
            mark = "✅" if granted else "⬜️"
            rows.append([{"text": f"{mark} {label}", "callback_data": f"user:togglescope:{scope}:{target_id}"}])

        if u["status"] == state.STATUS_PENDING:
            rows.append(
                [
                    {"text": "✅ Одобрить всё", "callback_data": f"user:approve:{target_id}"},
                    {"text": "❌ Отклонить", "callback_data": f"user:deny:{target_id}"},
                ]
            )
        elif u["status"] == state.STATUS_APPROVED:
            rows.append([{"text": "🚫 Отозвать весь доступ", "callback_data": f"user:deny:{target_id}"}])
        else:
            rows.append([{"text": "✅ Одобрить всё", "callback_data": f"user:approve:{target_id}"}])

        if state.is_owner(actor_id):
            if u["role"] == state.ROLE_ADMIN:
                rows.append([{"text": "⬇️ Снять права админа", "callback_data": f"user:demote:{target_id}"}])
            else:
                rows.append([{"text": "👑 Сделать админом", "callback_data": f"user:promote:{target_id}"}])

    rows.append([{"text": "⬅️ К списку", "callback_data": "menu:users"}])
    return text, {"inline_keyboard": rows}


def show_user_card(chat_id: int, thread_id: int, message_id: int | None, target_id: str, actor_id: int) -> None:
    text, kb = _render_user_card(target_id, actor_id)
    if message_id:
        edit_message(chat_id, message_id, text, kb)
    else:
        send_message(text, chat_id=chat_id, thread_id=thread_id, reply_markup=kb)


def show_stats(chat_id: int, thread_id: int, message_id: int) -> None:
    s = state.get_stats()
    text = (
        "📊 <b>Статистика</b>\n"
        f"Обработано транскрипций: {s['transcriptions']}\n"
        f"Пользователей всего: {s['total_users']}\n"
        f"Одобрено: {s['approved']}\n"
        f"Ожидают: {s['pending']}"
    )
    edit_message(chat_id, message_id, text, _back_kb())


def show_status(chat_id: int, thread_id: int, message_id: int, transcribe_url: str) -> None:
    import requests

    try:
        r = requests.get(f"{transcribe_url}/health", timeout=10)
        ok = r.ok and r.json().get("status") == "ok"
        text = "🩺 <b>transcribe-service</b>: ✅ работает" if ok else "🩺 <b>transcribe-service</b>: ⚠️ отвечает неожиданно"
    except requests.RequestException as e:
        text = f"🩺 <b>transcribe-service</b>: ❌ недоступен ({_esc(e)})"
    edit_message(chat_id, message_id, text, _back_kb())


def notify_admins_new_request(chat_id: int, admin_thread_id: int, target_id: int, username: str | None, first_name: str | None) -> None:
    name = _esc(first_name or (f"@{username}" if username else f"id{target_id}"))
    text = f"🔔 <b>Новая заявка на доступ</b>\n{name} (<code>{target_id}</code>) просит доступ к транскрибации."
    kb = {
        "inline_keyboard": [
            [
                {"text": "✅ Разрешить", "callback_data": f"user:approve:{target_id}"},
                {"text": "❌ Отклонить", "callback_data": f"user:deny:{target_id}"},
            ]
        ]
    }
    send_message(text, chat_id=chat_id, thread_id=admin_thread_id, reply_markup=kb)


def request_add_user(chat_id: int, thread_id: int, message_id: int, actor_id: int) -> None:
    _pending_input[actor_id] = "add_user"
    edit_message(
        chat_id,
        message_id,
        "➕ <b>Добавление пользователя</b>\n\n"
        "Перешлите сюда любое сообщение от этого человека, или пришлите его "
        "Telegram ID числом.",
        _back_kb("menu:users"),
    )


def is_awaiting_input(admin_id: int) -> bool:
    return _pending_input.get(admin_id) == "add_user"


def cancel_pending(admin_id: int) -> None:
    _pending_input.pop(admin_id, None)


def handle_add_user_input(msg: dict, chat_id: int, thread_id: int, actor_id: int) -> None:
    _pending_input.pop(actor_id, None)

    fwd = msg.get("forward_from")
    if fwd:
        target_id, username, first_name = fwd["id"], fwd.get("username"), fwd.get("first_name")
    else:
        text = (msg.get("text") or "").strip()
        if not text.isdigit():
            send_message(
                "Не похоже на Telegram ID и это не пересланное сообщение. Отменил добавление.",
                chat_id=chat_id,
                thread_id=thread_id,
            )
            return
        target_id, username, first_name = int(text), None, None

    state.register_user(target_id, username, first_name)
    show_user_card(chat_id, thread_id, None, str(target_id), actor_id)


def handle_callback(update: dict, admin_thread_id: int, transcribe_url: str) -> None:
    cq = update["callback_query"]
    actor_id = cq["from"]["id"]
    msg = cq["message"]
    chat_id = msg["chat"]["id"]
    message_id = msg["message_id"]
    data = cq.get("data", "")

    if not state.is_admin(actor_id):
        answer_callback(cq["id"], "Недостаточно прав.", show_alert=True)
        return

    answer_callback(cq["id"])
    cancel_pending(actor_id)

    if data == "noop":
        return
    if data == "menu:main":
        show_main_menu(chat_id, admin_thread_id, message_id)
    elif data == "menu:users":
        show_users_list(chat_id, admin_thread_id, message_id)
    elif data == "menu:adduser":
        request_add_user(chat_id, admin_thread_id, message_id, actor_id)
    elif data == "menu:stats":
        show_stats(chat_id, admin_thread_id, message_id)
    elif data == "menu:status":
        show_status(chat_id, admin_thread_id, message_id, transcribe_url)
    elif data.startswith("user:togglescope:"):
        _, _, scope, target_id = data.split(":", 3)
        state.toggle_scope(int(target_id), scope, decided_by=actor_id)
        show_user_card(chat_id, admin_thread_id, message_id, target_id, actor_id)
    elif data.startswith("user:"):
        _, action, target_id = data.split(":", 2)
        target_int = int(target_id)
        if action == "view":
            show_user_card(chat_id, admin_thread_id, message_id, target_id, actor_id)
        elif action == "approve":
            state.approve(target_int, state.SCOPE_TRANSCRIBE, decided_by=actor_id)
            show_user_card(chat_id, admin_thread_id, message_id, target_id, actor_id)
        elif action == "deny":
            state.deny(target_int, decided_by=actor_id)
            show_user_card(chat_id, admin_thread_id, message_id, target_id, actor_id)
        elif action == "promote" and state.is_owner(actor_id):
            state.set_admin(target_int, True)
            show_user_card(chat_id, admin_thread_id, message_id, target_id, actor_id)
        elif action == "demote" and state.is_owner(actor_id):
            state.set_admin(target_int, False)
            show_user_card(chat_id, admin_thread_id, message_id, target_id, actor_id)
