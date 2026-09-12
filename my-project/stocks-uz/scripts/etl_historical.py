#!/usr/bin/env python3
"""
ETL-скрипт для загрузки исторических данных OHLCV в InfluxDB.
"""
import os
import sys
import logging
from datetime import datetime, timedelta

try:
    import yfinance as yf
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    print("Необходимы библиотеки: pip install yfinance influxdb-client")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("etl_historical")

# Конфигурация InfluxDB (по умолчанию для локального docker-compose)
INFLUX_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN", "adminpass")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "uzstock")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "historical")

# Список тикеров для загрузки (пример, для UZSE возможно потребуется маппинг на доступные символы, 
# пока используем глобальные или аналоги)
TICKERS = ["SQBN.UZ", "HMKB.UZ", "URTS.UZ", "UZMK.UZ"]

def fetch_data(ticker, period="1y"):
    """Получает данные из Yahoo Finance (пример источника)."""
    logger.info(f"Загрузка данных для {ticker} за период {period}...")
    try:
        # Примечание: yfinance может не иметь тикеров UZSE, это шаблон
        # В реальной системе тут может быть парсер с сайта биржи или другой API
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        return df
    except Exception as e:
        logger.error(f"Ошибка при загрузке {ticker}: {e}")
        return None

def write_to_influx(df, ticker, client, write_api):
    """Записывает DataFrame в InfluxDB."""
    if df is None or df.empty:
        logger.warning(f"Нет данных для записи по тикеру {ticker}")
        return

    points = []
    for index, row in df.iterrows():
        point = (
            Point("ohlcv")
            .tag("ticker", ticker)
            .field("open", float(row["Open"]))
            .field("high", float(row["High"]))
            .field("low", float(row["Low"]))
            .field("close", float(row["Close"]))
            .field("volume", float(row["Volume"]))
            .time(index)
        )
        points.append(point)
    
    if points:
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        logger.info(f"Записано {len(points)} точек для {ticker} в InfluxDB.")

def main():
    logger.info("Начало работы ETL-скрипта InfluxDB...")
    
    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        for ticker in TICKERS:
            df = fetch_data(ticker, period="1y")
            write_to_influx(df, ticker, client, write_api)
            
    logger.info("ETL процесс успешно завершен.")

if __name__ == "__main__":
    main()
