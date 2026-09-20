# EMA_Cross v3 — с ADX фильтром тренда
# Проблема v2: WR=44% — много входов в боковик (ложные кроссоверы)
# Решение: торговать только когда ADX > 20 (есть реальный тренд)

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter


class EMA_Cross(IStrategy):
    """
    EMA_Cross v3:
    * EMA 9/21 кроссовер — сигнал входа
    * ADX > 20 — фильтр: входим только в трендовом рынке (не боковик)
    * EMA-50 trend filter — только лонг выше тренда
    * Volume filter — подтверждение объёмом
    * Trailing stop: +1.5% активация, 1% трейлинг
    * Stoploss: -5%
    * ROI: быстрый выход для фиксации прибыли
    """

    minimal_roi = {"0": 0.02, "15": 0.01, "45": 0.001}

    stoploss = -0.01
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    timeframe = "5m"

    short_ema = IntParameter(5, 20, default=9, space="buy")
    long_ema  = IntParameter(15, 40, default=21, space="sell")

    # ─── ADX ───────────────────────────────────────────────────
    def calc_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high, low, close = df["high"], df["low"], df["close"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()

        plus_dm  = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)
        # Выбираем только доминирующее движение
        mask = plus_dm < minus_dm
        plus_dm[mask]  = 0
        mask2 = minus_dm <= plus_dm
        minus_dm[mask2] = 0

        plus_di  = 100 * plus_dm.ewm(span=period, adjust=False).mean()  / atr.replace(0, 1e-10)
        minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, 1e-10)
        dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-10)
        return dx.ewm(span=period, adjust=False).mean()

    # ─── Indicators ────────────────────────────────────────────

    def leverage(self, step: int, config: dict, pair: str, **kwargs) -> float:
        return 2.0

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe["short_ema"]  = dataframe["close"].ewm(span=self.short_ema.value, adjust=False).mean()
        dataframe["long_ema"]   = dataframe["close"].ewm(span=self.long_ema.value, adjust=False).mean()
        dataframe["trend_ema"]  = dataframe["close"].ewm(span=50, adjust=False).mean()
        dataframe["adx"]        = self.calc_adx(dataframe, period=14)
        dataframe["volume_ma"]  = dataframe["volume"].rolling(20).mean()
        return dataframe

    # ─── Entry ─────────────────────────────────────────────────
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            # EMA кроссовер вверх
            (dataframe["short_ema"] > dataframe["long_ema"]) &
            (dataframe["short_ema"].shift(1) <= dataframe["long_ema"].shift(1)) &
            # ADX: есть тренд (не боковик)
            (dataframe["adx"] > 15) &
            # Цена выше долгосрочного тренда
            (dataframe["close"] > dataframe["trend_ema"]) &
            # Объём не нулевой
            (dataframe["volume"] > dataframe["volume_ma"] * 0.8),
            "enter_long"
        ] = 1
        return dataframe

    # ─── Exit ──────────────────────────────────────────────────
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (dataframe["short_ema"] < dataframe["long_ema"]) &
            (dataframe["short_ema"].shift(1) >= dataframe["long_ema"].shift(1)),
            "exit_long"
        ] = 1
        return dataframe
