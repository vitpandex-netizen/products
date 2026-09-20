# RSI_Bollinger strategy for Freqtrade
# v2 — смягчённые пороги для большего числа сделок и быстрее ROI

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter


class RSI_Bollinger(IStrategy):
    """
    Вход: RSI < 35 + цена ≤ нижней полосе Боллинджера (был 30 — слишком редко).
    Выход: RSI > 65 + цена ≥ верхней полосе (был 70).
    Добавлен trailing_stop для фиксации прибыли на движении.
    """

    minimal_roi = {"0": 0.02, "10": 0.015, "30": 0.008, "60": 0.003}
    stoploss = -0.02  # v4: -2% (был -1.5% — слишком жёсткий, давал лишние стопы на шуме)
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    timeframe = "5m"

    # Параметры (можно оптимизировать через hyperopt)
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=False)
    bb_window = IntParameter(15, 30, default=20, space="buy", optimize=False)
    bb_std = DecimalParameter(1.5, 2.5, default=2.0, space="buy", optimize=False)
    rsi_buy_threshold = IntParameter(25, 40, default=35, space="buy", optimize=False)
    rsi_sell_threshold = IntParameter(60, 75, default=65, space="sell", optimize=False)

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # RSI через EWM (более точный чем rolling)
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=self.rsi_period.value - 1, min_periods=self.rsi_period.value).mean()
        avg_loss = loss.ewm(com=self.rsi_period.value - 1, min_periods=self.rsi_period.value).mean()
        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        dataframe["rsi"] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        bb_mean = dataframe["close"].rolling(self.bb_window.value).mean()
        bb_std_val = dataframe["close"].rolling(self.bb_window.value).std()
        dataframe["bb_lower"] = bb_mean - self.bb_std.value * bb_std_val
        dataframe["bb_upper"] = bb_mean + self.bb_std.value * bb_std_val
        dataframe["bb_mid"] = bb_mean

        # Объём-фильтр: входим только при объёме выше среднего
        dataframe["volume_ma"] = dataframe["volume"].rolling(20).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (dataframe["rsi"] < self.rsi_buy_threshold.value) &
            (dataframe["close"] <= dataframe["bb_lower"]) &
            (dataframe["volume"] > dataframe["volume_ma"] * 0.8),  # объём не ниже 80% среднего
            "enter_long"
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (dataframe["rsi"] > self.rsi_sell_threshold.value) &
            (dataframe["close"] >= dataframe["bb_upper"]),
            "exit_long"
        ] = 1
        return dataframe
