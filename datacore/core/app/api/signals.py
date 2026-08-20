from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.db import get_session

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.get("/")
async def get_signals(
    signal_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    since: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Получить сигналы."""
    conditions = []
    params = {}

    if signal_type:
        conditions.append("s.signal_type = :signal_type")
        params["signal_type"] = signal_type
    if source:
        conditions.append("s.source = :source")
        params["source"] = source
    if since:
        conditions.append("s.ts >= :since")
        params["since"] = since

    where = " AND ".join(conditions) if conditions else "TRUE"

    query = text(f"""
        SELECT s.id, s.source, s.signal_type, s.symbol,
               s.direction, s.strength, s.price_at_signal,
               s.target_price, s.reason, s.ts
        FROM analytics.signals s
        WHERE {where}
        ORDER BY s.ts DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await session.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "id": r[0],
            "source": r[1],
            "signal_type": r[2],
            "symbol": r[3],
            "direction": r[4],
            "strength": float(r[5]) if r[5] else None,
            "price_at_signal": float(r[6]) if r[6] else None,
            "target_price": float(r[7]) if r[7] else None,
            "reason": r[8],
            "ts": r[9].isoformat() if r[9] else None,
        }
        for r in rows
    ]


@router.post("/")
async def create_signal(
    source: str,
    signal_type: str,
    symbol: Optional[str] = None,
    direction: Optional[str] = None,
    strength: Optional[float] = None,
    price_at_signal: Optional[float] = None,
    target_price: Optional[float] = None,
    reason: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Создать сигнал."""
    query = text("""
        INSERT INTO analytics.signals
            (source, signal_type, symbol, direction, strength,
             price_at_signal, target_price, reason, ts)
        VALUES
            (:source, :signal_type, :symbol, :direction, :strength,
             :price_at_signal, :target_price, :reason, NOW())
        RETURNING id
    """)
    result = await session.execute(query, {
        "source": source,
        "signal_type": signal_type,
        "symbol": symbol,
        "direction": direction,
        "strength": strength,
        "price_at_signal": price_at_signal,
        "target_price": target_price,
        "reason": reason,
    })
    signal_id = result.scalar()
    return {"id": signal_id, "status": "created"}