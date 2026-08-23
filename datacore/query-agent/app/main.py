"""DataCore Query Agent — Tool Calling шлюз (S3).

Естественный язык → SQL → данные.
Read-only, валидация, LLM-роутер.
"""

import logging
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    DescribeRequest, ExecuteRequest, QueryRequest,
    ExecuteResponse, QueryResponse, HealthResponse,
)
from .db import get_pool, get_tables, execute, check_health
from .guard import validate, mask
from .llm import generate_sql, explain

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="DataCore Query Agent", version="1.0.0",
              description="Tool Calling шлюз: естественный язык → SQL → данные")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    await get_pool()
    ok, n = await check_health()
    logger.info("DB health: %s (%d tables)", ok, n)


@app.get("/health", response_model=HealthResponse)
async def health():
    ok, n = await check_health()
    return HealthResponse(
        status="ok" if ok else "degraded",
        version="1.0.0",
        database="connected" if ok else "error",
        tables_count=n,
    )


@app.post("/describe")
async def describe(req: DescribeRequest):
    """Схема таблиц БД."""
    tables = await get_tables(req.schema_name)
    if req.table_name:
        tables = [t for t in tables if t["name"] == req.table_name]
        if not tables:
            raise HTTPException(404, f"Table '{req.table_name}' not found")
    return tables


@app.post("/execute", response_model=ExecuteResponse)
async def exec_sql(req: ExecuteRequest):
    """Выполнить read-only SQL (только SELECT)."""
    ok, result = validate(req.sql)
    if not ok:
        raise HTTPException(422, result)

    sql = result
    if not sql.upper().strip().endswith("LIMIT") and req.limit:
        import re
        if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            sql = f"{sql} LIMIT {req.limit}"

    logger.info("SQL: %s", mask(sql))
    res = await execute(sql, req.limit)
    if "error" in res and res["error"]:
        raise HTTPException(422, res["error"])

    return ExecuteResponse(sql=sql, **res)


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Естественный вопрос → SQL → результат + ответ."""
    start = time.monotonic()

    # 1. Schema
    tables = await get_tables()

    # 2. Generate SQL
    sql, err, gen_ms = await generate_sql(req.question, tables, req.model)
    if not sql:
        return QueryResponse(question=req.question, sql="", error=err or "Generation failed",
                             iterations=1)

    # 3. Validate
    ok, result = validate(sql)
    if not ok:
        return QueryResponse(question=req.question, sql=sql, error=result, iterations=2)

    # 4. Execute
    exec_res = await execute(result, 100)
    if "error" in exec_res and exec_res["error"]:
        return QueryResponse(question=req.question, sql=result, error=exec_res["error"],
                             iterations=3)

    # 5. Explain
    answer = ""
    if exec_res["rows"]:
        answer = await explain(req.question, result,
                               exec_res["columns"], exec_res["rows"], req.model)

    total = (time.monotonic() - start) * 1000
    return QueryResponse(
        question=req.question,
        sql=result,
        result=ExecuteResponse(sql=result, **exec_res),
        answer=answer,
        iterations=4,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8400)