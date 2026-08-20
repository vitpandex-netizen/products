#!/usr/bin/env python3
"""Remote DevOps Consulting — business plan prototype."""
import os, sys, logging
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from telegram import Telegram

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

SERVICES = [
    {"name": "Infrastructure Audit", "price": 500, "hours": 8, "desc": "Audit of existing infra (VMware, Proxmox, K8s)"},
    {"name": "Zero Trust Setup", "price": 1500, "hours": 24, "desc": "Zero Trust architecture implementation"},
    {"name": "CI/CD Pipeline", "price": 2000, "hours": 32, "desc": "GitLab/GitHub Actions CI/CD pipeline"},
    {"name": "Monitoring Stack", "price": 1000, "hours": 16, "desc": "Prometheus + Grafana + Alertmanager"},
    {"name": "Monthly Retainer", "price": 2500, "hours": 20, "desc": "Monthly support (20h)"},
    {"name": "K8s Migration", "price": 3000, "hours": 40, "desc": "On-prem to Kubernetes migration"},
]

def calculate(clients=2, avg_ticket=1500):
    monthly = clients * avg_ticket
    yearly = monthly * 12
    tax = yearly * 0.12
    net = yearly - tax
    return {"monthly_gross": monthly, "yearly_gross": yearly, "tax": tax,
            "yearly_net": net, "monthly_net": round(net/12, 2), "per_hour": round(avg_ticket/20, 2)}

def format_report():
    lines = [f"<b>Remote DevOps Consulting - Business Plan</b>",
             f"{datetime.now(TASHKENT).strftime('%d.%m.%Y %H:%M')}",
             chr(10) + "<b>Services:</b>"]
    for s in SERVICES:
        lines.append(f"  ${s['price']} - {s['name']} ({s['hours']}h)")
        lines.append(f"    {s['desc']}")
    lines.append(chr(10) + "<b>Financial model (Uzbekistan, 12% tax):</b>")
    for name, clients, ticket in [("Conservative", 1, 1500), ("Medium", 2, 2000), ("Active", 3, 2500)]:
        f = calculate(clients, ticket)
        lines.append(f"  {name}: {clients} client/mo x ${ticket}")
        lines.append(f"    Monthly: ${f['monthly_gross']} gross -> ${f['monthly_net']} net")
        lines.append(f"    Yearly: ${f['yearly_gross']} gross -> ${f['yearly_net']} net")
    lines.append(chr(10) + "<b>Platforms:</b> Upwork, Toptal, LinkedIn, Remote OK, We Work Remotely")
    lines.append(chr(10) + "Start with zero investment. Only need laptop + internet.")
    return chr(10).join(lines)

if __name__ == "__main__":
    report = format_report()
    print(report)
    t = Telegram()
    t.send(report)
