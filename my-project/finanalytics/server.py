"""
FinAnalytics — API сервер + BI дашборд
Запуск: python server.py
"""
import os, sys, json, logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, send_from_directory

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'src'))
sys.path.insert(0, str(BASE.parent))

from dotenv import load_dotenv
load_dotenv(BASE / '.env')
from shared.net import force_ipv4
force_ipv4()

from db import FinDB

TASHKENT = timezone(timedelta(hours=5))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("finanalytics-api")

app = Flask(__name__, static_folder='dashboard', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('dashboard', 'index.html')

@app.route('/api/data')
def api_data():
    db = FinDB()
    budget = db.get_budget_report()
    debt = db.get_credit_summary()
    cal = db.get_payment_calendar()
    now = datetime.now(TASHKENT)
    return jsonify({
        'budget': budget,
        'debt': debt,
        'calendar': cal,
        'month': now.strftime('%B %Y'),
    })

@app.route('/api/debt')
def api_debt():
    db = FinDB()
    return jsonify(db.get_credit_summary())

@app.route('/api/budget')
def api_budget():
    db = FinDB()
    return jsonify(db.get_budget_report())

@app.route('/api/calendar')
def api_calendar():
    db = FinDB()
    return jsonify(db.get_payment_calendar())

@app.route('/api/analytics')
def api_analytics():
    """AI аналитика — тренды, рекомендации"""
    db = FinDB()
    budget = db.get_budget_report()
    debt = db.get_credit_summary()
    now = datetime.now(TASHKENT)

    # Тренды: сравнение с прошлым месяцем
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    prev = db.get_budget_report(month=last_month)

    insights = []
    diff = 0
    if prev and prev.get('expense_total', 0) > 0:
        diff = budget['expense_total'] - prev['expense_total']
        pct = (diff / prev['expense_total']) * 100
        if pct > 10:
            insights.append(f"🔴 Расходы выросли на {pct:.0f}% vs прошлый месяц")
        elif pct < -10:
            insights.append(f"🟢 Расходы снизились на {abs(pct):.0f}% vs прошлый месяц")
        else:
            insights.append(f"⚪ Расходы стабильны ({pct:+.0f}%)")

    # Критические категории
    for c in budget['categories']:
        if c['budget'] > 0 and c['fact'] > c['budget'] * 1.2:
            insights.append(f"🔴 {c['name']}: превышение бюджета на {((c['fact']/c['budget'])-1)*100:.0f}%")

    # Долговая нагрузка
    monthly_income = budget['income_total']
    if monthly_income > 0:
        dti = (debt['total_monthly'] / monthly_income) * 100
        if dti > 40:
            insights.append(f"🔴 Критическая долговая нагрузка: {dti:.0f}% от дохода")
        elif dti > 25:
            insights.append(f"🟡 Высокая долговая нагрузка: {dti:.0f}% от дохода")

    return jsonify({
        'month': now.strftime('%B %Y'),
        'insights': insights,
        'expense_trend': {
            'current': budget['expense_total'],
            'previous': prev.get('expense_total', 0) if prev else 0,
            'diff': diff if prev else 0,
        },
        'debt_metrics': {
            'total': debt['total_debt'],
            'monthly': debt['total_monthly'],
            'avg_rate': debt['avg_rate'],
            'count': debt['count'],
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('FINANALYTICS_PORT', 8090))
    logger.info(f"FinAnalytics API on :{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
