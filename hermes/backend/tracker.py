"""
BGT Bot — Трекер сделок и мониторинг портфеля.
Добавляет: лимитные заявки, стоп-лоссы, тейк-профиты, P&L трекинг.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, Session

from models import engine, Base, SessionLocal, now

TASHKENT = timezone(timedelta(hours=5))


class Trade(Base):
    """Сделка / лимитная заявка"""
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    direction = Column(String, nullable=False)  # buy, sell
    status = Column(String, default="pending")  # pending, open, closed, cancelled
    order_type = Column(String, default="limit")  # limit, market
    limit_price = Column(Float, nullable=True)
    shares = Column(Float, nullable=False)
    filled_price = Column(Float, nullable=True)
    filled_at = Column(String, nullable=True)
    commission = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    rationale = Column(Text, nullable=True)
    created_at = Column(String, default=now)
    updated_at = Column(String, default=now)


class PortfolioWatch(Base):
    """Наблюдаемые позиции с автоматическими алертами"""
    __tablename__ = "portfolio_watch"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit_pct = Column(Float, default=0.9)  # % от таргета для алерта
    notes = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(String, default=now)
    updated_at = Column(String, default=now)


def init_trades():
    Base.metadata.create_all(engine)


def add_limit_order(ticker: str, shares: float, limit_price: float, 
                    stop_loss: float = None, take_profit: float = None,
                    rationale: str = None) -> int:
    """Добавить лимитную заявку в трекер."""
    session = SessionLocal()
    trade = Trade(
        ticker=ticker.upper(),
        direction="buy",
        status="pending",
        order_type="limit",
        limit_price=limit_price,
        shares=shares,
        stop_loss=stop_loss,
        take_profit=take_profit,
        rationale=rationale,
    )
    session.add(trade)
    session.commit()
    trade_id = trade.id
    session.close()
    return trade_id


def add_watch(ticker: str, shares: float, avg_price: float,
              target_price: float = None, stop_loss: float = None,
              notes: str = None) -> int:
    """Добавить позицию под наблюдение."""
    session = SessionLocal()
    watch = PortfolioWatch(
        ticker=ticker.upper(),
        shares=shares,
        avg_price=avg_price,
        target_price=target_price,
        stop_loss=stop_loss,
        notes=notes,
    )
    session.add(watch)
    session.commit()
    wid = watch.id
    session.close()
    return wid


def check_pending_orders(current_prices: dict[str, float]) -> list[dict]:
    """Проверить неисполненные лимитки."""
    session = SessionLocal()
    trades = session.query(Trade).filter(
        Trade.status == "pending",
        Trade.direction == "buy",
        Trade.order_type == "limit"
    ).all()
    
    alerts = []
    for t in trades:
        price = current_prices.get(t.ticker)
        if price and t.limit_price and price <= t.limit_price:
            # Цена достигла лимитки — алерт
            alerts.append({
                "type": "limit_hit",
                "ticker": t.ticker,
                "message": f"🎯 Лимитка {t.ticker} сработала! Цена {price:.2f} ≤ {t.limit_price:.2f}",
                "trade_id": t.id,
                "shares": t.shares,
                "price": price,
            })
            # Автоматически переводим в open
            t.status = "open"
            t.filled_price = price
            t.filled_at = now()
            t.commission = round(price * t.shares * 0.03, 2)
            t.updated_at = now()
    
    session.commit()
    session.close()
    return alerts


def check_watch_alerts(current_prices: dict[str, float]) -> list[dict]:
    """Проверить алерты по наблюдаемым позициям."""
    session = SessionLocal()
    watches = session.query(PortfolioWatch).filter(PortfolioWatch.active == True).all()
    
    alerts = []
    for w in watches:
        price = current_prices.get(w.ticker)
        if not price:
            continue
        
        # P&L
        pl_pct = (price / w.avg_price - 1) * 100
        pl_value = (price - w.avg_price) * w.shares
        
        # Stop-loss check
        if w.stop_loss and price <= w.stop_loss:
            alerts.append({
                "type": "stop_loss",
                "ticker": w.ticker,
                "message": f"🔴 STOP-LOSS {w.ticker}: {price:.2f} ≤ {w.stop_loss:.2f} (P&L: {pl_pct:+.2f}%)",
                "pl_pct": pl_pct,
                "pl_value": pl_value,
            })
        
        # Take-profit check
        if w.target_price and w.take_profit_pct:
            tp_level = w.target_price * w.take_profit_pct
            if price >= tp_level:
                alerts.append({
                    "type": "near_target",
                    "ticker": w.ticker,
                    "message": f"🟡 {w.ticker} у цели: {price:.2f} / {w.target_price:.2f} ({(price/w.target_price)*100:.0f}%)",
                    "pl_pct": pl_pct,
                    "pl_value": pl_value,
                })
        
        # Daily update (always)
        alerts.append({
            "type": "daily_pnl",
            "ticker": w.ticker,
            "message": f"📊 {w.ticker}: {price:.2f} | P&L: {pl_pct:+.2f}% ({pl_value:+,.0f} UZS)",
            "pl_pct": pl_pct,
            "pl_value": pl_value,
        })
    
    session.close()
    return alerts


def get_portfolio_summary(current_prices: dict[str, float]) -> dict:
    """Полная сводка по всем отслеживаемым позициям."""
    session = SessionLocal()
    watches = session.query(PortfolioWatch).filter(PortfolioWatch.active == True).all()
    trades = session.query(Trade).filter(Trade.status.in_(["pending", "open"])).all()
    
    result = {
        "positions": [],
        "pending_orders": [],
        "total_value": 0,
        "total_cost": 0,
        "total_pl": 0,
    }
    
    for w in watches:
        price = current_prices.get(w.ticker, 0)
        cost = w.shares * w.avg_price
        value = w.shares * price
        pl = value - cost
        pl_pct = (price / w.avg_price - 1) * 100 if w.avg_price else 0
        
        result["positions"].append({
            "ticker": w.ticker,
            "shares": w.shares,
            "avg_price": w.avg_price,
            "current_price": price,
            "cost": round(cost, 2),
            "value": round(value, 2),
            "pl": round(pl, 2),
            "pl_pct": round(pl_pct, 2),
            "target": w.target_price,
            "stop_loss": w.stop_loss,
        })
        result["total_cost"] += cost
        result["total_value"] += value
    
    for t in trades:
        result["pending_orders"].append({
            "id": t.id,
            "ticker": t.ticker,
            "type": t.order_type,
            "limit_price": t.limit_price,
            "shares": t.shares,
            "status": t.status,
            "rationale": t.rationale,
        })
    
    result["total_pl"] = round(result["total_value"] - result["total_cost"], 2)
    session.close()
    return result


# ===== CBSK DEAL SETUP =====

def setup_cbsk_deal():
    """Настройка отслеживания сделки по CBSK."""
    ticker = "CBSK"
    limit_price = 3.05
    shares = 150000
    target = 4.20
    stop = 2.70
    rationale = "KD таргет 4.20 (+32%). Лимитка 3.05 (середина диапазона 2.96-3.23). Стоп 2.70 (уровень майского аналитика)."

    # Добавляем лимитную заявку
    trade_id = add_limit_order(ticker, shares, limit_price, stop, target, rationale)
    
    # Добавляем позицию под наблюдение (заранее, для мониторинга)
    watch_id = add_watch(ticker, shares, limit_price, target, stop, rationale)
    
    return {
        "trade_id": trade_id,
        "watch_id": watch_id,
        "ticker": ticker,
        "limit_price": limit_price,
        "shares": shares,
        "total": round(limit_price * shares, 2),
        "commission": round(limit_price * shares * 0.03, 2),
        "target": target,
        "stop_loss": stop,
        "rationale": rationale,
        "created_at": now(),
    }


if __name__ == "__main__":
    init_trades()
    deal = setup_cbsk_deal()
    
    print("=== BGT Bot — Сделка CBSK ===")
    print(f"Тикер: {deal['ticker']}")
    print(f"Лимитка: {deal['limit_price']:.2f}")
    print(f"Кол-во: {deal['shares']:,} шт")
    print(f"Сумма: {deal['total']:,.0f} UZS")
    print(f"Комиссия 3%: {deal['commission']:,.0f} UZS")
    print(f"Таргет: {deal['target']:.2f} (+{(deal['target']/deal['limit_price']-1)*100:.0f}%)")
    print(f"Стоп-лосс: {deal['stop_loss']:.2f} ({(deal['stop_loss']/deal['limit_price']-1)*100:.0f}%)")
    print(f"Обоснование: {deal['rationale']}")
    print(f"\nТрекер активен: trade_id={deal['trade_id']}, watch_id={deal['watch_id']}")