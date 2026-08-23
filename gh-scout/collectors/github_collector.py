"""GH Scout — GitHub Collector.

Сбор данных с GitHub API: релизы, метрики, информация о проектах.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from github import Github, GithubException, RateLimitExceededException
from github.GithubException import UnknownObjectException

from core.config import settings
from core.models import TrackedProject, Release, Trend, Priority

logger = logging.getLogger(__name__)


class GitHubCollector:
    """Сборщик данных с GitHub."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token or os.getenv("GITHUB_TOKEN")
        if self.token:
            self.github = Github(self.token, per_page=100)
            logger.info("GitHub authenticated with token")
        else:
            self.github = Github(per_page=30)
            logger.warning("GitHub — без токена (лимит 60 req/h)")

    # ─── Релизы ───

    def fetch_releases(self, repo_full_name: str, since: Optional[datetime] = None) -> List[Dict]:
        """Получить новые релизы репозитория."""
        try:
            repo = self.github.get_repo(repo_full_name)
            releases = repo.get_releases()
            results = []
            for rel in releases:
                rel_dt = rel.published_at.replace(tzinfo=None) if rel.published_at else None
                if since and rel_dt and rel_dt <= since:
                    continue
                results.append({
                    "tag_name": rel.tag_name,
                    "release_name": rel.title or "",
                    "body": rel.body or "",
                    "html_url": rel.html_url,
                    "published_at": rel_dt,
                    "prerelease": rel.prerelease,
                })
            logger.info(f"Fetched {len(results)} releases for {repo_full_name}")
            return results
        except UnknownObjectException:
            logger.warning(f"Repository not found: {repo_full_name}")
            return []
        except RateLimitExceededException:
            logger.error("GitHub API rate limit exceeded")
            return []
        except Exception as e:
            logger.error(f"Error fetching releases for {repo_full_name}: {e}")
            return []

    def fetch_repo_info(self, repo_full_name: str) -> Optional[Dict]:
        """Получить базовую информацию о репозитории."""
        try:
            repo = self.github.get_repo(repo_full_name)
            return {
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "language": repo.language or "",
                "description": repo.description or "",
            }
        except Exception as e:
            logger.error(f"Error fetching repo info for {repo_full_name}: {e}")
            return None

    # ─── Тренды ───

    def fetch_trending(self, language: str = "", since: str = "daily") -> List[Dict]:
        """Получить трендовые репозитории с GitHub Trending.

        Использует неофициальный API (githunt). Если не работает, парсим HTML.
        """
        import httpx
        url = "https://api.gitterapp.com/repositories"
        params = {"since": since}
        if language:
            params["language"] = language

        try:
            resp = httpx.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                items = resp.json()
                logger.info(f"Fetched {len(items)} trending repos ({since}/{language})")
                return items
            else:
                logger.warning(f"Trending API returned {resp.status_code}")
                return self._fetch_trending_fallback(since, language)
        except Exception as e:
            logger.warning(f"Trending API error: {e}, using fallback")
            return self._fetch_trending_fallback(since, language)

    def _fetch_trending_fallback(self, since: str = "daily", language: str = "") -> List[Dict]:
        """Fallback: парсинг GitHub Trending HTML."""
        import httpx
        from bs4 import BeautifulSoup

        url = "https://github.com/trending"
        if language:
            url += f"/{language}"
        url += f"?since={since}"

        try:
            resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.select("article.Box-row")
            results = []

            for article in articles[:25]:
                h2 = article.select_one("h2 a")
                if not h2:
                    continue
                full_name = h2.get("href", "").strip("/")
                desc_el = article.select_one("p")
                stars_el = article.select_one(".d-inline-block.float-sm-right")
                today_el = article.select_one(".float-sm-right .d-inline-block")

                # Парсинг звёзд: из "14397 stars this week" берём только число
                stars_text = stars_el.text.strip() if stars_el else ""
                stars_num = 0
                if stars_text:
                    import re
                    nums = re.findall(r'\d+', stars_text.replace(",", ""))
                    if nums:
                        stars_num = int(nums[0])

                # Парсинг звёзд за сегодня: из "1,234 stars today" берём число
                today_text = today_el.text.strip() if today_el else ""
                today_num = 0
                if today_text:
                    import re
                    nums = re.findall(r'\d+', today_text.replace(",", ""))
                    if nums:
                        today_num = int(nums[0])

                results.append({
                    "repo_full_name": full_name,
                    "description": desc_el.text.strip() if desc_el else "",
                    "stars": stars_num,
                    "stars_today": today_num,
                    "language": language or "",
                })

            return results
        except Exception as e:
            logger.error(f"Trending fallback failed: {e}")
            return []

    def fetch_trending_repos(self, categories: List[str] = None) -> List[Dict]:
        """Собрать тренды по нескольким категориям."""
        if categories is None:
            categories = ["python", "javascript", "typescript", "rust", "go"]

        all_trends = []
        for lang in categories:
            repos = self.fetch_trending(language=lang, since="daily")
            for r in repos:
                all_trends.append({
                    "repo_full_name": r.get("repo_full_name", ""),
                    "repo_url": f"https://github.com/{r.get('repo_full_name', '')}",
                    "name": r.get("repo_full_name", "").split("/")[-1] if "/" in r.get("repo_full_name", "") else r.get("repo_full_name", ""),
                    "description": r.get("description", ""),
                    "language": lang,
                    "stars": r.get("stars", 0),
                    "stars_today": r.get("stars_today", 0),
                    "forks": r.get("forks", 0),
                    "trend_date": datetime.utcnow(),
                    "trend_source": "github_trending",
                })

        # Также топ-100 по звёздам за неделю
        weekly = self.fetch_trending(since="weekly")
        for r in weekly:
            all_trends.append({
                "repo_full_name": r.get("repo_full_name", ""),
                "repo_url": f"https://github.com/{r.get('repo_full_name', '')}",
                "name": r.get("repo_full_name", "").split("/")[-1] if "/" in r.get("repo_full_name", "") else r.get("repo_full_name", ""),
                "description": r.get("description", ""),
                "language": "mixed",
                "stars": r.get("stars", 0),
                "stars_today": r.get("stars_today", 0),
                "forks": r.get("forks", 0),
                "trend_date": datetime.utcnow(),
                "trend_source": "github_trending_weekly",
            })

        return all_trends


