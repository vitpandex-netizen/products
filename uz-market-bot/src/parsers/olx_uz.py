"""OLX UZ парсер — поиск товаров по открытому API"""

import httpx
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class OLXOffer:
    title: str
    price_label: str
    price_value: float  
    currency: str
    url: str
    photo_url: Optional[str]
    city: str
    district: Optional[str]
    state: Optional[str]  # Б/у, Новое
    seller_name: str
    is_negotiable: bool
    created_time: str
    description: str
    source: str = "olx"


@dataclass
class OLXSearchResult:
    offers: list[OLXOffer]
    total: int
    promoted_count: int


class OLXParser:
    """Парсер OLX.uz через открытое API"""
    
    BASE_URL = "https://www.olx.uz/api/v1/offers"
    
    CATEGORY_MAP = {
        "electronics": 85,
        "phones": 85,
        "computers": 95,
        "vehicles": 200,
        "furniture": 150,
        "clothing": 145,
        "real_estate": 100,
    }
    
    def __init__(self, timeout: int = 15):
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
            }
        )
    
    def search(
        self, 
        query: str, 
        page: int = 1, 
        limit: int = 20,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        city: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> OLXSearchResult:
        params = {
            "query": query,
            "page": page,
            "limit": min(limit, 40),
        }
        
        if min_price:
            params["price_from"] = min_price
        if max_price:
            params["price_to"] = max_price
        if city:
            params["city"] = city
        if category_id:
            params["category_id"] = category_id
        
        resp = self.client.get(self.BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        offers = []
        for item in data.get("data", []):
            price_info = self._extract_price(item)
            offer = self._parse_offer(item, price_info)
            offers.append(offer)
        
        metadata = data.get("metadata", {})
        total = metadata.get("total_elements", len(offers))
        promoted = len(metadata.get("promoted", []))
        
        return OLXSearchResult(
            offers=offers,
            total=total,
            promoted_count=promoted,
        )
    
    def _extract_price(self, item: dict) -> dict:
        for param in item.get("params", []):
            if param.get("key") == "price":
                val = param.get("value", {})
                return {
                    "value": val.get("converted_value") or val.get("value", 0),
                    "label": val.get("label", "Цена не указана"),
                    "currency": val.get("converted_currency") or val.get("currency", "UZS"),
                    "negotiable": val.get("negotiable", False),
                }
        return {"value": 0, "label": "Цена не указана", "currency": "UZS", "negotiable": False}
    
    def _extract_state(self, item: dict) -> Optional[str]:
        for param in item.get("params", []):
            if param.get("key") == "state":
                val = param.get("value", {})
                if isinstance(val, dict):
                    return val.get("label")
        return None
    
    def _parse_offer(self, item: dict, price_info: dict) -> OLXOffer:
        location = item.get("location", {})
        city = (location.get("city") or {}).get("name", "Не указан")
        district = (location.get("district") or {}).get("name")
        
        photos = item.get("photos", [])
        photo_url = None
        if photos:
            template = photos[0].get("link", "")
            photo_url = template.replace("{width}", "400").replace("{height}", "400")
        
        # Нормализуем цену
        price_val = price_info.get("value", 0)
        if isinstance(price_val, str):
            try:
                price_val = float(price_val)
            except (ValueError, TypeError):
                price_val = 0.0
        
        return OLXOffer(
            title=item.get("title", ""),
            price_label=price_info.get("label", ""),
            price_value=float(price_val) if price_val else 0.0,
            currency=price_info.get("currency", "UZS"),
            url=item.get("url", ""),
            photo_url=photo_url,
            city=city,
            district=district,
            state=self._extract_state(item),
            seller_name=item.get("user", {}).get("name", "Продавец"),
            is_negotiable=price_info.get("negotiable", False),
            created_time=item.get("created_time", ""),
            description=item.get("description", "")[:300],
        )
    
    def close(self):
        self.client.close()
