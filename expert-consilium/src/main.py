from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.db.session import init_db
from src.redis_client import close_redis, get_redis
from src.web.routes import router as web_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info(f"Starting {settings.service_name}...")

    # Init DB
    await init_db()
    logger.info("Database initialized")

    yield

    # Cleanup
    await close_redis()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Expert Consilium API",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(web_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": "0.1.0",
    }


def run_api() -> None:
    """Run the API server."""
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run_api()