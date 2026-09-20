# VWAP_RSI strategy for Freqtrade
# VWAP (Volume Weighted Average Price) + RSI + Bollinger Bands
# Популярная институциональная стратегия для внутридневной торговли

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy


class VWAP_RSI(IStrategy):
    """
    VWAP + RSI стратегия.

    Логика:
    * Цена отскочила от VWAP снизу вверх (close crossed above VWAP)
    * RSI < 55 (не перекупленность — есть пространство для роста)
    * Цена была ниже BB нижней полосы (перепроданность)
    * Volume spike — объём выше среднего (институциональный вход)

    Выход:
    * RSI > 65 — зона перекупленности
    * Цена выше BB верхней полосы
    * Trailing stop фиксирует прибыль

    VWAP — главный индикатор банков и хедж-фондов. Когда цена
    возвращается выше VWAP — это сигнал возобновления восходящего тренда.
    """

    minimal_roi = {
        "0":  0.025,  # 2.5% быстрый выход (на 3m достаточно)
        "15": 0.015,  # 1.5% через 15 мин
        "40": 0.008,  # 0.8% через 40 мин
        "90": 0.003   # 0.3% — минимальный
    }

    stoploss = -0.02   # -2% стоп (чуть жёстче для 3m)
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.012
    trailing_only_offset_is_reached = True

    timeframe = "3m"   # 5m → 3m: утраиваем кол-во сигналов
    startup_candle_count = 40

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # ── VWAP ─────────────────────────────────────────────
        # VWAP = сумма(типичная_цена * объём) / сумма(объём) за сессию
        # Аппроксимируем через rolling 50 свечей (≈4 часа на 5m)
        typical_price = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3
        tp_volume = typical_price * dataframe["volume"]
        dataframe["vwap"] = (
            tp_volume.rolling(window=50, min_periods=1).sum() /
            dataframe["volume"].rolling(window=50, min_periods=1).sum()
        )

        # ── RSI ──────────────────────────────────────────────
        delta    = dataframe["close"].diff()
        gain     = delta.clip(lower=0)
        loss     = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs       = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        dataframe["rsi"] = 100 - (100 / (1 + rs))

        # ── Bollinger Bands (20, 2.0) ─────────────────────────
        bb_mean = dataframe["close"].rolling(20).mean()
        bb_std  = dataframe["close"].rolling(20).std()
        dataframe["bb_upper"]  = bb_mean + 2.0 * bb_std
        dataframe["bb_lower"]  = bb_mean - 2.0 * bb_std
        dataframe["bb_middle"] = bb_mean

        # ── Volume spike ─────────────────────────────────────
        dataframe["volume_ma"]    = dataframe["volume"].rolling(20).mean()
        dataframe["volume_spike"] = dataframe["volume"] > dataframe["volume_ma"] * 1.2

        # ── VWAP distance ────────────────────────────────────
        # Насколько % цена отклонилась от VWAP
        dataframe["vwap_dist"] = (dataframe["close"] - dataframe["vwap"]) / dataframe["vwap"] * 100

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            # Цена пересекла VWAP снизу вверх — разворот
            (dataframe["close"] > dataframe["vwap"]) &
            (dataframe["close"].shift(1) <= dataframe["vwap"].shift(1)) &
            # RSI не перекуплен — есть пространство для роста
            (dataframe["rsi"] > 35) &
            (dataframe["rsi"] < 58) &
            # Цена недавно была перепродана (BB нижняя полоса)
            (dataframe["bb_lower"].shift(3) >= dataframe["close"].shift(3)) |
            # ИЛИ: цена у VWAP + RSI отскок + объём
            (
                (dataframe["vwap_dist"].abs() < 0.3) &      # цена близко к VWAP
                (dataframe["rsi"] < 50) &                    # RSI ниже нейтрали
                (dataframe["volume_spike"] == True)          # объёмный всплеск
            ),
            "enter_long"
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            # RSI в зоне перекупленности
            (dataframe["rsi"] > 65) &
            # Цена выше верхней BB — момент взят
            (dataframe["close"] >= dataframe["bb_upper"]),
            "exit_long"
        ] = 1
        return dataframe
