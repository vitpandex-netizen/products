"""Виджет интерактивных графиков TradingView Lightweight Charts в HTML (Sprint 5)."""
import json
from typing import Dict, Any, List

class TradingViewWidget:
    @staticmethod
    def render_lightweight_chart(ticker: str, ohlcv: List[Dict[str, Any]]) -> str:
        """Генерация standalone HTML-кода с графиком TradingView Canvas."""
        chart_data = []
        for row in reversed(ohlcv):
            if row.get("date") and row.get("close"):
                chart_data.append({
                    "time": row["date"][:10],
                    "open": row.get("open", row["close"]),
                    "high": row.get("high", row["close"]),
                    "low": row.get("low", row["close"]),
                    "close": row["close"],
                    "volume": row.get("volume", 0)
                })

        json_data = json.dumps(chart_data)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingView Chart - {ticker}</title>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background-color: #131722; color: #d1d4dc; font-family: sans-serif; }}
        #chart-container {{ width: 100vw; height: 100vh; }}
        .title-overlay {{ position: absolute; top: 10px; left: 10px; z-index: 10; font-size: 16px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="title-overlay">{ticker} - UZSE Interactive Chart</div>
    <div id="chart-container"></div>
    <script>
        const chartData = {json_data};
        const container = document.getElementById('chart-container');
        const chart = LightweightCharts.createChart(container, {{
            layout: {{ backgroundColor: '#131722', textColor: '#d1d4dc' }},
            grid: {{ vertLines: {{ color: '#2B2B43' }}, horzLines: {{ color: '#2B2B43' }} }},
            crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
            priceScale: {{ borderColor: '#485c7b' }},
            timeScale: {{ borderColor: '#485c7b' }}
        }});

        const candlestickSeries = chart.addCandlestickSeries({{
            upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350'
        }});
        candlestickSeries.setData(chartData);
    </script>
</body>
</html>"""
        return html
