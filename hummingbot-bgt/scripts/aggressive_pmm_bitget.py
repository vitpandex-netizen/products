import os
from decimal import Decimal
from typing import Dict, List

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType, PriceType, TradeType
from hummingbot.core.data_type.order_candidate import OrderCandidate
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class AggressivePMM(ScriptStrategyBase):
    """
    Very tight Pure Market Making script for high volatility pairs.
    """
    bid_spread = 0.0015  # 0.15% 
    ask_spread = 0.0015  # 0.15% 
    order_amount = Decimal("20")  # $20 per order
    order_refresh_time = 15       # Cancel and replace every 15 seconds
    
    # Paper trade bitget spot (connector name in paper trade is usually just the exchange name)
    exchange = "bitget_paper_trade" 
    trading_pair = "SOL-USDT"

    markets = {exchange: {trading_pair}}

    def on_tick(self):
        # Cancel all orders older than the refresh time
        for order in self.get_active_orders(connector_name=self.exchange):
            self.cancel(self.exchange, order.trading_pair, order.client_order_id)

        # Place new orders
        proposal: List[OrderCandidate] = self.create_proposal()
        for order_candidate in proposal:
            if order_candidate.order_side == TradeType.BUY:
                self.buy(
                    connector_name=self.exchange,
                    trading_pair=order_candidate.trading_pair,
                    amount=order_candidate.amount,
                    order_type=order_candidate.order_type,
                    price=order_candidate.price
                )
            elif order_candidate.order_side == TradeType.SELL:
                self.sell(
                    connector_name=self.exchange,
                    trading_pair=order_candidate.trading_pair,
                    amount=order_candidate.amount,
                    order_type=order_candidate.order_type,
                    price=order_candidate.price
                )

    def create_proposal(self) -> List[OrderCandidate]:
        proposal = []
        mid_price = self.connectors[self.exchange].get_mid_price(self.trading_pair)

        buy_price = mid_price * Decimal(1 - self.bid_spread)
        sell_price = mid_price * Decimal(1 + self.ask_spread)

        # Amount in base asset (SOL)
        buy_amount = self.order_amount / buy_price
        sell_amount = self.order_amount / sell_price

        proposal.append(OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                       order_side=TradeType.BUY, amount=buy_amount, price=buy_price))
        proposal.append(OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                       order_side=TradeType.SELL, amount=sell_amount, price=sell_price))
        return proposal
