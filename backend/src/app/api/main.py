from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import settings
from ..storage.database import init_db
from .dependencies import get_repo, get_vector_store, get_summarizer
from .routes import articles, feeds, search
from ..ingestion import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start(
        repo=get_repo(),
        vector_store=get_vector_store(),
        summarizer=get_summarizer(),
    )
    yield
    scheduler.scheduler.shutdown()


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


@app.get("/health")
async def health():
    return {"status": "ok"}
