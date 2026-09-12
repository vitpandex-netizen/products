"""Движок алгоритмического авто-трейдинга, ребалансировки портфеля и Trailing Stop-Loss (Sprint 5 - Stage 3)."""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AutoExecutionEngine:
    def __init__(self, db=None):
        self.db = db

    def calculate_rebalance(self, target_weights: Optional[Dict[str, float]] = None, threshold_pct: float = 5.0) -> Dict[str, Any]:
        """Расчет необходимой ребалансировки портфеля при отклонении долей активов от целевых на > threshold_pct%."""
        if self.db:
            summary = self.db.get_portfolio_summary()
            positions = summary.get("positions", [])
            total_value = summary.get("total_value", 0.0)
        else:
            positions = []
            total_value = 0.0

        if not positions or total_value <= 0:
            # Тестовый фоллбэк портфель
            total_value = 100000000.0  # 100M UZS
            positions = [
                {"ticker": "URTS", "shares": 5000, "current_price": 10500, "value": 52500000},  # 52.5%
                {"ticker": "ALKB", "shares": 30000000, "current_price": 0.90, "value": 27000000}, # 27.0%
                {"ticker": "CBSK", "shares": 5882352, "current_price": 3.40, "value": 20000000}   # 20.0%
            ]

        if not target_weights:
            # Равновзвешенный целевой портфель по умолчанию (33.3% / 33.3% / 33.3%)
            num_assets = max(len(positions), 1)
            target_weights = {p["ticker"]: 100.0 / num_assets for p in positions}

        rebalance_orders = []
        for pos in positions:
            ticker = pos["ticker"]
            curr_val = pos["value"]
            curr_weight = (curr_val / total_value) * 100.0
            tgt_weight = target_weights.get(ticker, 0.0)
            diff_weight = curr_weight - tgt_weight

            if abs(diff_weight) >= threshold_pct:
                target_value = total_value * (tgt_weight / 100.0)
                val_diff = target_value - curr_val
                price = pos.get("current_price") or 1.0

                shares_diff = int(val_diff / price)
                action = "BUY" if shares_diff > 0 else "SELL"

                rebalance_orders.append({
                    "ticker": ticker,
                    "action": action,
                    "current_weight_pct": round(curr_weight, 2),
                    "target_weight_pct": round(tgt_weight, 2),
                    "deviation_pct": round(diff_weight, 2),
                    "shares_to_trade": abs(shares_diff),
                    "estimated_trade_value_uzs": round(abs(val_diff), 0),
                    "price_per_share": price
                })

        return {
            "total_portfolio_value": total_value,
            "threshold_pct": threshold_pct,
            "rebalance_required": len(rebalance_orders) > 0,
            "orders": rebalance_orders
        }

    def update_trailing_stop(self, ticker: str, current_price: float, highest_price: float, trail_pct: float = 5.0) -> Dict[str, Any]:
        """Расчет и подтяг динамического уровня Trailing Stop-Loss."""
        if current_price <= 0 or highest_price <= 0:
            return {"status": "error", "message": "Некорректные значения цен"}

        new_highest = max(highest_price, current_price)
        stop_loss_price = new_highest * (1.0 - (trail_pct / 100.0))
        is_triggered = current_price <= stop_loss_price

        return {
            "ticker": ticker,
            "current_price": current_price,
            "highest_price_reached": new_highest,
            "trail_pct": trail_pct,
            "stop_loss_price": round(stop_loss_price, 2),
            "triggered": is_triggered,
            "action": "EXECUTE_STOP_LOSS_SELL" if is_triggered else "HOLD_AND_TRAIL"
        }
