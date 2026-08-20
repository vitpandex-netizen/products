from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db import get_session

router = APIRouter(prefix="/api/v1/prediction-markets", tags=["prediction-markets"])


@router.get("/")
async def get_prediction_markets(
    active: Optional[bool] = Query(True),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """Получить активные prediction markets."""
    conditions = ["pm.active = true"]
    params = {}

    if active is not None:
        if not active:
            conditions = ["pm.active = false"]
    if category:
        conditions.append("pm.category = :category")
        params["category"] = category

    where = " AND ".join(conditions)

    query = text(f"""
        SELECT pm.id, pm.condition_id, pm.question, pm.event_title,
               pm.category, pm.outcome_yes, pm.outcome_no,
               pm.volume, pm.liquidity, pm.open_interest,
               pm.closed, pm.end_date, pm.last_updated
        FROM market_data.prediction_markets pm
        WHERE {where}
        ORDER BY pm.volume DESC NULLS LAST
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await session.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "id": r[0],
            "condition_id": r[1],
            "question": r[2],
            "event_title": r[3],
            "category": r[4],
            "outcome_yes": float(r[5]) * 100 if r[5] else None,
            "outcome_no": float(r[6]) * 100 if r[6] else None,
            "volume": float(r[7]) if r[7] else None,
            "liquidity": float(r[8]) if r[8] else None,
            "open_interest": float(r[9]) if r[9] else None,
            "closed": r[10],
            "end_date": r[11].isoformat() if r[11] else None,
            "last_updated": r[12].isoformat() if r[12] else None,
        }
        for r in rows
    ]


@router.get("/categories")
async def get_categories(
    session: AsyncSession = Depends(get_session),
):
    """Получить список категорий."""
    query = text("""
        SELECT DISTINCT pm.category, COUNT(*) as cnt,
               SUM(pm.volume) as total_volume
        FROM market_data.prediction_markets pm
        WHERE pm.category IS NOT NULL
        GROUP BY pm.category
        ORDER BY total_volume DESC NULLS LAST
    """)
    result = await session.execute(query)
    rows = result.fetchall()
    return [{"category": r[0], "count": r[1], "total_volume": float(r[2]) if r[2] else 0} for r in rows]


@router.get("/history/{market_id}")
async def get_market_history(
    market_id: int,
    limit: int = Query(200, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    """Получить историю цен prediction market."""
    query = text("""
        SELECT ph.outcome_yes, ph.outcome_no, ph.volume, ph.ts
        FROM market_data.prediction_history ph
        WHERE ph.market_id = :market_id
        ORDER BY ph.ts DESC
        LIMIT :limit
    """)
    result = await session.execute(query, {"market_id": market_id, "limit": limit})
    rows = result.fetchall()
    return [
        {
            "outcome_yes": float(r[0]) * 100 if r[0] else None,
            "outcome_no": float(r[1]) * 100 if r[1] else None,
            "volume": float(r[2]) if r[2] else None,
            "ts": r[3].isoformat() if r[3] else None,
        }
        for r in rows
    ]