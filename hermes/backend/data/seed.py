"""
Сид-данные HERMES из ТЗ (Приложение A).
Загружаются при первом запуске /api/seed.
"""
from models import (Instrument, Position, PricePoint, Target, 
                    Catalyst, Bond, now)

def seed_all(db):
    # === Инструменты ===
    instruments = [
        Instrument(ticker="SQBN", name="Узпромстройбанк", type="equity", sector="banking"),
        Instrument(ticker="HMKB", name="Хамкорбанк", type="equity", sector="banking"),
        Instrument(ticker="UZTL", name="Узбектелеком", type="equity", sector="telecom"),
        Instrument(ticker="CBSK", name="Chilonzor b.s.k.", type="equity", sector="banking"),
        Instrument(ticker="ALKB", name="Алокабанк", type="equity", sector="banking"),
        Instrument(ticker="UZMK", name="УзМетКомбинат", type="equity", sector="metallurgy"),
        Instrument(ticker="IPTB", name="Ипотека-банк", type="equity", sector="banking"),
        Instrument(ticker="KVTS", name="Кварц", type="equity", sector="industry"),
        Instrument(ticker="TRSB", name="Трастбанк", type="equity", sector="banking"),
        Instrument(ticker="UZINP", name="Узбекинвест", type="equity", sector="insurance"),
        Instrument(ticker="AGMKP", name="АГМК преф", type="pref", sector="metallurgy"),
        Instrument(ticker="UZNF", name="UzNIF фонд", type="fund", sector="fund"),
        Instrument(ticker="ONETP", name="Худудий электр", type="pref", sector="energy"),
        Instrument(ticker="UZNGP", name="Узбекнефтегаз преф", type="pref", sector="energy"),
        Instrument(ticker="BNGPP", name="Бухоронефтегаз преф", type="pref", sector="energy"),
    ]
    for inst in instruments:
        db.merge(inst)

    # === Позиции ===
    positions = [
        Position(ticker="SQBN", broker="GoInvest", shares=162892, avg_buy_price=31.78),
        Position(ticker="HMKB", broker="GoInvest", shares=34386, avg_buy_price=65.50),
        Position(ticker="UZTL", broker="Jett", shares=397, avg_buy_price=5900),
        Position(ticker="CBSK", broker="GoInvest", shares=41754, avg_buy_price=3.05),
        Position(ticker="ALKB", broker="GoInvest", shares=99857, avg_buy_price=0.85),
        Position(ticker="UZMK", broker="Jett", shares=252, avg_buy_price=5550),
        Position(ticker="IPTB", broker="GoInvest", shares=3005, avg_buy_price=3.05),
        Position(ticker="KVTS", broker="Jett", shares=73, avg_buy_price=2460),
        Position(ticker="TRSB", broker="Jett", shares=111, avg_buy_price=11999),
        Position(ticker="UZINP", broker="Jett", shares=30, avg_buy_price=1990),
        Position(ticker="AGMKP", broker="GoInvest", shares=100, avg_buy_price=17000),
        Position(ticker="UZNF", broker="GoInvest", shares=888888, avg_buy_price=6.65),
        Position(ticker="ONETP", broker="Jett", shares=86, avg_buy_price=4770),
        Position(ticker="UZNGP", broker="Jett", shares=156, avg_buy_price=2821),
        Position(ticker="BNGPP", broker="Jett", shares=6, avg_buy_price=120000),
    ]
    for p in positions:
        p.updated_at = now()
        db.add(p)

    # === Цены ===
    prices = [
        PricePoint(ticker="SQBN", price=31.78, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="HMKB", price=65.50, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="UZTL", price=5900, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="CBSK", price=3.05, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="ALKB", price=0.85, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="UZMK", price=5550, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="IPTB", price=3.05, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="KVTS", price=2460, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="TRSB", price=11999, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="UZINP", price=1990, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="AGMKP", price=17000, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="UZNF", price=6.65, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="ONETP", price=4770, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="UZNGP", price=2821, source="kapdepo:H27", as_of="2026-08-01"),
        PricePoint(ticker="BNGPP", price=120000, source="manual", as_of="2026-08-01"),
    ]
    for p in prices:
        p.created_at = now()
        db.add(p)

    # === Таргеты ===
    targets = [
        Target(ticker="SQBN", value=37.00, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="HMKB", value=74.68, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="UZTL", value=7650, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="UZTL", value=52603, horizon="internal_fund", analyst="UzNIF", as_of="2026-08-01"),
        Target(ticker="CBSK", value=4.20, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="ALKB", value=1.13, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="ALKB", value=1.10, horizon="fundamental", analyst="KAP DEPO deep-dive", as_of="2026-08-01"),
        Target(ticker="UZMK", value=6800, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="UZMK", value=6314, horizon="1Y", analyst="Freedom Broker", as_of="2026-08-01"),
        Target(ticker="IPTB", value=3.40, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="KVTS", value=2000, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="KVTS", value=3490, horizon="fundamental", analyst="KAP DEPO deep-dive", as_of="2026-08-01"),
        Target(ticker="TRSB", value=8000, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
        Target(ticker="UZINP", value=1850, horizon="1Y", analyst="KAP DEPO panorama", as_of="2026-08-01"),
    ]
    for t in targets:
        t.created_at = now()
        db.add(t)

    # === Облигации ===
    bonds = [
        Bond(ticker="ACMT2B5", issuer="Agat Credit", coupon_rate=25, coupon_freq=4,
             nominal=100000, buy_price=109607, shares=96, maturity="2028-05-21",
             insured=True, insurer="Trust-Insurance", broker="EXTURE+G", account="IIS"),
        Bond(ticker="ACMT2B4", issuer="Agat Credit", coupon_rate=26, coupon_freq=4,
             nominal=100000, buy_price=105000, shares=93, maturity="2028-01-16",
             insured=True, insurer="Trust-Insurance", broker="EXTURE+G", account="IIS"),
    ]
    for b in bonds:
        b.updated_at = now()
        db.merge(b)

    # === Катализаторы ===
    catalysts = [
        Catalyst(date="2027-06-30", fuzzy_label="H1 2027", kind="ipo", 
                 label="IPO АГМК (LSE)", status="confirmed"),
        Catalyst(date="2027-12-31", fuzzy_label="2H 2027", kind="ipo",
                 label="IPO Узбектелеком (межд. рынки)", status="confirmed"),
        Catalyst(date="2028-06-30", fuzzy_label="2028", kind="ipo",
                 label="IPO ONETP / UTGA", status="confirmed"),
        Catalyst(date="2030-06-30", fuzzy_label="~2030", kind="ipo",
                 label="IPO Узпромстройбанк", status="confirmed"),
        Catalyst(date="2028-01-16", fuzzy_label="16.01.2028", kind="maturity",
                 label="Погашение ACMT2B4", status="confirmed"),
        Catalyst(date="2028-05-21", fuzzy_label="21.05.2028", kind="maturity",
                 label="Погашение ACMT2B5", status="confirmed"),
        Catalyst(ticker="UZTL", date="2026-09-01", fuzzy_label="Q3 2026", kind="todo",
                 label="Проверить страховку HMMT4B2 перед покупкой", status="confirmed"),
    ]
    for c in catalysts:
        c.created_at = now()
        db.add(c)

    db.commit()