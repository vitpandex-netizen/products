"""Клиент для OpenRouter (DeepSeek) — генерация уточняющих вопросов и анализ"""

import httpx
import json
from typing import Optional


DEFAULT_SYSTEM_PROMPT = """Ты — бот-помощник для поиска лучших предложений на рынке Узбекистана.
Твоя задача — помогать пользователю уточнить запрос, задавая короткие, конкретные вопросы.

Правила:
1. Задавай не более 2-3 вопросов за раз
2. Вопросы на русском языке
3. Уточняй: бюджет, город, состояние (новое/б/у), срочность
4. После того как пользователь ответил на вопросы, напиши только "ГОТОВО_К_ПОИСКУ"
5. Не добавляй лишнего текста после "ГОТОВО_К_ПОИСКУ"
"""


class LLMClient:
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-v4-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.http_client = httpx.Client(timeout=30)
    
    def generate_questions(self, user_query: str, history: list[dict] = None) -> str:
        """Генерирует уточняющие вопросы или сигнал ГОТОВО_К_ПОИСКУ"""
        messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_query})
        
        resp = self.http_client.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 300,
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    
    def analyze_results(
        self, 
        query: str,
        criteria: dict,
        results: list[dict],
    ) -> str:
        """Анализирует результаты поиска и выдаёт рекомендацию"""
        results_text = "\n".join(
            f"{i+1}. {r['title']} — {r['price_label']} — {r['city']}"
            for i, r in enumerate(results[:15])
        )
        
        prompt = f"""Запрос пользователя: {query}
Критерии: {json.dumps(criteria, ensure_ascii=False)}

Результаты поиска:
{results_text}

Проанализируй результаты и дай рекомендацию:
1. Топ-3 лучших предложения с причинами
2. Средняя цена по рынку
3. Совет (стоит ли брать/ждать/торговаться)
Будь конкретным и полезным."""
        
        resp = self.http_client.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 600,
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    
    def close(self):
        self.http_client.close()
