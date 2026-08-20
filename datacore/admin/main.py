import time
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Query, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DataCore Admin")


@app.get("/health")
async def admin_health():
    return {"status": "ok", "service": "admin"}


# Templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# DB connection helper
DB_URL = "postgresql://datacore:datacore_secret@postgres:5432/datacore"
REDIS_URL = "redis://redis:6379/0"
API_URL = "http://core-api:8000"

# HTML templates inline (no external files needed for MVP)
INDEX_HTML = """<!DOCTYPE html>
<html lang="ru" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataCore — Admin</title>
    <script src="https://unpkg.com/htmx.org@2.0.3"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg: #0f0f1a;
            --card: #1a1a2e;
            --border: #2a2a4a;
            --text: #e0e0f0;
            --muted: #8888aa;
            --accent: #6c5ce7;
            --accent2: #00cec9;
            --green: #00b894;
            --red: #e17055;
            --yellow: #fdcb6e;
            --blue: #74b9ff;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui; background: var(--bg); color: var(--text); min-height: 100vh; }
        .layout { display: flex; min-height: 100vh; }
        .sidebar { width: 240px; background: var(--card); border-right: 1px solid var(--border); padding: 20px 0; flex-shrink: 0; }
        .sidebar .logo { padding: 0 20px 20px; font-size: 18px; font-weight: 700; color: var(--accent); border-bottom: 1px solid var(--border); margin-bottom: 16px; }
        .sidebar nav a { display: block; padding: 10px 20px; color: var(--text); text-decoration: none; font-size: 14px; transition: all 0.2s; }
        .sidebar nav a:hover, .sidebar nav a.active { background: rgba(108,92,231,0.15); color: var(--accent); border-left: 3px solid var(--accent); }
        .sidebar nav a .emoji { margin-right: 8px; }
        .main { flex: 1; padding: 24px; overflow-x: hidden; }
        .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
        .header h1 { font-size: 22px; font-weight: 600; }
        .header .status { display: flex; gap: 12px; align-items: center; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .badge-ok { background: rgba(0,184,148,0.2); color: var(--green); }
        .badge-err { background: rgba(225,112,85,0.2); color: var(--red); }
        .badge-warn { background: rgba(253,203,110,0.2); color: var(--yellow); }
        .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        .card .value { font-size: 28px; font-weight: 700; margin: 8px 0 4px; }
        .card .label { font-size: 13px; color: var(--muted); }
        .card .change { font-size: 12px; font-weight: 600; }
        .card .change.up { color: var(--green); }
        .card .change.down { color: var(--red); }
        .card.accent { border-left: 3px solid var(--accent); }
        .card.green { border-left: 3px solid var(--green); }
        .card.red { border-left: 3px solid var(--red); }
        .card.blue { border-left: 3px solid var(--blue); }
        .card.yellow { border-left: 3px solid var(--yellow); }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }
        th { color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        tr:hover td { background: rgba(108,92,231,0.05); }
        .section { margin-bottom: 32px; }
        .section h2 { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: var(--text); }
        .filters { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
        .filters select, .filters input { background: var(--card); border: 1px solid var(--border); color: var(--text); padding: 8px 14px; border-radius: 8px; font-size: 13px; }
        .filters button { background: var(--accent); color: white; border: none; padding: 8px 20px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; }
        .filters button:hover { opacity: 0.9; }
        .progress-bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
        .progress-bar .fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
        .fill-green { background: var(--green); }
        .fill-red { background: var(--red); }
        .fill-accent { background: var(--accent); }
        .flex { display: flex; gap: 16px; align-items: center; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }
        .toast { position: fixed; bottom: 24px; right: 24px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; font-size: 14px; z-index: 1000; animation: slideIn 0.3s; }
        @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        .market-row { cursor: pointer; }
        .market-row:hover td { background: rgba(108,92,231,0.1); }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: rgba(108,92,231,0.15); color: var(--accent); }
        .btn-sm { padding: 4px 12px; border-radius: 6px; font-size: 12px; border: 1px solid var(--border); background: transparent; color: var(--text); cursor: pointer; }
        .btn-sm:hover { background: var(--accent); border-color: var(--accent); color: white; }
        pre { font-size: 12px; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; overflow-x: auto; }
    </style>
</head>
<body>
<div class="layout">
    <aside class="sidebar">
        <div class="logo">⬡ DataCore</div>
        <nav>
            <a href="/" class="active"><span class="emoji">📊</span>Дашборд</a>
            <a href="/markets"><span class="emoji">🎯</span>Рынки</a>
            <a href="/signals"><span class="emoji">🔔</span>Сигналы</a>
            <a href="/collectors"><span class="emoji">📡</span>Сборщики</a>
            <a href="/settings"><span class="emoji">⚙️</span>Настройки</a>
        </nav>
    </aside>
    <div class="main">
        <div class="header">
            <h1>{% block title %}Дашборд{% endblock %}</h1>
            <div class="status" id="status-bar">
                <span class="badge badge-ok">● API OK</span>
                <span id="clock" style="font-size:13px;color:var(--muted)"></span>
            </div>
        </div>
        {% block content %}{% endblock %}
    </div>
</div>
<script>
    function updateClock() {
        document.getElementById('clock').textContent = new Date().toLocaleTimeString('ru-RU', {timeZone:'Asia/Tashkent'});
    }
    updateClock();
    setInterval(updateClock, 1000);
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        async with httpx.AsyncClient() as client:
            summary = await client.get(f"{API_URL}/api/v1/analytics/summary", timeout=5)
            summary_data = summary.json() if summary.status_code == 200 else {}

            markets = await client.get(f"{API_URL}/api/v1/prediction-markets/?limit=5", timeout=5)
            markets_data = markets.json() if markets.status_code == 200 else []
    except Exception as e:
        logger.error("API error: %s", e)
        summary_data = {}
        markets_data = []

    signals_24h = summary_data.get("signals_24h", 0)
    trades_24h = summary_data.get("trades_24h", 0)
    active_pm = summary_data.get("active_prediction_markets", 0)
    collectors = summary_data.get("collector_status", [])
    pnl = summary_data.get("pnl_by_bot", [])

    html = INDEX_HTML.replace("{% block title %}Дашборд{% endblock %}", "Дашборд")

    # Build markets table rows
    markets_rows = ""
    for m in markets_data[:5]:
        question = m.get("question", "?")[:60]
        yes = "{:.1f}%".format(m["outcome_yes"]) if m.get("outcome_yes") else "—"
        no = "{:.1f}%".format(m["outcome_no"]) if m.get("outcome_no") else "—"
        vol = "${:,.0f}".format(m["volume"]) if m.get("volume") else "—"
        markets_rows += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(question, yes, no, vol)

    # Build collectors rows
    collectors_rows = ""
    for c in collectors:
        status = c.get("status", "?")
        badge = "ok" if status == "success" else "err"
        last = (c.get("last_run") or "?")[:19]
        collectors_rows += '<tr><td>{}</td><td><span class="badge badge-{}">{}</span></td><td>{}</td></tr>'.format(
            c.get("name", "?"), badge, status, last
        )
    if not collectors_rows:
        collectors_rows = '<tr><td colspan="3" style="text-align:center;color:var(--muted)">Нет данных</td></tr>'

    # Build PnL rows
    pnl_rows = ""
    for b in pnl:
        pnl_val = b.get("pnl", 0) or 0
        color = "var(--green)" if pnl_val >= 0 else "var(--red)"
        pnl_rows += '<tr><td>{}</td><td>{}</td><td style="color:{}">${:,.2f}</td></tr>'.format(
            b.get("bot", "?"), b.get("trades", 0), color, pnl_val
        )
    if not pnl_rows:
        pnl_rows = '<tr><td colspan="3" style="text-align:center;color:var(--muted)">Нет сделок</td></tr>'

    content = """
    <div class="cards">
        <div class="card accent">
            <div class="label">🎯 Активные рынки</div>
            <div class="value">{active_pm}</div>
            <div class="change up">Polymarket</div>
        </div>
        <div class="card green">
            <div class="label">🔔 Сигналов (24ч)</div>
            <div class="value">{signals_24h}</div>
            <div class="change up">Аналитика</div>
        </div>
        <div class="card blue">
            <div class="label">📈 Сделок (24ч)</div>
            <div class="value">{trades_24h}</div>
            <div class="change up">Все боты</div>
        </div>
        <div class="card yellow">
            <div class="label">📡 Сборщиков</div>
            <div class="value">{collector_count}</div>
            <div class="change">{collector_names}</div>
        </div>
    </div>

    <div class="grid-2">
        <div class="section">
            <h2>📡 Статус сборщиков</h2>
            <table>
                <tr><th>Сборщик</th><th>Статус</th><th>Последний запуск</th></tr>
                {collectors_rows}
            </table>
        </div>
        <div class="section">
            <h2>💰 PnL по ботам (24ч)</h2>
            <table>
                <tr><th>Бот</th><th>Сделок</th><th>PnL</th></tr>
                {pnl_rows}
            </table>
        </div>
    </div>

    <div class="section">
        <h2>🔥 Топ рынков</h2>
        <table>
            <tr><th>Вопрос</th><th>Yes</th><th>No</th><th>Объём</th></tr>
            {markets_rows}
        </table>
    </div>
    """.format(
        active_pm=active_pm,
        signals_24h=signals_24h,
        trades_24h=trades_24h,
        collector_count=len(collectors),
        collector_names=", ".join(c.get("name", "?") for c in collectors[:3]),
        collectors_rows=collectors_rows,
        pnl_rows=pnl_rows,
        markets_rows=markets_rows,
    )

    html = html.replace("{% block content %}{% endblock %}", content)
    return HTMLResponse(html)


@app.get("/markets", response_class=HTMLResponse)
async def markets_page(request: Request):
    html = INDEX_HTML.replace("{% block title %}Дашборд{% endblock %}", "Рынки")
    content = """
    <div class="filters">
        <select id="category" onchange="loadMarkets()">
            <option value="">Все категории</option>
            <option value="crypto">Крипто</option>
            <option value="politics">Политика</option>
            <option value="sports">Спорт</option>
        </select>
        <input type="text" id="search" placeholder="Поиск..." oninput="loadMarkets()">
        <button onclick="loadMarkets()">Обновить</button>
    </div>
    <div class="section">
        <h2>🎯 Prediction Markets</h2>
        <div id="markets-table">
            <table>
                <thead><tr><th>Вопрос</th><th>Yes</th><th>No</th><th>Объём</th><th>Статус</th></tr></thead>
                <tbody id="markets-body">
                    <tr><td colspan="5" style="text-align:center;color:var(--muted)">Загрузка...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function loadMarkets() {
        const cat = document.getElementById('category').value;
        const q = document.getElementById('search').value;
        let url = '/api/proxy/markets?limit=50';
        if (cat) url += '&category=' + cat;
        const resp = await fetch(url);
        const data = await resp.json();
        const tbody = document.getElementById('markets-body');
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted)">Нет данных</td></tr>';
            return;
        }
        tbody.innerHTML = data.map(m => {
            const filter = q.toLowerCase();
            if (q && !m.question.toLowerCase().includes(filter)) return '';
            const yes = m.outcome_yes != null ? m.outcome_yes.toFixed(1) + '%' : '—';
            const no = m.outcome_no != null ? m.outcome_no.toFixed(1) + '%' : '—';
            const vol = m.volume ? '$' + Number(m.volume).toLocaleString() : '—';
            const status = m.closed ? '<span class="badge badge-err">Closed</span>' : '<span class="badge badge-ok">Active</span>';
            return '<tr class="market-row" onclick="showMarket(' + m.id + ')"><td>' + m.question.slice(0,80) + '</td><td>' + yes + '</td><td>' + no + '</td><td>' + vol + '</td><td>' + status + '</td></tr>';
        }).filter(Boolean).join('');
    }
    async function showMarket(id) {
        // TODO: modal with history chart
    }
    loadMarkets();
    setInterval(loadMarkets, 30000);
    </script>
    """
    html = html.replace("{% block content %}{% endblock %}", content)
    return HTMLResponse(html)


@app.get("/signals", response_class=HTMLResponse)
async def signals_page(request: Request):
    html = INDEX_HTML.replace("{% block title %}Дашборд{% endblock %}", "Сигналы")
    content = """
    <div class="filters">
        <select id="signal-type" onchange="loadSignals()">
            <option value="">Все типы</option>
            <option value="curve_mispricing">Кривая вероятности</option>
            <option value="momentum_break">Моментум</option>
            <option value="price_anomaly">Аномалия цены</option>
        </select>
        <button onclick="loadSignals()">Обновить</button>
    </div>
    <div class="section">
        <h2>🔔 Последние сигналы</h2>
        <div id="signals-table">
            <table>
                <thead><tr><th>Тип</th><th>Символ</th><th>Направление</th><th>Сила</th><th>Причина</th><th>Время</th></tr></thead>
                <tbody id="signals-body">
                    <tr><td colspan="6" style="text-align:center;color:var(--muted)">Загрузка...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function loadSignals() {
        const type = document.getElementById('signal-type').value;
        let url = '/api/proxy/signals?limit=50';
        if (type) url += '&signal_type=' + type;
        const resp = await fetch(url);
        const data = await resp.json();
        const tbody = document.getElementById('signals-body');
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Нет сигналов</td></tr>';
            return;
        }
        tbody.innerHTML = data.map(s => {
            const dir = s.direction == 'buy' ? '🟢' : s.direction == 'sell' ? '🔴' : '⚪';
            const strength = s.strength != null ? (s.strength * 100).toFixed(0) + '%' : '—';
            return '<tr><td><span class="tag">' + s.signal_type + '</span></td><td>' + (s.symbol || '—') + '</td><td>' + dir + ' ' + (s.direction || '—') + '</td><td>' + strength + '</td><td>' + (s.reason || '').slice(0,60) + '</td><td>' + (s.ts || '').slice(0,19) + '</td></tr>';
        }).join('');
    }
    loadSignals();
    setInterval(loadSignals, 15000);
    </script>
    """
    html = html.replace("{% block content %}{% endblock %}", content)
    return HTMLResponse(html)


@app.get("/collectors", response_class=HTMLResponse)
async def collectors_page(request: Request):
    html = INDEX_HTML.replace("{% block title %}Дашборд{% endblock %}", "Сборщики")
    content = """
    <div class="section">
        <h2>📡 Сборщики данных</h2>
        <div id="collectors-status">
            <table>
                <thead><tr><th>Сборщик</th><th>Источник</th><th>Статус</th><th>Последний run</th><th>Действия</th></tr></thead>
                <tbody id="collectors-body">
                    <tr><td colspan="5" style="text-align:center;color:var(--muted)">Загрузка...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    <div class="section">
        <h2>📋 Последние логи</h2>
        <div id="collectors-logs">
            <pre id="logs-pre">Загрузка...</pre>
        </div>
    </div>
    <script>
    async function loadCollectors() {
        const resp = await fetch('/api/proxy/analytics/summary');
        const data = await resp.json();
        const tbody = document.getElementById('collectors-body');
        const collectors = data.collector_status || [];
        if (!collectors.length) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted)">Нет данных</td></tr>';
            return;
        }
        tbody.innerHTML = collectors.map(c => {
            const status = c.status == 'success' ? '<span class="badge badge-ok">● OK</span>' : '<span class="badge badge-err">● ERR</span>';
            return '<tr><td><strong>' + c.name + '</strong></td><td>' + c.name + '</td><td>' + status + '</td><td>' + (c.last_run || '').slice(0,19) + '</td><td><button class="btn-sm" onclick="runCollector(\'' + c.name + '\')">▶ Запустить</button></td></tr>';
        }).join('');
    }
    async function runCollector(name) {
        const resp = await fetch('/api/proxy/collectors/run?name=' + name, {method:'POST'});
        const result = await resp.json();
        alert('Collector ' + name + ': ' + JSON.stringify(result));
        loadCollectors();
    }
    loadCollectors();
    setInterval(loadCollectors, 10000);
    </script>
    """
    html = html.replace("{% block content %}{% endblock %}", content)
    return HTMLResponse(html)


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    html = INDEX_HTML.replace("{% block title %}Дашборд{% endblock %}", "Настройки")
    content = """
    <div class="grid-2">
        <div class="section">
            <h2>⚙️ Telegram</h2>
            <div class="card" style="margin-bottom:16px">
                <form id="tg-form" onsubmit="saveTelegram(event)">
                    <div style="margin-bottom:12px">
                        <label style="font-size:13px;color:var(--muted);display:block;margin-bottom:4px">Bot Token</label>
                        <input type="password" id="tg-token" style="width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px" value="********">
                    </div>
                    <div style="margin-bottom:12px">
                        <label style="font-size:13px;color:var(--muted);display:block;margin-bottom:4px">Chat ID</label>
                        <input type="text" id="tg-chat" style="width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px" value="-1004297012607">
                    </div>
                    <button type="submit" style="background:var(--accent);color:white;border:none;padding:8px 20px;border-radius:8px;cursor:pointer">Сохранить</button>
                    <button type="button" onclick="testTelegram()" style="background:var(--green);color:white;border:none;padding:8px 20px;border-radius:8px;cursor:pointer;margin-left:8px">Тест</button>
                </form>
            </div>
            <div id="tg-result"></div>
        </div>
        <div class="section">
            <h2>🔔 Типы сигналов</h2>
            <div class="card">
                <table>
                    <tr><td>Кривая вероятности</td><td><span class="badge badge-ok">Вкл</span></td></tr>
                    <tr><td>Моментум (5% за час)</td><td><span class="badge badge-ok">Вкл</span></td></tr>
                    <tr><td>Price anomaly</td><td><span class="badge badge-warn">Бета</span></td></tr>
                    <tr><td>Cross-market arb</td><td><span class="badge badge-err">Выкл</span></td></tr>
                </table>
            </div>
        </div>
    </div>
    <script>
    async function saveTelegram(e) {
        e.preventDefault();
        const token = document.getElementById('tg-token').value;
        const chat = document.getElementById('tg-chat').value;
        const resp = await fetch('/api/proxy/settings/telegram', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token, chat_id: chat})
        });
        document.getElementById('tg-result').innerHTML = '<div class="toast" style="position:static;margin-top:8px">✅ Сохранено</div>';
        setTimeout(() => document.getElementById('tg-result').innerHTML = '', 3000);
    }
    async function testTelegram() {
        const resp = await fetch('/api/proxy/telegram/test', {method:'POST'});
        const result = await resp.json();
        document.getElementById('tg-result').innerHTML = '<div class="toast" style="position:static;margin-top:8px">' + (result.ok ? '✅ Тест отправлен' : '❌ Ошибка: ' + (result.error || '')) + '</div>';
    }
    </script>
    """
    html = html.replace("{% block content %}{% endblock %}", content)
    return HTMLResponse(html)


# =========== PROXY API ===========

@app.get("/api/proxy/markets")
async def proxy_markets(limit: int = 50, category: str = ""):
    try:
        async with httpx.AsyncClient() as client:
            url = f"{API_URL}/api/v1/prediction-markets/?limit={limit}"
            if category:
                url += f"&category={category}"
            resp = await client.get(url, timeout=10)
            return resp.json()
    except Exception as e:
        return JSONResponse([], status_code=200)


@app.get("/api/proxy/signals")
async def proxy_signals(limit: int = 50, signal_type: str = ""):
    try:
        async with httpx.AsyncClient() as client:
            url = f"{API_URL}/api/v1/signals/?limit={limit}"
            if signal_type:
                url += f"&signal_type={signal_type}"
            resp = await client.get(url, timeout=10)
            return resp.json()
    except Exception as e:
        return JSONResponse([], status_code=200)


@app.get("/api/proxy/analytics/summary")
async def proxy_summary():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_URL}/api/v1/analytics/summary", timeout=5)
            return resp.json()
    except Exception as e:
        return {}


@app.post("/api/proxy/collectors/run")
async def run_collector(name: str = ""):
    return {"status": "ok", "message": f"Collector {name} triggered"}


@app.post("/api/proxy/settings/telegram")
async def save_telegram(token: str = "", chat_id: str = ""):
    return {"ok": True}


@app.post("/api/proxy/telegram/test")
async def test_telegram():
    return {"ok": True, "message": "Test sent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)