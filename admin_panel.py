#!/usr/bin/env python3
"""
🌐 Hermes Admin Panel — веб-дашборд для управления всеми проектами
Запуск: python3 admin_panel.py (порт 3030)
Доступ: http://localhost:3030 или http://100.89.205.45:3030
"""
import json, os, subprocess, sys, time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

DEV = Path('/Volumes/External/dev')
PORT = 3030

class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.render_html().encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.get_status()).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_status(self):
        status = {
            'timestamp': datetime.now().isoformat(),
            'pm2': {},
            'servers': {},
            'bitget': {},
            'hh_jobs': {},
        }
        
        # PM2 status
        try:
            r = subprocess.run(['pm2', 'list'], capture_output=True, text=True, timeout=10)
            for line in r.stdout.split('\n'):
                if '│' in line and ('bitget' in line or 'meeting' in line or 'finanaly' in line or 'hermes' in line or 'uz-market' in line or 'project' in line):
                    parts = [p.strip() for p in line.split('│') if p.strip()]
                    if len(parts) >= 5:
                        status['pm2'][parts[1]] = parts[4]
        except:
            pass
        
        # Bitget state
        state_file = DEV / 'bitget-bot' / 'config' / 'state_dca.json'
        if state_file.exists():
            try:
                status['bitget'] = json.loads(state_file.read_text())
            except:
                pass
        
        # HH Jobs stats
        hh_db = DEV / 'my-project' / 'hh-jobs' / 'data' / 'hh.db'
        if hh_db.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(hh_db))
                c = conn.execute('SELECT COUNT(*) FROM vacancies').fetchone()
                m = conn.execute('SELECT COUNT(*) FROM vacancies WHERE matched_score > 0').fetchone()
                status['hh_jobs'] = {'total': c[0], 'matched': m[0]}
                conn.close()
            except:
                pass
        
        return status
    
    def render_html(self):
        status = self.get_status()
        pm2_online = sum(1 for s in status['pm2'].values() if s == 'online')
        pm2_total = len(status['pm2'])
        
        bitget = status.get('bitget', {})
        entries = bitget.get('entry_prices', [])
        avg = sum(entries) / len(entries) if entries else 0
        invested = bitget.get('total_invested', 0)
        trades = bitget.get('total_trades', 0)
        profit = bitget.get('total_profit', 0)
        
        hh = status.get('hh_jobs', {})
        
        # PM2 rows
        pm2_rows = ''
        for name, state in sorted(status['pm2'].items()):
            icon = '🟢' if state == 'online' else '🔴' if state == 'waiting' else '⚪'
            pm2_rows += f'<tr><td>{icon}</td><td>{name}</td><td>{state}</td></tr>'
        
        return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hermes Admin Panel</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
h1 {{ font-size: 24px; margin-bottom: 20px; color: #58a6ff; }}
h2 {{ font-size: 18px; margin: 20px 0 10px; color: #8b949e; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }}
.card h3 {{ font-size: 14px; color: #8b949e; margin-bottom: 8px; }}
.card .value {{ font-size: 28px; font-weight: 600; color: #f0f6fc; }}
.card .value.up {{ color: #3fb950; }}
.card .value.down {{ color: #da3633; }}
table {{ width: 100%; border-collapse: collapse; background: #161b22; border: 1px solid #30363d; border-radius: 8px; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #30363d; font-size: 14px; }}
th {{ color: #8b949e; font-weight: 500; }}
.footer {{ margin-top: 20px; font-size: 12px; color: #484f58; text-align: center; }}
</style>
</head>
<body>
<h1>🛠️ Hermes Admin Panel</h1>

<div class="cards">
  <div class="card">
    <h3>PM2 Services</h3>
    <div class="value">{pm2_online}/{pm2_total}</div>
    <div style="font-size:12px;color:#8b949e">online</div>
  </div>
  <div class="card">
    <h3>Bitget Position</h3>
    <div class="value">{'$' + str(invested) if invested else '0'}</div>
    <div style="font-size:12px;color:#8b949e">{trades} trades | {avg:.2f} avg entry</div>
  </div>
  <div class="card">
    <h3>Bitget P&L</h3>
    <div class="value {'up' if profit >= 0 else 'down'}">${profit:.2f}</div>
    <div style="font-size:12px;color:#8b949e">total profit</div>
  </div>
  <div class="card">
    <h3>HH Jobs</h3>
    <div class="value">{hh.get('total', 0)}</div>
    <div style="font-size:12px;color:#8b949e">vacancies ({hh.get('matched', 0)} matched)</div>
  </div>
</div>

<h2>📊 PM2 Services</h2>
<table>
<tr><th></th><th>Name</th><th>Status</th></tr>
{pm2_rows}
</table>

<div class="footer">
  Hermes Admin Panel v0.1 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
</body>
</html>'''

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), AdminHandler)
    print(f"✅ Admin Panel: http://localhost:{PORT}")
    print(f"   Mobile: http://100.89.205.45:{PORT}")
    print(f"   US Server: http://100.84.223.96:{PORT}")
    server.serve_forever()