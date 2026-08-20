#!/usr/bin/env python3
"""Улучшенный матчер для IT Director позиций — работает по заголовкам RSS"""
import sys, os, re
from pathlib import Path

# IT Director ключевые слова (высокий приоритет)
DIRECTOR_KEYWORDS = [
    'IT директор', 'технический директор', 'CTO', 'CIO', 'Head of IT',
    'Head of Infrastructure', 'IT Director', 'Director of Engineering',
    'VP of Engineering', 'руководитель IT', 'начальник IT',
    'IT Operations Manager', 'Infrastructure Manager',
    'руководитель эксплуатации', 'главный инженер',
    'Head of Corporate Technologies', 'IT менеджер',
    'Information Systems', 'главный инженер', 'заместитель начальника IT',
    'DevOps Engineer', 'DevOps', 'Senior DevOps',
    'Senior Linux', 'системный администратор',
    'администратор баз данных', 'Database Administrator',
    'Network Engineer', 'инженер сети',
]

def score_title(title: str) -> float:
    """Оценка вакансии по заголовку (без описания)"""
    title_lower = title.lower()
    score = 0.0
    
    # Прямые совпадения с IT Director ключевыми словами
    for kw in DIRECTOR_KEYWORDS:
        if kw.lower() in title_lower:
            # Чем длиннее ключевое слово, тем выше вес
            weight = len(kw) / 30.0  # 0.3-1.0 в зависимости от длины
            score = max(score, min(weight, 0.9))
    
    # Бонус за руководящие слова
    if any(w in title_lower for w in ['head', 'chief', 'director', 'manager', 'lead', 'руководитель', 'начальник', 'главный', 'заместитель']):
        score += 0.15
    
    # Бонус за IT-специфику
    if any(w in title_lower for w in ['it', 'информацион', 'техническ', 'digital', 'technology', 'infrastructure', 'devops', 'devops', 'system', 'network', 'security', 'database', 'cloud', 'platform']):
        score += 0.1
    
    # Штраф за нерелевантные
    if any(w in title_lower for w in ['водитель', 'уборщик', 'продавец', 'кассир', 'охранник', 'повар', 'barista', 'junior']):
        score *= 0.3
    
    return min(score, 1.0)

# Test
if __name__ == '__main__':
    tests = [
        'Head of Corporate Technologies Information Systems',
        'Главный инженер/ руководитель службы эксплуатации',
        'DevOps Engineer (Tez/Узбекистан)',
        'Software Engineer (Python / Django)',
        'Заместитель начальника IT-поддержки',
        'Database Administrator (PostgreSQL)',
        'Системный администратор Linux',
        'Водитель',
        'Специалист по слаботочным системам (видеонаблюдение)',
    ]
    for t in tests:
        s = score_title(t)
        print(f'{s:.2f}  {t[:50]}')