# ─── Синхронный сборщик для cron ───

def collect_all_projects(token: str = None):
    """Собрать релизы всех активных P0 проектов. Вызывается из cron."""
    from core.database import get_sync_session
    from sqlalchemy.orm import Session

    session = get_sync_session()
    collector = GitHubCollector(token=token)

    try:
        projects = session.query(TrackedProject).filter(
            TrackedProject.status == "active",
            TrackedProject.priority.in_([Priority.P0, Priority.P1])
        ).all()

        logger.info(f"Collecting releases for {len(projects)} projects")

        for project in projects:
            releases = collector.fetch_releases(
                project.repo_full_name,
                since=project.last_release_check
            )

            for rel_data in releases:
                # Проверка дубликата
                existing = session.query(Release).filter(
                    Release.project_id == project.id,
                    Release.tag_name == rel_data["tag_name"]
                ).first()
                if existing:
                    continue

                release = Release(
                    project_id=project.id,
                    tag_name=rel_data["tag_name"],
                    release_name=rel_data["release_name"],
                    body=rel_data["body"],
                    html_url=rel_data["html_url"],
                    published_at=rel_data["published_at"],
                    prerelease=rel_data["prerelease"],
                )
                session.add(release)

            # Обновляем метрики
            info = collector.fetch_repo_info(project.repo_full_name)
            if info:
                project.stars = info["stars"]
                project.forks = info["forks"]
                project.open_issues = info["open_issues"]
                project.language = info["language"]
                if info["description"]:
                    project.description = info["description"]

            project.last_release_check = datetime.utcnow()

        session.commit()
        logger.info("Release collection complete")
    except Exception as e:
        session.rollback()
        logger.error(f"Collection failed: {e}")
        raise
    finally:
        session.close()


def collect_trends(token: str = None):
    """Собрать трендовые репозитории. Вызывается из cron."""
    from core.database import get_sync_session
    collector = GitHubCollector(token=token)
    session = get_sync_session()

    try:
        categories = ["python", "javascript", "typescript", "rust"]
        trends = collector.fetch_trending_repos(categories)
        trend_date = datetime.utcnow().date()

        added = 0
        for t in trends:
            # Проверка дубликата по дате
            existing = session.query(Trend).filter(
                Trend.repo_full_name == t["repo_full_name"],
                Trend.trend_date >= trend_date
            ).first()
            if existing:
                continue

            trend = Trend(**t)
            session.add(trend)
            added += 1

        session.commit()
        logger.info(f"Trend collection complete: {added} new trends")
    except Exception as e:
        session.rollback()
        logger.error(f"Trend collection failed: {e}")
        raise
    finally:
        session.close()