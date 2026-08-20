"""GH Scout — Telegram интеграция."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from core.config import settings
from core.models import Recommendation, Trend, Release, TrackedProject

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Отправка уведомлений в Telegram."""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self._enabled = bool(self.bot_token and self.chat_id)

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Отправить сообщение в Telegram."""
        if not self._enabled:
            logger.warning("Telegram not configured, skipping message")
            return False

        import httpx
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            resp = httpx.post(url, json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def send_digest(
        self,
        new_releases: List[dict],
        recommendations: List[dict],
        trends: List[dict],
    ) -> bool:
        """Отправить ежедневный дайджест."""
        lines = [
            "🤖 <b>GH Scout — Ежедневный дайджест</b>\n",
        ]

        # Релизы
        if new_releases:
            lines.append("📦 <b>Новые релизы:</b>")
            for r in new_releases[:5]:
                project = r.get("project_name", "")
                tag = r.get("tag_name", "")
                url = r.get("html_url", "")
                lines.append(f"  • <a href='{url}'>{project} {tag}</a>")
            if len(new_releases) > 5:
                lines.append(f"  ... и ещё {len(new_releases) - 5}")
            lines.append("")

        # Рекомендации
        if recommendations:
            lines.append("💡 <b>Рекомендации по улучшению:</b>")
            for rec in recommendations[:5]:
                title = rec.get("title", "")
                target = rec.get("target_project", "")
                priority = rec.get("priority", "medium")
                emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                lines.append(f"  {emoji} [{target}] {title}")
            if len(recommendations) > 5:
                lines.append(f"  ... и ещё {len(recommendations) - 5}")
            lines.append("")

        # Тренды
        if trends:
            lines.append("🔥 <b>Тренды GitHub:</b>")
            for t in trends[:5]:
                name = t.get("name", "")
                stars = t.get("stars", 0)
                desc = t.get("description", "")[:80]
                lines.append(f"  • <b>{name}</b> ⭐{stars} — {desc}")
            if len(trends) > 5:
                lines.append(f"  ... и ещё {len(trends) - 5}")

        return self.send_message("\n".join(lines))

    def send_recommendation(self, rec: Recommendation, project: TrackedProject) -> bool:
        """Отправить одну рекомендацию."""
        emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.priority, "⚪")
        text = (
            f"{emoji} <b>Новая рекомендация</b>\n\n"
            f"<b>Проект:</b> {rec.target_project}\n"
            f"<b>Что:</b> {rec.title}\n\n"
            f"<b>Источник:</b> {project.name}\n"
            f"<b>Релиз:</b> {rec.source_release}\n"
            f"<b>Оценка:</b> {rec.effort_estimate}\n"
            f"<b>Приоритет:</b> {rec.priority.upper()}\n\n"
            f"<a href='{project.repo_url}'>Открыть проект</a>"
        )
        return self.send_message(text)

    def send_trend_alert(self, trend: Trend) -> bool:
        """Отправить уведомление о новом тренде."""
        text = (
            f"🔥 <b>Новый тренд!</b>\n\n"
            f"<b>{trend.name}</b>\n"
            f"⭐ {trend.stars} звёзд\n"
            f"{trend.description[:200]}\n\n"
            f"<a href='{trend.repo_url}'>Открыть</a>"
        )
        return self.send_message(text)


# ─── Cron-функции ───

def send_daily_digest():
    """Отправить ежедневный дайджест. Вызывается из cron."""
    from core.database import get_sync_session
    from sqlalchemy import select

    session = get_sync_session()
    notifier = TelegramNotifier()
    since = datetime.utcnow() - timedelta(hours=24)

    try:
        # Собираем данные
        releases = (
            session.query(Release)
            .join(TrackedProject)
            .filter(Release.published_at >= since)
            .order_by(Release.published_at.desc())
            .limit(10)
            .all()
        )

        recommendations = (
            session.query(Recommendation)
            .filter(
                Recommendation.status == "new",
                Recommendation.created_at >= since,
            )
            .order_by(Recommendation.priority.desc())
            .limit(10)
            .all()
        )

        trends = (
            session.query(Trend)
            .filter(Trend.trend_date >= since)
            .order_by(Trend.relevance_score.desc())
            .limit(10)
            .all()
        )

        # Форматируем
        release_data = [
            {
                "project_name": r.project.name if r.project else "",
                "tag_name": r.tag_name,
                "html_url": r.html_url,
            }
            for r in releases
        ]

        rec_data = [
            {
                "title": r.title,
                "target_project": r.target_project,
                "priority": r.priority,
            }
            for r in recommendations
        ]

        trend_data = [
            {
                "name": t.name,
                "stars": t.stars,
                "description": t.description,
            }
            for t in trends
        ]

        if not any([release_data, rec_data, trend_data]):
            logger.info("No new data for daily digest")
            return

        notifier.send_digest(release_data, rec_data, trend_data)
        logger.info("Daily digest sent")

    except Exception as e:
        logger.error(f"Digest failed: {e}")
        raise
    finally:
        session.close()