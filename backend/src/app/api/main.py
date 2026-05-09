from contextlib import asynccontextmanager

from arq.connections import RedisSettings, create_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import settings
from ..storage.database import init_db
from .routes import articles, feeds, search, topics


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    yield
    await app.state.redis_pool.aclose()


app = FastAPI(title="SmartFeed API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feeds.router, prefix="/api/feeds", tags=["feeds"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(topics.router, prefix="/api/topics", tags=["topics"])


@app.get("/health")
async def health():
    return {"status": "ok"}
