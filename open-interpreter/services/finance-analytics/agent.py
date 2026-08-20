"""Financial analytics agent - tracks expenses, generates reports, finds passive income."""
import sys
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.db import get_conn
from shared.utils import notify, send_hermes_message, get_config, set_config

REPORT_DIR = Path(__file__).parent.parent.parent / "data" / "reports"

class FinanceAgent:
    def __init__(self):
        self.conn = get_conn()
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    def add_transaction(self, date, description, amount, category, account="cash"):
        """Record a transaction."""
        self.conn.execute(
            "INSERT INTO transactions (date, description, amount, category, account) VALUES (?, ?, ?, ?, ?)",
            (date, description, amount, category, account)
        )
        self.conn.commit()
        return True
    
    def import_csv(self, csv_path):
        """Import transactions from a CSV file."""
        imported = 0
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.add_transaction(
                    row.get("date", datetime.now().strftime("%Y-%m-%d")),
                    row.get("description", "Import"),
                    float(row.get("amount", 0)),
                    row.get("category", "other"),
                    row.get("account", "cash")
                )
                imported += 1
        return imported
    
    def monthly_report(self, year, month):
        """Generate a monthly financial report."""
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year+1}-01-01"
        else:
            end = f"{year}-{month+1:02d}-01"
        
        rows = self.conn.execute("""
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM transactions
            WHERE date >= ? AND date < ?
            GROUP BY category
            ORDER BY total DESC
        """, (start, end)).fetchall()
        
        total_income = sum(r["total"] for r in rows if r["total"] > 0)
        total_expenses = sum(r["total"] for r in rows if r["total"] < 0)
        
        report = {
            "period": f"{year}-{month:02d}",
            "income": total_income,
            "expenses": abs(total_expenses),
            "net": total_income + total_expenses,
            "categories": [dict(r) for r in rows],
            "top_expense_categories": sorted(
                [dict(r) for r in rows if r["total"] < 0],
                key=lambda x: x["total"]
            )[:5]
        }
        
        # Save report
        report_file = REPORT_DIR / f"report_{year}_{month:02d}.json"
        report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        
        return report
    
    def analyze_passive_income_opportunities(self):
        """Analyze and suggest passive income ideas based on current finances."""
        # Get last 6 months of data
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        monthly_spend = self.conn.execute("""
            SELECT strftime('%Y-%m', date) as month,
                   SUM(CASE WHEN amount < 0 THEN abs(amount) ELSE 0 END) as total_spend
            FROM transactions
            WHERE date >= ?
            GROUP BY month
            ORDER BY month DESC
        """, (six_months_ago,)).fetchall()
        
        avg_monthly = sum(r["total_spend"] for r in monthly_spend) / max(len(monthly_spend), 1)
        
        suggestions = []
        
        # Suggestion based on available capital
        if avg_monthly > 0:
            safety_buffer = avg_monthly * 6
            suggestions.append({
                "type": "safety",
                "priority": "high",
                "description": f"Финансовая подушка безопасности: {safety_buffer:,.0f} сум ({int(avg_monthly)}× месячных расходов)",
                "detail": "Рекомендуется держать 3-6 месяцев расходов в ликвидной форме"
            })
        
        suggestions.extend([
            {
                "type": "deposit",
                "priority": "low",
                "description": "Депозиты в UZS (20-24% годовых)",
                "detail": "Низкий риск, стабильный доход — банки Узбекистана"
            },
            {
                "type": "bonds",
                "priority": "medium",
                "description": "Гособлигации США (T-bills, ~4-5% годовых)",
                "detail": "Надежная инвестиция в долларах"
            },
            {
                "type": "dividend_stocks",
                "priority": "medium",
                "description": "Дивидендные акции US рынка",
                "detail": "SCHD, VYM, JEPI — ETF с фокусом на дивиденды"
            },
            {
                "type": "real_estate",
                "priority": "low",
                "description": "REIT — недвижимость через ETF",
                "detail": "VNQ, O, STAG — без прямого владения"
            },
            {
                "type": "dollar_cost_average",
                "priority": "high",
                "description": "DCA в SPY/QQQ каждый месяц",
                "detail": "Средняя доходность ~10% годовых исторически"
            }
        ])
        
        return {"avg_monthly_spend": avg_monthly, "suggestions": suggestions}
    
    def run_weekly(self):
        """Weekly financial digest."""
        now = datetime.now()
        report = self.monthly_report(now.year, now.month)
        
        msg = f"💰 *Финансовый дайджест*\n\n"
        msg += f"Текущий месяц: {report['period']}\n"
        msg += f"Доходы: {report['income']:,.0f}\n"
        msg += f"Расходы: {report['expenses']:,.0f}\n"
        msg += f"Баланс: {report['net']:+,.0f}\n\n"
        
        if report['top_expense_categories']:
            msg += "Топ-3 расходов:\n"
            for c in report['top_expense_categories'][:3]:
                msg += f"  • {c['category']}: {abs(c['total']):,.0f}\n"
        
        send_hermes_message(msg)
        
        # Also generate passive income suggestions monthly
        pi = self.analyze_passive_income_opportunities()
        report["passive_income"] = pi
        (REPORT_DIR / f"passive_income_{now.strftime('%Y_%m')}.json").write_text(
            json.dumps(pi, indent=2, ensure_ascii=False))
        
        return report

if __name__ == "__main__":
    agent = FinanceAgent()
    
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "weekly":
            report = agent.run_weekly()
            print(f"Weekly report generated: income={report['income']}, expenses={report['expenses']}")
        elif cmd == "report":
            year = int(sys.argv[2]) if len(sys.argv) > 2 else datetime.now().year
            month = int(sys.argv[3]) if len(sys.argv) > 3 else datetime.now().month
            report = agent.monthly_report(year, month)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif cmd == "passive":
            pi = agent.analyze_passive_income_opportunities()
            print(json.dumps(pi, indent=2, ensure_ascii=False))
    else:
        print("Usage: python3 agent.py [weekly|report|passive]")
