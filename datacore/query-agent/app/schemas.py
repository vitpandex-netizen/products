from typing import Optional
from pydantic import BaseModel, Field


class DescribeRequest(BaseModel):
    schema_name: str = Field(default="public")
    table_name: Optional[str] = None


class ExecuteRequest(BaseModel):
    sql: str = Field(..., min_length=5, max_length=10000)
    limit: int = Field(default=100, ge=1, le=500)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000)
    context: str = ""
    model: str = "auto"


class ExecuteResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int
    execution_time_ms: float


class QueryResponse(BaseModel):
    question: str
    sql: str
    result: Optional[ExecuteResponse] = None
    answer: str = ""
    iterations: int = 0
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    tables_count: int