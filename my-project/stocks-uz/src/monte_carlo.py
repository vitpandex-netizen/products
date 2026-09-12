"""Симуляция портфельных рисков методом Монте-Карло (Sprint 5)."""
import random
import math
from typing import Dict, Any, List

class MonteCarloSimulator:
    def __init__(self, db=None):
        self.db = db

    def simulate_portfolio(self, portfolio_summary: Dict[str, Any] = None, simulations: int = 1000, days: int = 30) -> Dict[str, Any]:
        """Запуск 1,000 вероятностных путей развития стоимости портфеля (Geometric Brownian Motion)."""
        summary = portfolio_summary
        if summary is None and self.db:
            summary = self.db.get_portfolio_summary()

        total_value = summary.get("total_value", 0.0) if summary else 0.0
        if total_value <= 0:
            total_value = 10000000.0  # Fallback 10M UZS for simulation testing

        # Предполагаемые параметры рынка UZSE (средняя доходность и волатильность)
        mu = 0.0005  # Daily expected return (~12% per year)
        sigma = 0.015  # Daily volatility (~24% per year)

        final_values = []
        for _ in range(simulations):
            current = total_value
            for _ in range(days):
                # Box-Muller transform for normal distribution
                u1 = random.random()
                u2 = random.random()
                z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

                daily_return = mu + sigma * z
                current *= (1.0 + daily_return)
            final_values.append(current)

        final_values.sort()

        # Calculate Value at Risk (VaR 95%) and Expected Shortfall (CVaR 95%)
        idx_5pct = int(simulations * 0.05)
        var_95_value = final_values[idx_5pct]
        var_95_loss = total_value - var_95_value
        var_95_pct = (var_95_loss / total_value) * 100

        cvar_5pct_list = final_values[:idx_5pct]
        cvar_val = sum(cvar_5pct_list) / max(len(cvar_5pct_list), 1)
        cvar_loss = total_value - cvar_val
        cvar_pct = (cvar_loss / total_value) * 100

        median_val = final_values[int(simulations * 0.5)]

        return {
            "initial_portfolio_value": total_value,
            "simulations_count": simulations,
            "horizon_days": days,
            "median_projected_value": round(median_val, 2),
            "var_95_loss_uzs": round(max(var_95_loss, 0), 2),
            "var_95_loss_pct": round(max(var_95_pct, 0), 2),
            "cvar_95_loss_uzs": round(max(cvar_loss, 0), 2),
            "cvar_95_loss_pct": round(max(cvar_pct, 0), 2),
            "worst_case_value": round(final_values[0], 2),
            "best_case_value": round(final_values[-1], 2)
        }
