import asyncio
import typer
from ..core.models import Feed
from ..api.dependencies import get_repo, get_vector_store, get_summarizer
from ..ingestion.scheduler import sync_all_feeds

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
    """Sync all feeds: fetch, classify, summarize, and index articles."""
    repo = get_repo()
    vector_store = get_vector_store()
    summarizer = get_summarizer()
    typer.echo("Syncing all feeds...")
    asyncio.run(sync_all_feeds(repo, vector_store, summarizer))
    typer.echo("Done.")


@app.command()
def search(query: str, n: int = 10):
    """Search articles using semantic search."""
    vector_store = get_vector_store()
    results = asyncio.run(vector_store.search(query=query, n_results=n))
    if not results:
        typer.echo("No results found.")
        return
    for r in results:
        typer.echo(f"[{r.score:.2f}] {r.metadata.get('title', '')} — {r.metadata.get('url', '')}")
