"""
Architecture Diagram Generator.
Вдохновлено diagram-design ⭐14K — 38 editorial diagram types for Claude Code.
Генерирует SVG-диаграммы архитектуры наших проектов для дашбордов и документации.

Использование:
  python3 arch_diagram.py gh-scout    # диаграмма GH Scout
  python3 arch_diagram.py bitget      # диаграмма Bitget бота
  python3 arch_diagram.py all         # все проекты
"""

import json
import os
import sys
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "diagrams")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def svg_style() -> str:
    return """<style>
  .title { font-family: -apple-system, system-ui, sans-serif; font-size: 18px; font-weight: 700; fill: #e2e8f0; }
  .subtitle { font-family: -apple-system, system-ui, sans-serif; font-size: 12px; fill: #94a3b8; }
  .box { fill: #1e293b; stroke: #334155; stroke-width: 1.5; rx: 6; }
  .box:hover { stroke: #3b82f6; }
  .box-label { font-family: -apple-system, system-ui, sans-serif; font-size: 11px; fill: #e2e8f0; text-anchor: middle; }
  .box-sub { font-family: -apple-system, system-ui, sans-serif; font-size: 9px; fill: #94a3b8; text-anchor: middle; }
  .arrow { stroke: #475569; stroke-width: 1.5; fill: none; marker-end: url(#arrowhead); }
  .arrow:hover { stroke: #3b82f6; }
  .badge { fill: #3b82f6; rx: 3; }
  .badge-text { font-family: -apple-system, system-ui, sans-serif; font-size: 8px; fill: #fff; text-anchor: middle; }
  .bg { fill: #0f172a; }
</style>"""


def svg_defs() -> str:
    return """<defs>
  <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#475569" />
  </marker>
  <marker id="arrow-blue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#3b82f6" />
  </marker>
  <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#1e293b;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1" />
  </linearGradient>
</defs>"""


def draw_box(svg: list, x: int, y: int, w: int, h: int, title: str, sub: str = "", badge: str = ""):
    """Draw a service box."""
    svg.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" class="box" />')
    if badge:
        bw = len(badge) * 7 + 10
        svg.append(f'  <rect x="{x + w - bw - 6}" y="{y + 4}" width="{bw}" height="{14}" class="badge" />')
        svg.append(f'  <text x="{x + w - bw/2 - 6}" y="{y + 14}" class="badge-text">{badge}</text>')
    svg.append(f'  <text x="{x + w/2}" y="{y + h/2 - 4}" class="box-label">{title}</text>')
    if sub:
        svg.append(f'  <text x="{x + w/2}" y="{y + h/2 + 12}" class="box-sub">{sub}</text>')


def draw_arrow(svg: list, x1: int, y1: int, x2: int, y2: int, label: str = "", cls: str = "arrow"):
    """Draw an arrow between boxes."""
    svg.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" />')
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 8
        svg.append(f'  <text x="{mx}" y="{my}" class="box-sub">{label}</text>')


# ─── Architecture definitions ───

