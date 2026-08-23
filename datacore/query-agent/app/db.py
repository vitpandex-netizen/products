"""Database pool — read-only connection to DataCore PostgreSQL."""

import logging
import os
import time
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATACORE_DATABASE_URL",
                         "postgresql://datacore_reader:reader_pass@postgres:5432/datacore")
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT_SECONDS", "30"))

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL, min_size=1, max_size=5,
            command_timeout=QUERY_TIMEOUT,
        )
    return _pool


async def get_tables(schema: str = "public") -> list[dict]:
    """Schema + columns + row counts for all tables."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT t.table_name,
               c.column_name, c.data_type, c.is_nullable,
               c.character_maximum_length, COALESCE(pgd.description,'') as comment
        FROM information_schema.tables t
        JOIN information_schema.columns c
            ON t.table_name=c.table_name AND t.table_schema=c.table_schema
        LEFT JOIN pg_catalog.pg_statio_all_tables st ON t.table_name=st.relname
        LEFT JOIN pg_catalog.pg_description pgd
            ON pgd.objoid=st.relid AND pgd.objsubid=c.ordinal_position::int
        WHERE t.table_schema=$1 AND t.table_type='BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position
    """, schema)

    tables = {}
    for r in rows:
        t = r["table_name"]
        if t not in tables:
            tables[t] = {"name": t, "columns": []}
        tables[t]["columns"].append({
            "name": r["column_name"], "type": r["data_type"],
            "nullable": r["is_nullable"] == "YES",
            "max_length": r["character_maximum_length"],
            "comment": r["comment"],
        })
    return list(tables.values())


async def execute(sql: str, limit: int = 100) -> dict:
    """Execute SELECT, return structured result."""
    pool = await get_pool()
    start = time.monotonic()
    try:
        rows = await pool.fetch(sql, timeout=QUERY_TIMEOUT)
    except Exception as e:
        return {"error": str(e), "columns": [], "rows": [], "row_count": 0, "execution_time_ms": 0}

    elapsed = (time.monotonic() - start) * 1000
    if not rows:
        return {"columns": [], "rows": [], "row_count": 0, "execution_time_ms": round(elapsed, 2)}

    cols = list(rows[0].keys())
    data = [list(r.values()) for r in rows[:limit]]
    return {"columns": cols, "rows": data, "row_count": len(data),
            "execution_time_ms": round(elapsed, 2)}


async def check_health() -> tuple[bool, int]:
    pool = await get_pool()
    try:
        await pool.fetchval("SELECT 1")
        tables = await get_tables()
        return True, len(tables)
    except Exception:
        return False, 0