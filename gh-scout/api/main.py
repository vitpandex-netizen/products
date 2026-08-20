"""GH Scout — FastAPI приложение."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import init_db, async_engine
from core.event_bus import close_redis
from api.routes.projects import router as projects_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    logger.info("Starting GH Scout...")
    await init_db()
    logger.info("Database tables ready")
    yield
    logger.info("Shutting down GH Scout...")
    await close_redis()
    await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router, prefix="/api/v1")

# Для обратной совместимости с DataCore gateway
app.include_router(projects_router, prefix="")


@app.get("/")
async def root():
    return {
        "service": "GH Scout",
        "version": "1.0.0",
        "endpoints": {
            "projects": "/api/v1/projects",
            "releases": "/api/v1/releases",
            "trends": "/api/v1/trends",
            "recommendations": "/api/v1/recommendations",
            "digest": "/api/v1/digest",
            "health": "/api/v1/health",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=settings.port, reload=True)