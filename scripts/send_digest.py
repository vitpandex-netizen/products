#!/usr/bin/env python3
"""GH Scout — скрипт отправки дайджеста в Telegram.
Запускается из cron: python3 /home/us/dev/gh-scout/scripts/send_digest.py
"""

import json
import urllib.request
from datetime import datetime, timezone

API_BASE = "http://localhost:8005/api/v1"
TG_TOKEN = "8836439317:AAGxNogYtL024gRkhw2YV5wbjPwRYv9ABkY"
TG_CHAT = "-1004297012607"
TG_TOPIC = 203


def api_get(path):
    url = f"{API_BASE}{path}"
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def tg_send(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TG_CHAT,
        "message_thread_id": TG_TOPIC,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "text": text,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def build_digest(recs, releases, trends, projects):
    now = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC+5")
    lines = [
        f"🤖 <b>GH Scout — Ежедневный дайджест</b>",
        f"🗓 {now}\n",
    ]

    proj_map = {p["id"]: p["name"] for p in projects}

    if releases:
        lines.append("📦 <b>Новые релизы аналогов</b>")
        for r in releases[:5]:
            pname = proj_map.get(r.get("project_id", 0), "?")
            tag = r.get("tag_name", "?")
            body = (r.get("body") or "")[:100].replace("\n", " ")
            lines.append(f"• <b>{pname}</b> <code>{tag}</code> — {body}")
        lines.append("")

    if recs:
        lines.append("💡 <b>Рекомендации</b>")
        by_proj = {}
        for r in recs:
            by_proj.setdefault(r.get("target_project", "?"), []).append(r)
        for proj, items in sorted(by_proj.items()):
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(items[0].get("priority", "medium"), "⚪")
            titles = "; ".join((i.get("title") or "")[:50] for i in items[:3])
            lines.append(f"  {emoji} <b>{proj}:</b> {titles}")
            if len(items) > 3:
                lines.append(f"     +{len(items)-3} ещё")
        lines.append("")

    if trends:
        lines.append("🔥 <b>Тренды GitHub</b>")
        for t in trends[:5]:
            lines.append(f"• <b>{t.get('name','?')}</b> ⭐{t.get('stars',0)} — {(t.get('description') or '')[:80]}")
        lines.append("")

    p0 = sum(1 for p in projects if p.get("priority") == "P0")
    lines.append(f"📊 {len(projects)} проектов ({p0} P0) • {len(recs)} рекомендаций")

    return "\n".join(lines)


if __name__ == "__main__":
    recs = api_get("/recommendations?status=new")
    releases = api_get("/releases?limit=5")
    trends = api_get("/trends?limit=5")
    projects = api_get("/projects")
    msg = build_digest(recs, releases, trends, projects)
    result = tg_send(msg)
    if result.get("ok"):
        print(f"✅ Digest sent (msg_id: {result['result']['message_id']})")
    else:
        print(f"❌ Send failed: {result}")