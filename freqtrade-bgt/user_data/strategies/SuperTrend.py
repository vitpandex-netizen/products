# SuperTrend strategy for Freqtrade
# v2: ADX filter (тренд > 20) + 15m timeframe (меньше шума)
# Проблема v1: WR=32% из-за ложных сигналов на 5m боковике
# Решение: входить только при сильном тренде (ADX > 20)

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy


class SuperTrend(IStrategy):
    """
    SuperTrend v2 — с ADX-фильтром и 15m таймфреймом.

    Логика:
    * Вход: SuperTrend бычий + ADX > 20 (сильный тренд) + RSI 45-70 + volume OK
    * Выход: SuperTrend переключился в медвежью фазу
    * Trailing stop: фиксирует прибыль от 2% прибыли
    * Stoploss: -3%
    * Timeframe: 15m (меньше ложных сигналов vs 5m)
    """

    minimal_roi = {"0": 0.02, "15": 0.01, "45": 0.001}

    stoploss = -0.01
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    timeframe = "15m"          # ключевое изменение: 5m → 15m
    startup_candle_count = 30  # ADX требует больше свечей

    # ─── SuperTrend ────────────────────────────────────────────
    def supertrend(self, df: pd.DataFrame, atr_period: int = 14, multiplier: float = 2.5):
        """SuperTrend с ATR-14 и мультипликатором 2.5 для 15m."""
        hl2 = (df["high"] + df["low"]) / 2
        high_low   = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close  = (df["low"]  - df["close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.ewm(span=atr_period, adjust=False).mean()

        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        final_upper = upper_band.copy()
        final_lower = lower_band.copy()
        direction   = pd.Series(np.ones(len(df)), index=df.index)

        for i in range(1, len(df)):
            fu_prev = final_upper.iloc[i - 1]
            fl_prev = final_lower.iloc[i - 1]
            c_prev  = df["close"].iloc[i - 1]

            final_upper.iloc[i] = upper_band.iloc[i] if upper_band.iloc[i] < fu_prev or c_prev > fu_prev else fu_prev
            final_lower.iloc[i] = lower_band.iloc[i] if lower_band.iloc[i] > fl_prev or c_prev < fl_prev else fl_prev

            if   df["close"].iloc[i] > fu_prev: direction.iloc[i] =  1
            elif df["close"].iloc[i] < fl_prev: direction.iloc[i] = -1
            else:                               direction.iloc[i] = direction.iloc[i - 1]

        return final_upper, final_lower, direction

    # ─── ADX ───────────────────────────────────────────────────
    def adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average Directional Index — измеряет силу тренда (0-100)."""
        high, low, close = df["high"], df["low"], df["close"]
        plus_dm  = (high.diff()).clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)
        plus_dm[plus_dm <= (-low.diff()).clip(lower=0)] = 0
        minus_dm[minus_dm <= (high.diff()).clip(lower=0)] = 0

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs()
        ], axis=1).max(axis=1)

        atr      = tr.ewm(span=period, adjust=False).mean()
        plus_di  = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, 1e-10)
        minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, 1e-10)
        dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-10)
        return dx.ewm(span=period, adjust=False).mean()

    # ─── Indicators ────────────────────────────────────────────

    def leverage(self, step: int, config: dict, pair: str, **kwargs) -> float:
        return 2.0

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        upper, lower, direction = self.supertrend(dataframe, atr_period=14, multiplier=2.5)
        dataframe["st_upper"]     = upper
        dataframe["st_lower"]     = lower
        dataframe["st_direction"] = direction

        # ADX — сила тренда
        dataframe["adx"] = self.adx(dataframe, period=14)

        # RSI
        delta    = dataframe["close"].diff()
        gain     = delta.clip(lower=0)
        loss     = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs       = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        dataframe["rsi"] = 100 - (100 / (1 + rs))

        # Объём
        dataframe["volume_ma"] = dataframe["volume"].rolling(20).mean()

        return dataframe

    # ─── Entry ─────────────────────────────────────────────────
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (dataframe["st_direction"] == 1) &                       # SuperTrend бычий
            (dataframe["st_direction"].shift(1) == -1) &             # только что переключился
            (dataframe["adx"] > 20) &                                # ADX: тренд сильный
            (dataframe["rsi"] > 45) & (dataframe["rsi"] < 72) &      # RSI в рабочей зоне
            (dataframe["volume"] > dataframe["volume_ma"] * 0.7),    # объём нормальный
            "enter_long"
        ] = 1
        return dataframe

    # ─── Exit ──────────────────────────────────────────────────
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (dataframe["st_direction"] == -1) &
            (dataframe["st_direction"].shift(1) == 1),
            "exit_long"
        ] = 1
        return dataframe
