#!/usr/bin/env python3
"""
BGT Monitor — непрерывный мониторинг и самопроверка всех стратегий.
Запускается каждые 5 минут через cron или напрямую.
"""
import subprocess
import requests
import json
import datetime
import time
import csv
import os

# ─── КОНФИГ ────────────────────────────────────────────────────────────────
FREQTRADE_BOTS = [
    {"name": "UltraScalper",  "url": "http://localhost:8096", "auth": ("admin", "bgt_password123")},
    {"name": "EMA_Cross",     "url": "http://localhost:8091", "auth": ("admin", "bgt_password123")},
    {"name": "RSI_Bollinger", "url": "http://localhost:8092", "auth": ("admin", "bgt_password123")},
]
HB_API = "http://localhost:8000"
HB_AUTH = ("admin", "admin")
METRICS_FILE = os.path.expanduser("~/bgt_metrics.csv")
LOG_FILE = os.path.expanduser("~/bgt_monitor.log")
TIMEOUT = 5

# ─── ЛОГИРОВАНИЕ ─────────────────────────────────────────────────────────────
def log(msg, level="INFO"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ─── ПРОВЕРКИ ─────────────────────────────────────────────────────────────────
def check_docker_containers():
    """Проверяем что все нужные контейнеры запущены."""
    expected = [
        "freqtrade-bgt", "freqtrade-ema-bgt", "freqtrade-rsi-bgt",
        "hummingbot-bgt", "hummingbot-backend-api-bgt",
        "hummingbot-dashboard-bgt", "hummingbot-emqx-bgt"
    ]
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
        capture_output=True, text=True
    )
    running = {}
    for line in result.stdout.strip().split("\n"):
        if "\t" in line:
            name, status = line.split("\t", 1)
            running[name.strip()] = status.strip()
    
    issues = []
    for c in expected:
        if c not in running:
            issues.append(f"❌ КОНТЕЙНЕР НЕ ЗАПУЩЕН: {c}")
            log(f"CONTAINER DOWN: {c}", "ERROR")
        else:
            log(f"✅ {c}: {running[c]}")
    return issues

def check_freqtrade_bots():
    """Проверяем состояние всех Freqtrade ботов и собираем метрики."""
    results = []
    for bot in FREQTRADE_BOTS:
        try:
            r = requests.get(f"{bot['url']}/api/v1/show_config",
                             auth=bot["auth"], timeout=TIMEOUT)
            if r.status_code == 200:
                cfg = r.json()
                strategy = cfg.get("strategy", "?")
                # Получаем баланс
                b = requests.get(f"{bot['url']}/api/v1/balance",
                                 auth=bot["auth"], timeout=TIMEOUT)
                bal = 0
                if b.status_code == 200:
                    currencies = b.json().get("currencies", [])
                    for c in currencies:
                        if c.get("currency") == "USDT" and not c.get("is_position"):
                            bal = c.get("balance", 0)
                # Получаем открытые сделки
                tr = requests.get(f"{bot['url']}/api/v1/trades",
                                  auth=bot["auth"], timeout=TIMEOUT)
                open_trades = 0
                total_profit = 0
                if tr.status_code == 200:
                    td = tr.json()
                    open_trades = td.get("trades_count", 0)
                    for t in td.get("trades", []):
                        total_profit += t.get("profit_abs", 0)
                
                log(f"✅ Freqtrade [{bot['name']}] strategy={strategy} balance={bal:.2f} USDT trades={open_trades} profit={total_profit:.4f}")
                results.append({
                    "ts": datetime.datetime.now().isoformat(),
                    "platform": "freqtrade",
                    "strategy": bot["name"],
                    "balance": bal,
                    "open_trades": open_trades,
                    "total_profit": total_profit,
                    "status": "OK"
                })
            else:
                log(f"⚠️ Freqtrade [{bot['name']}] HTTP {r.status_code}", "WARN")
                results.append({"ts": datetime.datetime.now().isoformat(), "platform": "freqtrade", "strategy": bot["name"], "status": f"HTTP_{r.status_code}"})
        except Exception as e:
            log(f"❌ Freqtrade [{bot['name']}] недоступен: {e}", "ERROR")
            results.append({"ts": datetime.datetime.now().isoformat(), "platform": "freqtrade", "strategy": bot["name"], "status": f"ERROR: {e}"})
    return results

