import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class UltraScalper(IStrategy):
    INTERFACE_VERSION = 3
    
    # 1-minute chart for maximum action
    timeframe = '1m'

    # Lightning fast take profit
    minimal_roi = {
        "0": 0.007,  # 0.7% with 5x leverage is 3.5% ROE
        "5": 0.003,
        "10": 0.001,
        "15": 0
    }

    # Tight stoploss
    stoploss = -0.015  # -1.5%

    # Trailing stop to lock in profits
    trailing_stop = True
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.005
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    startup_candle_count: int = 30

    # 5x Leverage
    def leverage(self, step: str, config: dict, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['ema8'] = ta.EMA(dataframe, timeperiod=8)
        dataframe['ema21'] = ta.EMA(dataframe, timeperiod=21)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long when EMA8 crosses above EMA21 and RSI is not overbought
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe['ema8'], dataframe['ema21']) &
                (dataframe['rsi'] < 65) &
                (dataframe['volume'] > 0)
            ),
            ['enter_long', 'enter_tag']] = (1, 'ema_cross_long')

        # Short when EMA8 crosses below EMA21 and RSI is not oversold
        dataframe.loc[
            (
                qtpylib.crossed_below(dataframe['ema8'], dataframe['ema21']) &
                (dataframe['rsi'] > 35) &
                (dataframe['volume'] > 0)
            ),
            ['enter_short', 'enter_tag']] = (1, 'ema_cross_short')
            
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (qtpylib.crossed_below(dataframe['ema8'], dataframe['ema21'])),
            'exit_long'
        ] = 1

        dataframe.loc[
            (qtpylib.crossed_above(dataframe['ema8'], dataframe['ema21'])),
            'exit_short'
        ] = 1
        
        return dataframe
