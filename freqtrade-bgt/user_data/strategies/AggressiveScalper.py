import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class AggressiveScalper(IStrategy):
    INTERFACE_VERSION = 3
    
    # Максимально быстрый таймфрейм для спринта
    timeframe = '1m'

    # Быстрый Take Profit (1.5% сразу, 0.5% через 10 минут)
    minimal_roi = {
        "0": 0.015,
        "10": 0.005,
        "20": 0.002,
        "30": 0
    }

    # Короткий стоп-лосс (с учетом плеча х5 это 15% от маржи)
    stoploss = -0.03

    # Трейлинг стоп для захвата пампов
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    startup_candle_count: int = 30

    # АГРЕССИВНОЕ ПЛЕЧО x5 (Futures)
    def leverage(self, step: str, config: dict, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Bollinger Bands (волатильность)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2.5)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        
        # RSI для подтверждения перепроданности
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Объемный фильтр (Money Flow Index)
        dataframe['mfi'] = ta.MFI(dataframe, timeperiod=14)
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ЛОНГ: Цена пробила нижний Боллинджер + RSI на дне + зашли объемы
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['rsi'] < 30) &
                (dataframe['volume'] > 0)
            ),
            ['enter_long', 'enter_tag']] = (1, 'scalp_dip_long')
        
        # ШОРТ: Цена пробила верхний Боллинджер + RSI в небесах
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['bb_upperband']) &
                (dataframe['rsi'] > 70) &
                (dataframe['volume'] > 0)
            ),
            ['enter_short', 'enter_tag']] = (1, 'scalp_peak_short')
            
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Экстренный выход по RSI, если не дошли до профита
        dataframe.loc[
            (dataframe['rsi'] > 80), 'exit_long'
        ] = 1
        
        dataframe.loc[
            (dataframe['rsi'] < 20), 'exit_short'
        ] = 1
        
        return dataframe
