"""Polymarket Trader — автоматическая торговля prediction markets.

Использует сигналы из analytics.signals для открытия позиций через CLOB API.
Требует Polygon кошелёк с USDC.

Установка:
    pip install web3 eth-account

Запуск:
    python3 polymarket_trader.py --db ... --private-key ... --strategy momentum
"""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("polymarket-trader")

CLOB_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

# Минимальный размер ставки
MIN_STAKE = 5  # USDC


class PolymarketTrader:
    """Торговля prediction markets через CLOB API."""

    def __init__(
        self,
        db_url: str = "",
        private_key: str = "",
        strategy: str = "momentum",
        max_stake: float = 25.0,
    ):
        self.db_url = db_url
        self.private_key = private_key
        self.strategy = strategy
        self.max_stake = max_stake
        self.address = ""
        self.api_key = ""

        if private_key:
            self._init_wallet()

    def _init_wallet(self):
        """Инициализация кошелька и API ключа."""
        from eth_account import Account
        Account.enable_unaudited_hdwallet_features()
        acct = Account.from_key(self.private_key)
        self.address = acct.address
        logger.info("Wallet: %s", self.address)

        # API key через EIP-712
        self.api_key = self._generate_api_key(acct)
        logger.info("API key: %s", self.api_key[:12] + "...")

    def _generate_api_key(self, account) -> str:
        """Генерация API ключа для CLOB через типизированные данные."""
        from eth_account.messages import encode_typed_data

        domain = {
            "name": "PolymarketSignature",
            "version": "1",
            "chainId": 137,  # Polygon
        }
        types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "Message": [
                {"name": "action", "type": "string"},
                {"name": "timestamp", "type": "string"},
            ],
        }
        msg = {
            "action": "register",
            "timestamp": str(int(time.time())),
        }

        signed = account.sign_typed_data(domain, types, msg)
        return signed.signature.hex()

    async def get_signals(self) -> list[dict]:
        """Получить новые сигналы для торговли."""
        if not self.db_url:
            return []

        import asyncpg

        conn = await asyncpg.connect(self.db_url)
        try:
            rows = await conn.fetch("""
                SELECT id, signal_type, symbol, direction, strength, reason, ts
                FROM analytics.signals
                WHERE source = 'polymarket'
                  AND signal_type = 'momentum_break'
                  AND direction IN ('buy', 'sell')
                  AND ts > NOW() - INTERVAL '1 hour'
                  AND id NOT IN (
                    SELECT signal_id FROM analytics.trades
                    WHERE signal_id IS NOT NULL
                  )
                ORDER BY strength DESC
                LIMIT 3
            """)

            return [
                {
                    "id": r["id"],
                    "type": r["signal_type"],
                    "symbol": r["symbol"],
                    "direction": r["direction"],
                    "strength": float(r["strength"]) if r["strength"] else 0,
                    "reason": r["reason"],
                }
                for r in rows
            ]
        finally:
            await conn.close()

    async def get_market_by_question(self, question: str) -> Optional[dict]:
        """Найти market по вопросу."""
        if not self.db_url:
            return None

        import asyncpg

        conn = await asyncpg.connect(self.db_url)
        try:
            row = await conn.fetchrow(
                "SELECT condition_id, clob_token_ids FROM market_data.prediction_markets "
                "WHERE question ILIKE $1 LIMIT 1",
                f"{question[:60]}%",
            )
            if row:
                return {
                    "condition_id": row["condition_id"],
                    "token_ids": json.loads(row["clob_token_ids"]) if isinstance(row["clob_token_ids"], str) else row["clob_token_ids"],
                }
            return None
        finally:
            await conn.close()

    async def place_order(
        self,
        token_id: str,
        side: str,
        size: float,
        price: float,
    ) -> dict:
        """Разместить лимитный ордер на CLOB."""
        if not self.api_key:
            logger.warning("No API key — order not placed")
            return {"status": "simulated", "token": token_id, "side": side, "size": size, "price": price}

        import httpx

        payload = {
            "token_id": token_id,
            "side": side.upper(),  # BUY or SELL
            "size": str(size),
            "price": str(price),
            "fee_rate_bps": "0",
            "signature": self._sign_order(token_id, side, size, price),
            "owner": self.address,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{CLOB_API}/order",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 200:
                logger.info("Order placed: %s %s @ %.2f", side, token_id[:20], price)
                return resp.json()
            else:
                logger.error("Order failed: %s %s", resp.status_code, resp.text)
                return {"status": "error", "code": resp.status_code, "text": resp.text}

    def _sign_order(self, token_id: str, side: str, size: float, price: float) -> str:
        """Подписать ордер (заглушка — реальная подпись требует EIP-712)."""
        from eth_account import Account
        Account.enable_unaudited_hdwallet_features()
        acct = Account.from_key(self.private_key)

        domain = {
            "name": "Polymarket Order",
            "version": "1",
            "chainId": 137,
        }
        types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
            ],
            "Order": [
                {"name": "token_id", "type": "uint256"},
                {"name": "side", "type": "string"},
                {"name": "size", "type": "string"},
                {"name": "price", "type": "string"},
            ],
        }
        msg = {
            "token_id": token_id,
            "side": side.upper(),
            "size": str(size),
            "price": str(price),
        }

        signed = acct.sign_typed_data(domain, types, msg)
        return signed.signature.hex()

    async def run_cycle(self):
        """Один торговый цикл."""
        signals = await self.get_signals()
        logger.info("Found %d signals to trade", len(signals))

        for sig in signals:
            market = await self.get_market_by_question(sig["symbol"])
            if not market:
                logger.warning("Market not found: %s", sig["symbol"])
                continue

            token_ids = market.get("token_ids", [])
            if not token_ids:
                continue

            # Для BUY сигнала покупаем YES токен (индекс 0)
            token_idx = 0 if sig["direction"] == "buy" else 1
            token_id = token_ids[token_idx] if isinstance(token_ids, list) else token_ids

            # Размер ставки пропорционален strength сигнала
            stake = min(self.max_stake, max(MIN_STAKE, self.max_stake * sig["strength"] * 3))
            price = 0.50  # Средняя цена — реально надо брать из orderbook

            result = await self.place_order(token_id, "buy", stake, price)

            # Записываем сделку
            if self.db_url:
                await self._record_trade(sig["id"], token_id, sig["direction"], stake, price, result)

            await asyncio.sleep(5)  # Пауза между ордерами

    async def _record_trade(self, signal_id: int, token_id: str, side: str, size: float, price: float, result: dict):
        """Записать сделку в БД."""
        import asyncpg

        conn = await asyncpg.connect(self.db_url)
        try:
            await conn.execute("""
                INSERT INTO analytics.trades
                    (bot_name, symbol, side, quantity, price, value_usd, signal_id, meta, ts)
                VALUES ('polymarket-trader', $1, $2, $3, $4, $5, $6, $7::jsonb, NOW())
            """,
                f"token:{token_id[:20]}",
                side,
                size / price if price else 0,
                price,
                size,
                signal_id,
                json.dumps({"order_result": str(result)[:200]}),
            )
        finally:
            await conn.close()

    async def close(self):
        pass


async def main_loop(db_url: str, private_key: str, strategy: str, interval: int = 120):
    """Бесконечный цикл торговли."""
    trader = PolymarketTrader(
        db_url=db_url,
        private_key=private_key,
        strategy=strategy,
    )

    try:
        while True:
            logger.info("Trading cycle...")
            await trader.run_cycle()
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await trader.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Polymarket Trader")
    parser.add_argument("--db", default="", help="DB URL")
    parser.add_argument("--private-key", default="", help="Ethereum private key")
    parser.add_argument("--strategy", default="momentum", help="Trading strategy")
    parser.add_argument("--max-stake", type=float, default=25.0, help="Max USDC per trade")
    parser.add_argument("--interval", type=int, default=120, help="Cycle interval")
    parser.add_argument("--once", action="store_true", help="Single cycle")

    args = parser.parse_args()

    if args.once:
        async def run_once():
            t = PolymarketTrader(args.db, args.private_key, args.strategy, args.max_stake)
            try:
                signals = await t.get_signals()
                print(json.dumps({"signals": signals, "wallet": t.address}, indent=2))
            finally:
                await t.close()
        asyncio.run(run_once())
    else:
        asyncio.run(main_loop(
            args.db, args.private_key, args.strategy, args.interval
        ))