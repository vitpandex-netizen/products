"""System Change Log — FastAPI приложение.

Единый контур фиксации всех изменений в экосистеме.
Все агенты пишут сюда, все агенты читают отсюда.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="System Change Log",
    description="Единый контур фиксации всех изменений в экосистеме",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8300)