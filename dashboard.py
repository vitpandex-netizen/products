#!/usr/bin/env python3
"""
🌐 Hermes Project Dashboard — единый статус всех проектов
Запуск: python3 dashboard.py
Вывод: JSON со статусом всех проектов, сервисов, серверов
"""
import json, os, subprocess, sys, time
from datetime import datetime
from pathlib import Path

DEV = Path('/Volumes/External/dev')
OUTPUT = Path('/tmp/hermes-dashboard.json')

def check_service(name, pid_cmd=None, port=None, url=None):
    """Check if a service is running"""
    if pid_cmd:
        try:
            r = subprocess.run(pid_cmd, shell=True, capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                return {'status': 'running', 'pid': r.stdout.strip().split()[0]}
        except:
            pass
    if port:
        try:
            r = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return {'status': 'running', 'port': port}
        except:
            pass
    if url:
        try:
            import requests
            r = requests.get(url, timeout=5)
            if r.status_code < 500:
                return {'status': 'running', 'code': r.status_code}
        except:
            pass
    return {'status': 'stopped'}

def check_pm2():
    """Check PM2 services"""
    services = {}
    try:
        r = subprocess.run(['pm2', 'list'], capture_output=True, text=True, timeout=10)
        for line in r.stdout.split('\n'):
            if 'bitget' in line or 'meeting' in line or 'finanaly' in line or 'admin' in line:
                parts = line.split('│')
                if len(parts) >= 5:
                    name = parts[1].strip()
                    status = parts[5].strip()
                    services[name] = status
    except:
        pass
    return services

def check_servers():
    """Check all servers"""
    servers = {
        'mac': {'hostname': 'Mac M1', 'ip': '100.89.205.45'},
        'oracle': {'hostname': 'Oracle Cloud', 'ip': '100.94.224.89'},
        'us': {'hostname': 'US Server', 'ip': '100.84.223.96'},
    }
    for name, info in servers.items():
        try:
            ping = subprocess.run(['ping', '-c', '1', '-t', '2', info['ip']], 
                                capture_output=True, text=True, timeout=5)
            info['reachable'] = ping.returncode == 0
        except:
            info['reachable'] = False
    return servers

def check_git():
    """Check git status of all projects"""
    projects = {}
    for p in sorted(DEV.iterdir()):
        if p.is_dir() and not p.name.startswith('.') and (p / '.git').exists():
            try:
                r = subprocess.run(['git', '-C', str(p), 'status', '--porcelain'],
                                 capture_output=True, text=True, timeout=5)
                is_clean = r.stdout.strip() == ''
                projects[p.name] = 'clean' if is_clean else 'dirty'
            except:
                projects[p.name] = 'error'
    return projects

def main():
    dashboard = {
        'timestamp': datetime.now().isoformat(),
        'servers': check_servers(),
        'pm2': check_pm2(),
        'projects': check_git(),
        'bitget_bot': {},
    }
    
    # Bitget bot state
    state_file = DEV / 'bitget-bot' / 'config' / 'state_dca.json'
    if state_file.exists():
        try:
            dashboard['bitget_bot'] = json.loads(state_file.read_text())
        except:
            pass
    
    # Write output
    OUTPUT.write_text(json.dumps(dashboard, indent=2, default=str))
    print(f"✅ Dashboard saved to {OUTPUT}")
    print(f"   Servers: {sum(1 for s in dashboard['servers'].values() if s['reachable'])}/3 reachable")
    print(f"   PM2: {sum(1 for s in dashboard['pm2'].values() if s == 'online')} services online")
    print(f"   Git: {sum(1 for s in dashboard['projects'].values() if s == 'clean')}/{len(dashboard['projects'])} clean")

if __name__ == '__main__':
    main()