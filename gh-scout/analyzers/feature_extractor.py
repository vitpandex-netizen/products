"""GH Scout — Feature Extractor & Recommendation Engine.

Извлекает фичи из релиз-ноутов, оценивает релевантность к нашим проектам,
генерирует рекомендации по улучшению.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from core.models import Release, ExtractedFeature, Recommendation, TrackedProject

logger = logging.getLogger(__name__)

# ─── Ключевые слова для категоризации фич ───

FEATURE_PATTERNS = {
    "new_feature": [
        r"(?i)\bnew\b.*\bfeature\b",
        r"(?i)\badd(?:ed|ing)?\b",
        r"(?i)\bintroduc(?:e|ed|ing)\b",
        r"(?i)\blaunch(?:ed|ing)?\b",
        r"(?i)\bsupport(?:s|ed|ing)?\b.*\bfor\b",
        r"(?i)\bimplement(?:ed|ing)?\b",
    ],
    "improvement": [
        r"(?i)\bimprov(?:e|ed|ement)\b",
        r"(?i)\boptimiz(?:e|ed|ation)\b",
        r"(?i)\benhanc(?:e|ed|ement)\b",
        r"(?i)\bupdat(?:e|ed)\b",
        r"(?i)\brefactor(?:ed|ing)?\b",
        r"(?i)\bupgrad(?:e|ed)\b",
    ],
    "fix": [
        r"(?i)\bfix(?:ed|es)?\b",
        r"(?i)\bhotfix\b",
        r"(?i)\bpatch\b",
        r"(?i)\bresolv(?:e|ed)\b",
        r"(?i)\bbug\b",
    ],
    "deprecation": [
        r"(?i)\bdeprecat(?:e|ed|ion)\b",
        r"(?i)\bremov(?:e|ed|ing)\b",
        r"(?i)\bdrop(?:ped)?\b",
    ],
}


# ─── Маппинг фич → наши проекты ───

OUR_PROJECTS_KEYWORDS = {
    "bitget-bot": [
        "trading", "bot", "order", "position", "strategy", "grid", "dca",
        "stop-loss", "take-profit", "trailing", "leverage", "margin",
        "signal", "backtest", "arbitrage", "market-making", "liquidity",
        "portfolio", "risk", "pnl", "profit", "balance", "exchange",
        "binance", "bybit", "okx", "kucoin", "bitget", "hyperliquid",
        "websocket", "realtime", "candle", "indicator", "rsi", "macd",
        "ema", "sma", "bollinger", "freqtrade", "3commas", "octobot",
    ],
    "finanalytics": [
        "analytics", "dashboard", "chart", "metric", "kpi", "report",
        "visualization", "bi", "data", "insight", "forecast", "trend",
        "financial", "stock", "crypto", "portfolio", "performance",
        "valuation", "screener", "filter", "alert", "notification",
    ],
    "anyidea": [
        "idea", "trend", "market", "research", "discovery", "scout",
        "collector", "crawler", "scraper", "rss", "feed", "aggregator",
        "recommendation", "suggestion", "insight", "opportunity",
    ],
    "itops": [
        "monitoring", "alerting", "incident", "deployment", "ci/cd",
        "automation", "orchestration", "infrastructure", "docker",
        "kubernetes", "devops", "sre", "observability", "telemetry",
        "logging", "metrics", "health", "uptime", "sla",
    ],
}


class FeatureExtractor:
    """Извлекает фичи из текста релиза."""

    def extract_features(self, release: Release) -> List[Dict]:
        """Извлечь фичи из релиз-ноута."""
        if not release.body:
            return []

        features = []
        body = release.body

        # Разбиваем на секции/пункты
        sections = self._split_into_sections(body)

        # Фильтруем мусорные секции
        NOISE_KEYWORDS = [
            "what's changed", "what's new", "contributors", "changelog",
            "full changelog", "how to get this update", "how to update",
            "documentation", "feedback and issues", "new contributors",
            "all contributors", "installation", "install", "getting started",
            "license", "upgrade guide", "migration guide", "release notes",
            "release info", "about this release", "acknowledgements",
            "special thanks", "thanks to", "credits",
        ]

        for section in sections:
            section_lower = section.lower()[:200]

            # Пропускаем мусорные заголовки
            if any(nk in section_lower for nk in NOISE_KEYWORDS) and len(section) < 300:
                continue

            # Пропускаем простые упоминания contributor'ов
            if re.search(r"@\w+", section) and len(section) < 80:
                continue

            category = self._categorize(section)
            title = self._extract_title(section)
            if not title:
                continue

            # Пропускаем заглушки
            if title.lower() in ("what's changed", "what's new", "features", "bug fixes", "bugfix",
                                  "new features", "new", "fixes", "improvements", "changelog",
                                  "release", "releases", "version", "initial release"):
                continue

            # Пропускаем заголовки релизов типа "Semantica v0.6.7" или "# Semantica v0.6.7"
            if re.match(r"^[A-Za-z]+[ -][vV]?\d+\.\d+", title):
                continue

            our_projects = self._match_our_projects(section)
            relevance = self._calc_relevance(section, our_projects)

            # Только реальные фичи (с содержанием)
            if len(section.split()) < 5:
                continue

            features.append({
                "title": title[:200],
                "description": section[:500],
                "category": category,
                "relevance": relevance,
                "our_projects_tags": our_projects,
            })

        return features

    def _split_into_sections(self, body: str) -> List[str]:
        """Разбить релиз-ноут на логические секции."""
        lines = body.split("\n")
        sections = []
        current = []

        for line in lines:
            # Новая секция по заголовку markdown
            if line.strip().startswith("##") or line.strip().startswith("###"):
                if current:
                    sections.append("\n".join(current))
                current = [line]
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                current.append(line)
            elif line.strip():
                current.append(line)

        if current:
            sections.append("\n".join(current))

        return sections if sections else [body]

    def _categorize(self, text: str) -> str:
        """Определить категорию фичи."""
        scores = {}
        for cat, patterns in FEATURE_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, text))
            if score > 0:
                scores[cat] = score

        if not scores:
            return "other"

        return max(scores, key=scores.get)

    def _extract_title(self, text: str) -> Optional[str]:
        """Извлечь заголовок фичи."""
        # Заголовок markdown
        header_match = re.search(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)
        if header_match:
            header = header_match.group(1).strip()
            # Пропускаем общие заголовки
            if header.lower() not in ("what's changed", "what's new", "features", "bug fixes", "bugfix", "fixes", "improvements",
                                       "new features", "new", "changelog", "contributors", "new contributors"):
                return header[:100]

        # Первая строка с "- **" или "* **" (жирный пункт)
        bold_match = re.search(r"[-*]\s+\*\*(.+?)\*\*", text)
        if bold_match:
            return bold_match.group(1).strip()[:100]

        # PR-стиль: "- [#1071](url) Fix: preserve..." → "preserve..."
        pr_match = re.search(r"[-*]\s+\[#\d+\]\([^)]*\)\s*(?:Fix|Add|Update|Improve|Support|Change|Remove|Refactor):\s*(.{5,80})", text, re.IGNORECASE)
        if pr_match:
            return pr_match.group(1).strip()[:100]

        # AutoGPT-стиль: "- **#14021** - AI-voice narrative..." → "AI-voice narrative..."
        agpt_match = re.search(r"[-*]\s+\*\*#?\d+\*\*\s*-\s*(.{5,80})", text)
        if agpt_match:
            title = agpt_match.group(1).strip()
            if not title.lower().startswith("fix") and len(title) > 5:
                return title[:100]

        # Первая строка с "- " или "* " — это конкретная фича
        item_match = re.search(r"[-*]\s+([A-Za-z][^.]*[.:])", text)
        if item_match:
            title = item_match.group(1).strip()
            # Убираем PR-ссылку: "- [#1071](url) Fix: ..." → "Fix: ..."
            title = re.sub(r"^\[#\d+\]\([^)]*\)\s*", "", title).strip()
            # Если это похоже на PR-ссылку, берём контекст
            if len(title) > 5 and title.lower() not in ("features", "bug fixes", "fixes", "new"):
                return title[:100]

        # Первая содержательная строка
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 15:
                # Убираем PR-ссылку из строки
                line = re.sub(r"\[#\d+\]\([^)]*\)\s*", "", line).strip()
                return line[:100]

        return None

    def _match_our_projects(self, text: str) -> List[str]:
        """Определить, к каким нашим проектам релевантна фича."""
        matched = []
        text_lower = text.lower()

        for project, keywords in OUR_PROJECTS_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    matched.append(project)
                    break

        return matched

    def _calc_relevance(self, text: str, our_projects: List[str]) -> float:
        """Рассчитать релевантность фичи (0.0-1.0)."""
        score = 0.0

        # Есть совпадение с нашими проектами
        if our_projects:
            score += 0.4

        # Длина текста (содержательность)
        words = len(text.split())
        if words > 20:
            score += 0.1
        if words > 50:
            score += 0.1

        # Ключевые слова высокой важности
        high_importance = [
            "new", "feature", "support", "integration", "api",
            "strategy", "automation", "real-time", "websocket",
            "backtest", "optimization", "performance",
        ]
        for kw in high_importance:
            if re.search(rf"(?i)\b{kw}\b", text):
                score += 0.05
                break

        return min(score, 1.0)


class RecommendationEngine:
    """Генерирует рекомендации на основе извлечённых фич."""

    def __init__(self):
        self.extractor = FeatureExtractor()

    def process_release(self, release: Release, project: TrackedProject):
        """Обработать релиз и создать рекомендации."""
        features = self.extractor.extract_features(release)

        for feat_data in features:
            if not feat_data["our_projects_tags"]:
                continue

            # Создаём ExtractedFeature
            feature = ExtractedFeature(
                release_id=release.id,
                project_id=project.id,
                title=feat_data["title"],
                description=feat_data["description"],
                category=feat_data["category"],
                relevance=feat_data["relevance"],
                our_projects_tags=feat_data["our_projects_tags"],
            )

            from core.database import get_sync_session
            session = get_sync_session()
            try:
                session.add(feature)
                session.flush()  # чтобы получить id

                # Для каждого нашего проекта создаём рекомендацию
                for target in feat_data["our_projects_tags"]:
                    rec = Recommendation(
                        project_id=project.id,
                        feature_id=feature.id,
                        target_project=target,
                        title=f"[{project.name}] {feat_data['title']}",
                        description=self._build_description(
                            feat_data, project, release
                        ),
                        source_repo=project.repo_full_name,
                        source_release=release.tag_name,
                        priority=self._determine_priority(feat_data),
                        effort_estimate=self._estimate_effort(feat_data),
                    )
                    session.add(rec)

                session.commit()
                logger.info(
                    f"Created {len(feat_data['our_projects_tags'])} recommendations "
                    f"from {project.name}/{release.tag_name}"
                )
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to create recommendations: {e}")
            finally:
                session.close()

        # Помечаем релиз как обработанный
        release.is_processed = True

    def _build_description(self, feature: dict, project: TrackedProject, release: Release) -> str:
        """Сформировать описание рекомендации."""
        return (
            f"**Источник**: {project.name} ({project.repo_full_name})\n"
            f"**Релиз**: {release.tag_name}\n"
            f"**Фича**: {feature['title']}\n\n"
            f"{feature['description']}\n\n"
            f"**Релевантность**: {feature['relevance']:.0%}\n"
            f"**Категория**: {feature['category']}\n"
            f"**Ссылка**: {release.html_url}"
        )

    def _determine_priority(self, feature: dict) -> str:
        """Определить приоритет рекомендации."""
        relevance = feature["relevance"]
        category = feature["category"]

        if relevance >= 0.7 and category in ("new_feature", "improvement"):
            return "high"
        elif relevance >= 0.5:
            return "medium"
        else:
            return "low"

    def _estimate_effort(self, feature: dict) -> str:
        """Оценить примерные трудозатраты."""
        category = feature["category"]
        if category == "new_feature":
            return "4-8 hours"
        elif category == "improvement":
            return "2-4 hours"
        elif category == "fix":
            return "1-2 hours"
        else:
            return "2-6 hours"


def process_unprocessed_releases():
    """Обработать все необработанные релизы. Вызывается из cron."""
    from core.database import get_sync_session
    from sqlalchemy.orm import joinedload

    session = get_sync_session()
    engine = RecommendationEngine()

    try:
        releases = (
            session.query(Release)
            .options(joinedload(Release.project))
            .filter(Release.is_processed == False)
            .all()
        )

        logger.info(f"Processing {len(releases)} unprocessed releases")

        for release in releases:
            if release.project:
                engine.process_release(release, release.project)

        session.commit()
        logger.info("Release processing complete")
    except Exception as e:
        session.rollback()
        logger.error(f"Release processing failed: {e}")
        raise
    finally:
        session.close()