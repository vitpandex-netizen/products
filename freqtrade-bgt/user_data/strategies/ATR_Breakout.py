# ATR_Breakout strategy for Freqtrade
# Ловит взрывные движения на всплесках волатильности (ATR spike)
# Специально разработана для максимизации прибыли в последние 12 часов

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy


class ATR_Breakout(IStrategy):
    """
    ATR Volatility Breakout v1.

    Логика: входим когда волатильность (ATR) резко выше нормы —
    это признак начала сильного направленного движения.

    Вход (лонг):
    * ATR > ATR_MA * 1.5 (волатильность взорвалась)
    * Свеча зелёная (close > open) — направление вверх
    * Цена пробила максимум последних 10 свечей (breakout)
    * RSI 45-70 (импульс есть, но не перекупленность)
    * Volume > volume_MA * 1.5 (подтверждение объёмом)
    * EMA-20 > EMA-50 (общий тренд восходящий)

    Выход: trailing_stop или ROI

    Стоп: -2% (ATR-стратегии требуют жёсткий стоп — ложные пробои опасны)
    Таймфрейм: 5m (ловим быстрые взрывы)
    """

    minimal_roi = {
        "0":  0.04,   # 4% — взрывное движение, берём сразу
        "10": 0.025,  # 2.5% через 10 мин
        "30": 0.012,  # 1.2% через 30 мин
        "60": 0.005   # 0.5% страховка
    }

    stoploss = -0.02   # -2% жёсткий стоп: ложные пробои режем быстро
    trailing_stop = True
    trailing_stop_positive = 0.008          # трейлим 0.8%
    trailing_stop_positive_offset = 0.015   # активация с +1.5%
    trailing_only_offset_is_reached = True

    timeframe = "5m"
    startup_candle_count = 50

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # ── ATR (Average True Range) ──────────────────────────
        high_low   = dataframe["high"] - dataframe["low"]
        high_close = (dataframe["high"] - dataframe["close"].shift()).abs()
        low_close  = (dataframe["low"]  - dataframe["close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        dataframe["atr"]    = true_range.ewm(span=14, adjust=False).mean()
        dataframe["atr_ma"] = dataframe["atr"].rolling(50).mean()  # норма волатильности

        # ── ATR Spike: насколько текущая волатильность выше нормы
        dataframe["atr_ratio"] = dataframe["atr"] / dataframe["atr_ma"].replace(0, 1e-10)

        # ── Breakout: пробой максимума последних N свечей ──────
        dataframe["high_10"] = dataframe["high"].rolling(10).max().shift(1)  # макс прошлых 10

        # ── EMA тренд-фильтр ──────────────────────────────────
        dataframe["ema20"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        dataframe["ema50"] = dataframe["close"].ewm(span=50, adjust=False).mean()

        # ── RSI ───────────────────────────────────────────────
        delta    = dataframe["close"].diff()
        gain     = delta.clip(lower=0)
        loss     = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs       = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        dataframe["rsi"] = 100 - (100 / (1 + rs))

        # ── Volume ────────────────────────────────────────────
        dataframe["volume_ma"] = dataframe["volume"].rolling(20).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            # 🔥 ATR spike: волатильность взорвалась (>1.5x от нормы)
            (dataframe["atr_ratio"] > 1.5) &
            # 📈 Breakout: цена пробила максимум последних 10 свечей
            (dataframe["close"] > dataframe["high_10"]) &
            # 🟢 Бычья свеча (движение вверх)
            (dataframe["close"] > dataframe["open"]) &
            # 📊 RSI в рабочей зоне (импульс есть, не перекуплен)
            (dataframe["rsi"] > 45) & (dataframe["rsi"] < 72) &
            # 🔊 Объёмный всплеск (не фейк)
            (dataframe["volume"] > dataframe["volume_ma"] * 1.3) &
            # 🏔️ Общий тренд восходящий
            (dataframe["ema20"] > dataframe["ema50"]),
            "enter_long"
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            # Волатильность успокоилась + RSI перегрет = момент упущен
            (dataframe["atr_ratio"] < 0.8) &
            (dataframe["rsi"] > 68),
            "exit_long"
        ] = 1
        return dataframe
