"""Main orchestrator - runs all services on schedule. Single process, low memory."""
import sys
import time
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.db import get_conn
from shared.utils import notify, get_config, set_config, send_hermes_message

SERVICES_DIR = Path(__file__).parent.parent / "services"

SCHEDULE = {
    "hh-monitor": {"interval": 1800, "module": "hh-monitor/monitor.py"},     # 30 min
    "us-stocks": {"interval": 3600, "module": "us-stocks/monitor.py"},       # 1 hour
    "uz-stocks": {"interval": 7200, "module": "uz-stocks/monitor.py"},       # 2 hours
    "events-monitor": {"interval": 43200, "module": "events-monitor/monitor.py"}, # 12 hours
    "finance-analytics": {"interval": 86400, "module": "finance-analytics/agent.py weekly"},  # daily
    "education-center": {"interval": 86400, "module": None},                 # daily (TBD)
    "passive-income": {"interval": 86400, "module": None},                   # daily (TBD)
    "confidential-projects": {"interval": 3600, "module": None},             # hourly (TBD)
}

def check_ollama():
    """Verify Ollama is running."""
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = r.json().get("models", [])
        has_model = any(m["name"].startswith("qwen3.5:4b") for m in models)
        if not has_model:
            print("[ORCH] Pulling qwen3.5:4b...")
            os.system("ollama pull qwen3.5:4b")
        return True
    except:
        print("[ORCH] Warning: Ollama not available")
        return False

def check_hermes():
    """Verify Hermes gateway is running."""
    import requests
    try:
        r = requests.get("http://localhost:20128", timeout=3)
        return r.status_code in (200, 404)  # 404 means gateway is up
    except:
        print("[ORCH] Warning: Hermes gateway not available")
        return False

def run_service(name, config):
    """Run a single service script."""
    module = config.get("module")
    if not module:
        return {"status": "skipped", "reason": "no module defined"}
    
    full_path = SERVICES_DIR / module
    if not full_path.exists():
        return {"status": "error", "reason": f"module not found: {full_path}"}
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running {name}...")
    start = time.time()
    
    try:
        result = subprocess.run(
            ["python3", str(full_path)],
            capture_output=True, text=True, timeout=120
        )
        elapsed = time.time() - start
        print(f"[{name}] Finished in {elapsed:.1f}s, exit={result.returncode}")
        
        if result.returncode != 0:
            print(f"[{name}] STDOUT: {result.stdout[-500:]}")
            print(f"[{name}] STDERR: {result.stderr[-500:]}")
            return {"status": "error", "output": result.stdout[-200:], "error": result.stderr[-200:]}
        
        return {"status": "ok", "elapsed": elapsed, "output": result.stdout[-200:]}
    except subprocess.TimeoutExpired:
        print(f"[{name}] Timeout after 120s")
        return {"status": "timeout"}
    except Exception as e:
        print(f"[{name}] Exception: {e}")
        return {"status": "error", "reason": str(e)}

def run_cycle():
    """Run all services in sequence (single cycle)."""
    print(f"\n{'='*50}")
    print(f"ORCHESTRATOR CYCLE — {datetime.now().isoformat()}")
    print(f"{'='*50}")
    
    # Check dependencies
    ollama_ok = check_ollama()
    hermes_ok = check_hermes()
    print(f"Deps: Ollama={'✅' if ollama_ok else '❌'} Hermes={'✅' if hermes_ok else '❌'}")
    
    if not hermes_ok:
        # Try to start Hermes
        subprocess.Popen(["python3", "-m", "hermes_cli.main", "gateway", "run"],
                        cwd=str(Path.home() / ".hermes" / "hermes-agent"),
                        start_new_session=True)
    
    conn = get_conn()
    results = {}
    
    for name, cfg in SCHEDULE.items():
        # Check last run time
        last_run = conn.execute(
            "SELECT created_at FROM notifications WHERE service=? ORDER BY id DESC LIMIT 1",
            (name,)
        ).fetchone()
        
        should_run = True
        if last_run:
            last_time = datetime.fromisoformat(last_run["created_at"])
            elapsed = (datetime.now() - last_time).total_seconds()
            should_run = elapsed >= cfg["interval"]
        
        if should_run:
            result = run_service(name, cfg)
            results[name] = result
            
            if result.get("status") == "ok":
                notify(name, f"Cycle completed in {result.get('elapsed', 0):.1f}s", "", "info")
        else:
            print(f"[{name}] Skipped (ran {elapsed:.0f}s ago, interval={cfg['interval']}s)")
    
    conn.close()
    
    print(f"\nCycle summary:")
    for k, v in results.items():
        status_icon = {"ok": "✅", "error": "❌", "timeout": "⏰", "skipped": "⏭️"}.get(v.get("status"), "❓")
        print(f"  {status_icon} {k}: {v.get('status')}")
    
    return results

def run_loop():
    """Run forever with checking all services."""
    print("[ORCH] Starting 24/7 orchestrator loop")
    print(f"[ORCH] Hermes PID check: {'ok' if check_hermes() else 'not found'}")
    print(f"[ORCH] Ollama check: {'ok' if check_ollama() else 'not found'}")
    print(f"[ORCH] Starting first cycle...")
    
    run_cycle()
    
    while True:
        try:
            # Check every 5 minutes
            time.sleep(300)
            
            conn = get_conn()
            for name, cfg in SCHEDULE.items():
                last_run = conn.execute(
                    "SELECT created_at FROM notifications WHERE service=? ORDER BY id DESC LIMIT 1",
                    (name,)
                ).fetchone()
                
                should_run = True
                if last_run:
                    elapsed = (datetime.now() - datetime.fromisoformat(last_run["created_at"])).total_seconds()
                    should_run = elapsed >= cfg["interval"]
                
                if should_run:
                    run_service(name, cfg)
                    notify(name, f"Service cycle", "", "info")
            
            conn.close()
        except KeyboardInterrupt:
            print("[ORCH] Shutting down...")
            break
        except Exception as e:
            print(f"[ORCH] Error in loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    check_ollama()
    check_hermes()
    
    import sys
    if "--loop" in sys.argv:
        run_loop()
    else:
        run_cycle()