def check_hummingbot():
    """Проверяем Hummingbot backend и все боты."""
    results = []
    try:
        r = requests.get(f"{HB_API}/is-docker-running", auth=HB_AUTH, timeout=TIMEOUT)
        if r.status_code == 200:
            log(f"✅ Hummingbot Backend API: docker running = {r.json()}")
        # Получаем статусы всех ботов
        ac = requests.get(f"{HB_API}/active-containers", auth=HB_AUTH, timeout=TIMEOUT)
        if ac.status_code == 200:
            bots = ac.json().get("active_instances", [])
            log(f"✅ Hummingbot активных контейнеров: {len(bots)}")
            for b in bots:
                log(f"   → {b['name']}: {b['status']}")
                results.append({"ts": datetime.datetime.now().isoformat(), "platform": "hummingbot", "strategy": b["name"], "status": b["status"]})
        # Получаем accounts state
        ast = requests.get(f"{HB_API}/accounts-state", auth=HB_AUTH, timeout=TIMEOUT)
        if ast.status_code == 200:
            accounts = ast.json()
            log(f"✅ Hummingbot accounts state: {json.dumps(accounts)[:200]}")
    except Exception as e:
        log(f"❌ Hummingbot API недоступен: {e}", "ERROR")
    return results

def save_metrics(all_results):
    """Сохраняем метрики в CSV."""
    fieldnames = ["ts", "platform", "strategy", "balance", "open_trades", "total_profit", "status"]
    file_exists = os.path.exists(METRICS_FILE)
    with open(METRICS_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        for row in all_results:
            writer.writerow(row)
    log(f"📊 Метрики сохранены в {METRICS_FILE} ({len(all_results)} записей)")

def analyze_and_suggest(all_results):
    """Анализируем результаты и предлагаем улучшения."""
    log("─── АНАЛИЗ И РЕКОМЕНДАЦИИ ──────────────────────────────")
    freqtrade_results = [r for r in all_results if r.get("platform") == "freqtrade" and r.get("total_profit") is not None]
    if freqtrade_results:
        best = max(freqtrade_results, key=lambda x: x.get("total_profit", 0))
        worst = min(freqtrade_results, key=lambda x: x.get("total_profit", 0))
        log(f"🏆 Лучшая стратегия: {best['strategy']} (profit={best.get('total_profit', 0):.4f} USDT)")
        log(f"⚠️  Худшая стратегия: {worst['strategy']} (profit={worst.get('total_profit', 0):.4f} USDT)")
        if worst.get("open_trades", 0) == 0:
            log(f"💡 ПРЕДЛОЖЕНИЕ: {worst['strategy']} не имеет открытых сделок — проверьте pairlist или параметры стратегии")

# ─── ГЛАВНАЯ ФУНКЦИЯ ──────────────────────────────────────────────────────────
def run_monitor():
    log("═══════════════════════════════════════════════════════")
    log("🚀 BGT MONITOR ЗАПУЩЕН")
    log("═══════════════════════════════════════════════════════")
    
    all_results = []
    
    log("── 1. Проверка Docker контейнеров ──")
    issues = check_docker_containers()
    if issues:
        for issue in issues:
            log(issue, "CRITICAL")
    
    log("── 2. Проверка Freqtrade ботов ──")
    ft_results = check_freqtrade_bots()
    all_results.extend(ft_results)
    
    log("── 3. Проверка Hummingbot ──")
    hb_results = check_hummingbot()
    all_results.extend(hb_results)
    
    log("── 4. Сохранение метрик ──")
    save_metrics(all_results)
    
    log("── 5. Анализ и рекомендации ──")
    analyze_and_suggest(all_results)
    
    log("✅ Мониторинг завершён\n")

if __name__ == "__main__":
    run_monitor()
