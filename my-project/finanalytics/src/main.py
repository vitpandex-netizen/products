"""FinAnalytics — точка входа. --bot (поллинг), --import, --report, --serve"""
import sys, os, logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent.parent
os.chdir(str(BASE))
sys.path.insert(0, str(BASE / 'src'))
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent))

from dotenv import load_dotenv
load_dotenv(BASE / '.env')
from shared.net import force_ipv4
from shared.vault import get as vault_get
force_ipv4()

TASHKENT = timezone(timedelta(hours=5))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("finanalytics")

def get_token():
    return vault_get('FINANALYTICS_BOT_TOKEN') or os.getenv('FINANALYTICS_BOT_TOKEN', '')

def get_chat_id():
    return vault_get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '-1004297012607')

def get_thread_id():
    return vault_get('TELEGRAM_THREAD_ID') or os.getenv('TELEGRAM_THREAD_ID', '116')

def cmd_bot():
    from bot import FinBot
    FinBot(get_token(), get_chat_id(), get_thread_id()).start()

def cmd_import():
    from db import FinDB
    db = FinDB()
    db.import_credit_data()
    s = db.get_credit_summary()
    print(f"Imported: {s['count']} credits, {s['total_monthly']:,.0f} sum/month")
    # Save report
    from bot import FinBot
    bot = FinBot(get_token(), get_chat_id(), get_thread_id())
    bot.send_report(f"📊 FinAnalytics — импорт завершён\n{s['count']} кредитов, {s['total_monthly']:,.0f} сум/мес")

def cmd_report():
    from db import FinDB
    from bot import FinBot
    db = FinDB()
    bot = FinBot(get_token(), get_chat_id(), get_thread_id())
    debt = db.get_credit_summary()
    budget = db.get_budget_report()
    text = (
        f"📊 <b>FinAnalytics — {budget['month']}</b>\n\n"
        f"💰 Долги: {debt['count']} кредитов | {debt['total_monthly']:,.0f} сум/мес\n"
        f"📈 Доходы: {budget['income_total']:,.0f} | Расходы: {budget['expense_total']:,.0f}\n"
        f"📅 Общий долг: {debt['total_debt']:,.0f} сум\n"
        f"⚡ Баланс: {budget['balance']:+,.0f} сум"
    )
    bot.send_report(text)

def cmd_serve():
    """Запуск веб-сервера для Mini App (дашборд)."""
    import http.server, socketserver, json
    from db import FinDB

    PORT = 8080
    dashboard_dir = BASE / "dashboard"

    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/api/data':
                db = FinDB()
                debt = db.get_credit_summary()
                budget = db.get_budget_report()
                cal = db.get_payment_calendar()
                data = {
                    'debt': debt,
                    'budget': budget,
                    'calendar': cal,
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())
                return
            return super().do_GET()

        def log_message(self, format, *args):
            logger.info(f"Dashboard: {args[0]} {args[1]} {args[2]}")

    os.chdir(str(dashboard_dir))
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        logger.info(f"Dashboard server at http://0.0.0.0:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py --bot | --import | --report | --serve")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == '--bot': cmd_bot()
    elif cmd == '--import': cmd_import()
    elif cmd == '--report': cmd_report()
    elif cmd == '--serve': cmd_serve()
    else: print(f"Unknown: {cmd}")
