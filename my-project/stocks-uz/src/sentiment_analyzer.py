"""ИИ-Анализатор сентимента новостных сообщений и Telegram-каналов по рынку UZSE (Sprint 5)."""
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

POSITIVE_KEYWORDS = [
    "дивиденд", "рост", "прибыль", "выкупит", "доход", "выручка",
    "байбэк", "байбек", "одобрил", "рекорд", "положительн", "покупка", "перспектива"
]

NEGATIVE_KEYWORDS = [
    "убыток", "падение", "падении", "снижение", "штраф", "риск", "банкрот",
    "проблем", "отмена", "задержка", "суд", "долг", "сокращени"
]

class SentimentAnalyzer:
    def __init__(self, db=None):
        self.db = db

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Анализ эмоционального тона текста (сентимента)."""
        if not text:
            return {"sentiment_score": 0.0, "label": "neutral", "positive_words": [], "negative_words": []}

        lower_text = text.lower()
        pos_found = [kw for kw in POSITIVE_KEYWORDS if re.search(r'\b' + re.escape(kw), lower_text)]
        neg_found = [kw for kw in NEGATIVE_KEYWORDS if re.search(r'\b' + re.escape(kw), lower_text)]

        pos_count = len(pos_found)
        neg_count = len(neg_found)

        total = pos_count + neg_count
        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = (pos_count - neg_count) / float(total)
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"

        return {
            "sentiment_score": round(score, 2),
            "label": label,
            "positive_words": pos_found,
            "negative_words": neg_found
        }

    def analyze_ticker_sentiment(self, ticker: str, messages_override: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Расчет агрегированного индекса сентимента для конкретного тикера по сообщениям из каналов."""
        messages = messages_override
        if messages is None and self.db:
            all_msgs = self.db.get_recent_channel_messages(limit=50)
            messages = [m for m in all_msgs if ticker.lower() in (m.get("message_text") or "").lower()]

        if not messages:
            return {
                "ticker": ticker,
                "sentiment_index": 0.0,
                "label": "neutral",
                "message_count": 0,
                "breakdown": {"positive": 0, "neutral": 0, "negative": 0}
            }

        scores = []
        breakdown = {"positive": 0, "neutral": 0, "negative": 0}

        for msg in messages:
            res = self.analyze_text(msg.get("message_text", "") or msg.get("text", ""))
            scores.append(res["sentiment_score"])
            breakdown[res["label"]] += 1

        avg_score = sum(scores) / max(len(scores), 1)
        if avg_score > 0.15:
            overall_label = "bullish"
        elif avg_score < -0.15:
            overall_label = "bearish"
        else:
            overall_label = "neutral"

        return {
            "ticker": ticker,
            "sentiment_index": round(avg_score, 2),
            "label": overall_label,
            "message_count": len(messages),
            "breakdown": breakdown
        }
