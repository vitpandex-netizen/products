from jesse.strategies import Strategy, cached
import jesse.indicators as ta
from jesse import utils

class AggressiveMomentum(Strategy):
    @property
    def bb(self):
        return ta.bollinger_bands(self.candles, period=20, devup=2.5, devdn=2.5)

    def should_long(self) -> bool:
        return self.price > self.bb.upperband

    def should_short(self) -> bool:
        return self.price < self.bb.lowerband

    @property
    def qty(self):
        # 5x leverage of the capital for this route
        return utils.size_to_qty(self.capital * 5, self.price, fee_rate=self.fee_rate)

    def go_long(self):
        entry_price = self.price
        self.buy = self.qty, entry_price
        # Tight stoploss
        self.stop_loss = self.qty, entry_price * 0.985
        # Fast Take profit
        self.take_profit = self.qty, entry_price * 1.015

    def go_short(self):
        entry_price = self.price
        self.sell = self.qty, entry_price
        self.stop_loss = self.qty, entry_price * 1.015
        self.take_profit = self.qty, entry_price * 0.985

    def update_position(self):
        if self.is_long and self.price > self.average_entry_price * 1.005:
            # Move stoploss to breakeven + trailing
            self.stop_loss = self.qty, self.price * 0.995
        elif self.is_short and self.price < self.average_entry_price * 0.995:
            self.stop_loss = self.qty, self.price * 1.005
