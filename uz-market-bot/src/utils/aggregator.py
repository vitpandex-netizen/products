"""Агрегатор — объединяет результаты с разных площадок, сортирует, фильтрует"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchCriteria:
    query: str
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    city: Optional[str] = None
    condition: Optional[str] = None  # new, used, any
    category: Optional[str] = None
    sort_by: str = "price_asc"  # price_asc, price_desc, newest


@dataclass
class UnifiedOffer:
    title: str
    price_label: str
    price_value: float
    currency: str
    url: str
    photo_url: Optional[str]
    city: str
    source: str
    condition: Optional[str]
    seller: str
    created: str
    score: float = 0.0  # computed score for ranking


class Aggregator:
    """Объединяет и ранжирует предложения с разных площадок"""
    
    def __init__(self):
        self.parsers = []
    
    def register_parser(self, name: str, search_fn):
        """Регистрирует парсер: search_fn(query, criteria) -> list[UnifiedOffer]"""
        self.parsers.append((name, search_fn))
    
    def merge_and_rank(
        self, 
        all_offers: list[UnifiedOffer],
        criteria: SearchCriteria,
    ) -> list[UnifiedOffer]:
        """Сортирует и ранжирует предложения"""
        
        # Фильтр по цене
        filtered = []
        for o in all_offers:
            if criteria.max_price and o.price_value > criteria.max_price:
                continue
            if criteria.min_price and o.price_value < criteria.min_price:
                continue
            filtered.append(o)
        
        # Вычисляем score
        for o in filtered:
            score = 0.0
            # Чем ниже цена — тем выше score (для price_asc)
            if criteria.sort_by == "price_asc" and o.price_value > 0:
                score = 1000 / o.price_value
            # Бонус за фото
            if o.photo_url:
                score += 0.5
            # Бонус за указанный город
            if o.city and o.city != "Не указан":
                score += 0.3
            o.score = round(score, 4)
        
        # Сортировка
        if criteria.sort_by == "price_asc":
            filtered.sort(key=lambda x: (x.price_value if x.price_value > 0 else float('inf'), -x.score))
        elif criteria.sort_by == "price_desc":
            filtered.sort(key=lambda x: x.price_value, reverse=True)
        elif criteria.sort_by == "newest":
            filtered.sort(key=lambda x: x.created, reverse=True)
        
        return filtered
    
    def format_offer_text(self, offer: UnifiedOffer) -> str:
        """Форматирует одно предложение для вывода в Telegram"""
        lines = [
            f"🔹 {offer.title}",
            f"💰 {offer.price_label}",
            f"📍 {offer.city}",
        ]
        if offer.condition:
            lines.append(f"📦 {offer.condition}")
        lines.append(f"🔗 {offer.url}")
        if offer.photo_url:
            lines.append(f"🖼 {offer.photo_url}")
        return "\n".join(lines)
    
    def format_summary(self, offers: list[UnifiedOffer], total_found: int, analysis: str = None) -> str:
        """Форматирует итоговый ответ"""
        if not offers:
            return "😕 Ничего не найдено по вашему запросу. Попробуйте изменить критерии."
        
        text = f"📊 *Найдено {total_found} предложений*\n"
        text += f"Показано топ-{min(len(offers), 10)}:\n\n"
        
        for i, offer in enumerate(offers[:10], 1):
            text += f"{i}. *{offer.title}*\n"
            text += f"   💰 {offer.price_label}  |  📍 {offer.city}  |  🏪 {offer.source}\n"
            if offer.condition:
                text += f"   📦 {offer.condition}\n"
            text += f"   🔗 {offer.url}\n\n"
        
        if analysis:
            text += f"━━━━━━━━━━━━━━━━\n*🧠 Анализ:*\n{analysis}\n"
        
        return text