ARCHITECTURES = {
    "gh-scout": {
        "title": "GH Scout — GitHub Project Monitor",
        "width": 700,
        "height": 420,
        "boxes": [
            # (x, y, w, h, title, sub, badge)
            (50, 40, 140, 50, "GitHub Collector", "releases + trends", "P0"),
            (250, 40, 140, 50, "Feature Extractor", "release parsing", "AI"),
            (450, 40, 140, 50, "Recommender", "→ bitget, anyidea", "AI"),
            (50, 140, 140, 50, "Trend Scanner", "GitHub trending", "P0"),
            (250, 140, 140, 50, "API Core", "FastAPI + REST", "8005"),
            (450, 140, 140, 50, "Telegram Bot", "@ghscout_bot", "TG"),
            (150, 260, 180, 50, "PostgreSQL", "projects + recs", "DB"),
            (380, 260, 180, 50, "Redis", "event bus + cache", "DB"),
            (100, 350, 120, 40, "Git Sync", "cron 3h", ""),
            (280, 350, 120, 40, "Auto-Improver", "cron 10:00", "AI"),
            (460, 350, 120, 40, "Digest", "cron 11:00", "TG"),
        ],
        "arrows": [
            (120, 90, 120, 140, ""),
            (250, 90, 250, 140, "releases"),
            (320, 90, 320, 140, "features"),
            (520, 90, 520, 140, "recs"),
            (120, 190, 150, 260, "store"),
            (320, 190, 380, 260, "pub/sub"),
            (240, 310, 160, 350, "sync"),
            (320, 310, 340, 350, "improve"),
            (520, 310, 520, 350, "send"),
        ],
    },
    "bitget": {
        "title": "Bitget Bot — Trading Platform",
        "width": 750,
        "height": 450,
        "boxes": [
            (50, 40, 150, 50, "WebSocket", "real-time price", "LIVE"),
            (250, 40, 150, 50, "API Client", "HMAC + retry", "CORE"),
            (450, 40, 150, 50, "Strategy Mgr", "6 strategies", "AI"),
            (50, 130, 150, 50, "Market Analyzer", "regime detection", "AI"),
            (250, 130, 150, 50, "Order Executor", "Bitget API v3", ""),
            (450, 130, 150, 50, "Risk Manager", "trailing stop", ""),
            (50, 220, 150, 50, "Webhook Server", "external signals", "8123"),
            (250, 220, 150, 50, "PnL Tracker", "per-strategy", "NEW"),
            (450, 220, 150, 50, "Morning Briefing", "AI voice", "NEW"),
            (150, 320, 180, 50, "PostgreSQL", "trades + events", "DB"),
            (380, 320, 180, 50, "Redis", "event bus", "DB"),
            (150, 400, 180, 40, "Telegram Bot", "notifications", "TG"),
            (380, 400, 180, 40, "Dashboard", ":3004", "UI"),
        ],
        "arrows": [
            (125, 90, 125, 130, "price"),
            (325, 90, 325, 130, "orders"),
            (525, 90, 525, 130, "signals"),
            (125, 180, 125, 220, "analysis"),
            (325, 180, 325, 220, "execute"),
            (525, 180, 525, 220, "protect"),
            (125, 270, 150, 320, "store"),
            (325, 270, 380, 320, "events"),
            (240, 370, 240, 400, "alerts"),
            (420, 370, 420, 400, "stats"),
            (525, 270, 525, 400, "briefing"),
        ],
    },
    "anyidea": {
        "title": "AnyIdea — Idea Collection & Analysis",
        "width": 700,
        "height": 420,
        "boxes": [
            (50, 40, 140, 50, "Scout Engine", "sources + cron", "P0"),
            (250, 40, 140, 50, "Web Search", "DuckDuckGo", "NEW"),
            (450, 40, 140, 50, "RSS Sources", "PH + HN + Reddit", ""),
            (50, 130, 140, 50, "AI Analyzer", "market + risks", "AI"),
            (250, 130, 140, 50, "Knowledge Graph", "idea connections", "NEW"),
            (450, 130, 140, 50, "Idea Tracker", "UUID + traces", "NEW"),
            (150, 240, 180, 50, "PostgreSQL", "ideas + logs", "DB"),
            (380, 240, 180, 50, "Redis", "event bus", "DB"),
            (100, 330, 140, 50, "Telegram Bot", "@anyidea_ai_bot", "TG"),
            (280, 330, 140, 50, "API Core", "FastAPI :8002", ""),
            (460, 330, 140, 50, "DataCore Bus", "ghscout:*", ""),
        ],
        "arrows": [
            (120, 90, 120, 130, "ideas"),
            (320, 90, 320, 130, "search"),
            (520, 90, 520, 130, "sources"),
            (120, 180, 150, 240, "store"),
            (320, 180, 380, 240, "graph"),
            (520, 180, 520, 240, "traces"),
            (240, 290, 170, 330, "bot"),
            (320, 290, 350, 330, "api"),
            (520, 290, 520, 330, "bus"),
        ],
    },
}


def generate_svg(name: str, arch: dict) -> str:
    """Generate SVG diagram for an architecture."""
    w, h = arch["width"], arch["height"]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%">',
        svg_style(),
        svg_defs(),
        f'<rect width="{w}" height="{h}" class="bg" />',
        f'<text x="20" y="24" class="title">{arch["title"]}</text>',
        f'<text x="20" y="36" class="subtitle">Generated {datetime.now().strftime("%d %b %Y")} · diagram-design inspired</text>',
    ]

    for box in arch["boxes"]:
        draw_box(svg, *box)

    for arrow in arch["arrows"]:
        draw_arrow(svg, *arrow)

    # Legend
    legend_y = h - 20
    svg.append(f'<rect x="20" y="{legend_y - 4}" width="10" height="10" class="badge" />')
    svg.append(f'<text x="36" y="{legend_y + 5}" class="box-sub" style="fill:#94a3b8">P0 · AI · NEW · LIVE · DB · TG · UI</text>')

    svg.append("</svg>")
    return "\n".join(svg)


def generate_html(name: str, arch: dict) -> str:
    """Generate an HTML page with the SVG diagram embedded."""
    svg_content = generate_svg(name, arch)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{arch['title']}</title>
<style>
  body {{ margin: 0; padding: 20px; background: #0f172a; display: flex; justify-content: center; }}
  svg {{ max-width: 100%; height: auto; border: 1px solid #1e293b; border-radius: 8px; }}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["all"]

    for name, arch in ARCHITECTURES.items():
        if "all" in targets or name in targets:
            html = generate_html(name, arch)
            path = os.path.join(OUTPUT_DIR, f"{name}.html")
            with open(path, "w") as f:
                f.write(html)
            print(f"✅ {name} — {path}")

    # Generate index
    if "all" in targets:
        index = [
            "<html><head><title>Architecture Diagrams</title>",
            '<style>body{background:#0f172a;color:#e2e8f0;font-family:system-ui;padding:40px}a{color:#3b82f6;text-decoration:none}</style>',
            "</head><body>",
            "<h1>🏗 Architecture Diagrams</h1>",
            "<p>Generated by GH Scout · diagram-design inspired</p>",
            "<ul>",
        ]
        for name, arch in ARCHITECTURES.items():
            index.append(f'<li><a href="{name}.html">{arch["title"]}</a></li>')
        index.append("</ul></body></html>")
        with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
            f.write("\n".join(index))
        print(f"✅ index — {os.path.join(OUTPUT_DIR, 'index.html')}")


if __name__ == "__main__":
    main()