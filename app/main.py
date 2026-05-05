from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
import asyncio

from app.core.redis import close_redis, get_redis
from app.db.init_db import init_db
from app.core.worker import run_worker


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    await get_redis()
    
    # Start the background worker process natively inside the FastAPI event loop
    worker_task = asyncio.create_task(run_worker())
    
    yield
    
    worker_task.cancel()
    await close_redis()


settings = get_settings()
configure_logging()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def home():
    return {"message": "News Analyst API running"}


@app.get("/health")
async def health():
    redis = await get_redis()
    return {"status": "ok", "redis": await redis.ping()}
