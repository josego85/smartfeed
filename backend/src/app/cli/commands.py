import asyncio

import typer

from ..api.dependencies import get_classifier, get_repo, get_summarizer, get_vector_store
from ..core.config import settings
from ..core.models import Feed
from ..services.sync_service import FeedSyncService

app = typer.Typer(help="SmartFeed CLI")


@app.command()
def feeds_add(url: str, title: str = "", description: str = ""):
    """Add a new RSS feed."""
    repo = get_repo()
    feed = asyncio.run(repo.save_feed(Feed(url=url, title=title, description=description)))
    typer.echo(f"Feed added: [{feed.id}] {feed.url}")


@app.command()
def feeds_list():
    """List all registered feeds."""
    repo = get_repo()
    feeds = asyncio.run(repo.list_feeds())
    if not feeds:
        typer.echo("No feeds registered.")
        return
    for feed in feeds:
        typer.echo(f"[{feed.id}] {feed.title or feed.url}")


@app.command()
def feeds_sync():
    """Sync all feeds via FeedSyncService (fetch, classify, summarize, index)."""
    repo = get_repo()
    service = FeedSyncService(repo, get_vector_store(), get_summarizer(), get_classifier())

    async def run() -> None:
        feeds = await repo.list_feeds()
        for feed in feeds:
            if feed.id is None:
                continue
            typer.echo(f"Syncing {feed.title or feed.url}...")
            result = await service.sync(feed.id)
            typer.echo(f"  fetched={result.fetched}  new={result.new}  skipped={result.skipped}")

    asyncio.run(run())


@app.command()
def search(query: str, n: int = settings.search_default_results):
    """Search articles using semantic search."""
    vector_store = get_vector_store()
    results = asyncio.run(vector_store.search(query=query, n_results=n))
    if not results:
        typer.echo("No results found.")
        return
    for r in results:
        typer.echo(f"[{r.score:.2f}] {r.metadata.get('title', '')} — {r.metadata.get('url', '')}")
