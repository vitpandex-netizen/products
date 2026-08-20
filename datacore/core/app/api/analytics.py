from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary")
async def get_summary(
    session: AsyncSession = Depends(get_session),
):
    """Сводка по всем проектам."""
    # Количество сигналов за последние 24ч
    signals_count = await session.execute(text("""
        SELECT COUNT(*) FROM analytics.signals
        WHERE ts > NOW() - INTERVAL '24 hours'
    """))
    signals_24h = signals_count.scalar()

    # Количество сделок за последние 24ч
    trades_count = await session.execute(text("""
        SELECT COUNT(*) FROM analytics.trades
        WHERE ts > NOW() - INTERVAL '24 hours'
    """))
    trades_24h = trades_count.scalar()

    # PnL за последние 24ч по ботам
    pnl = await session.execute(text("""
        SELECT bot_name, COUNT(*) as trades, SUM(pnl) as total_pnl
        FROM analytics.trades
        WHERE ts > NOW() - INTERVAL '24 hours' AND pnl IS NOT NULL
        GROUP BY bot_name
        ORDER BY total_pnl DESC
    """))
    pnl_by_bot = [{"bot": r[0], "trades": r[1], "pnl": float(r[2]) if r[2] else 0} for r in pnl.fetchall()]

    # Активные prediction markets
    pm_count = await session.execute(text("""
        SELECT COUNT(*) FROM market_data.prediction_markets WHERE active = true AND closed = false
    """))
    active_pm = pm_count.scalar()

    # Статус сборщиков
    collectors = await session.execute(text("""
        SELECT DISTINCT ON (collector) collector, status, ts
        FROM core.collector_logs
        ORDER BY collector, ts DESC
    """))
    collector_status = [{"name": r[0], "status": r[1], "last_run": r[2].isoformat() if r[2] else None} for r in collectors.fetchall()]

    return {
        "signals_24h": signals_24h,
        "trades_24h": trades_24h,
        "pnl_by_bot": pnl_by_bot,
        "active_prediction_markets": active_pm,
        "collector_status": collector_status,
        "generated_at": "now",
    }


@router.get("/dashboard")
async def get_dashboard(
    session: AsyncSession = Depends(get_session),
):
    """Дашборд — последние данные для визуализации."""
    # Последние цены ключевых активов
    latest = await session.execute(text("""
        SELECT DISTINCT ON (s.symbol) s.symbol, p.price, p.ts
        FROM market_data.prices p
        JOIN core.symbols s ON s.id = p.symbol_id
        WHERE p.ts > NOW() - INTERVAL '1 hour'
        ORDER BY s.symbol, p.ts DESC
    """))
    prices = [{"symbol": r[0], "price": float(r[1]) if r[1] else None, "ts": r[2].isoformat() if r[2] else None} for r in latest.fetchall()]

    # Последние 10 сигналов
    signals = await session.execute(text("""
        SELECT signal_type, symbol, direction, strength, reason, ts
        FROM analytics.signals
        ORDER BY ts DESC
        LIMIT 10
    """))
    recent_signals = [
        {
            "type": r[0], "symbol": r[1], "direction": r[2],
            "strength": float(r[3]) if r[3] else None,
            "reason": r[4], "ts": r[5].isoformat() if r[5] else None,
        }
        for r in signals.fetchall()
    ]

    return {
        "prices": prices,
        "recent_signals": recent_signals,
    }