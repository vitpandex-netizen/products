from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db import get_session

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])


@router.get("/")
async def get_prices(
    source: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    """Получить последние цены."""
    conditions = []
    params = {}

    if source:
        conditions.append("p.source = :source")
        params["source"] = source
    if symbol:
        conditions.append("s.symbol = :symbol")
        params["symbol"] = symbol

    where = " AND ".join(conditions) if conditions else "TRUE"

    query = text(f"""
        SELECT p.id, s.symbol, p.source, p.price, p.bid, p.ask, p.volume, p.ts
        FROM market_data.prices p
        JOIN core.symbols s ON s.id = p.symbol_id
        WHERE {where}
        ORDER BY p.ts DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await session.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "id": r[0],
            "symbol": r[1],
            "source": r[2],
            "price": float(r[3]) if r[3] else None,
            "bid": float(r[4]) if r[4] else None,
            "ask": float(r[5]) if r[5] else None,
            "volume": float(r[6]) if r[6] else None,
            "ts": r[7].isoformat() if r[7] else None,
        }
        for r in rows
    ]


@router.get("/history")
async def get_price_history(
    symbol: str = Query(...),
    source: str = Query("yahoo"),
    interval: str = Query("1d"),
    limit: int = Query(500, ge=1, le=10000),
    session: AsyncSession = Depends(get_session),
):
    """Получить историю цен по символу."""
    # Bucket-based aggregation
    bucket = {
        "1h": "date_trunc('hour', p.ts)",
        "1d": "p.ts::date",
        "1w": "date_trunc('week', p.ts)",
    }.get(interval, "p.ts::date")

    query = text(f"""
        SELECT {bucket} as bucket,
               first(p.price, p.ts) as open,
               MAX(p.price) as high,
               MIN(p.price) as low,
               last(p.price, p.ts) as close,
               SUM(p.volume) as volume
        FROM market_data.prices p
        JOIN core.symbols s ON s.id = p.symbol_id
        WHERE s.symbol = :symbol AND p.source = :source
        GROUP BY bucket
        ORDER BY bucket DESC
        LIMIT :limit
    """)

    result = await session.execute(query, {"symbol": symbol, "source": source, "limit": limit})
    rows = result.fetchall()

    return [
        {
            "ts": r[0].isoformat() if r[0] else None,
            "open": float(r[1]) if r[1] else None,
            "high": float(r[2]) if r[2] else None,
            "low": float(r[3]) if r[3] else None,
            "close": float(r[4]) if r[4] else None,
            "volume": float(r[5]) if r[5] else None,
        }
        for r in rows
    ]