import time
from dataclasses import dataclass, field
from datetime import datetime

import feedparser
import httpx

from ..core.config import settings
from ..core.models import Article, Feed


@dataclass
class FetchResult:
    title: str
    description: str
    articles: list[Article] = field(default_factory=list)


async def fetch_feed(feed: Feed) -> FetchResult:
    headers = {
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"),
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    async with httpx.AsyncClient(timeout=settings.http_timeout, follow_redirects=True) as client:
        response = await client.get(feed.url, headers=headers)
        response.raise_for_status()

    parsed = feedparser.parse(response.text)
    title = getattr(parsed.feed, "title", "") or ""
    description = (
        getattr(parsed.feed, "description", "") or getattr(parsed.feed, "subtitle", "") or ""
    )
    articles = []

    for entry in parsed.entries:
        content = entry.get("summary") or (entry.get("content") or [{}])[0].get("value") or ""
        articles.append(
            Article(
                feed_id=feed.id,
                url=entry.get("link", ""),
                title=entry.get("title", ""),
                content=content,
                published_at=_parse_date(entry),
            )
        )

    return FetchResult(title=title, description=description, articles=articles)


def _parse_date(entry) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime.fromtimestamp(time.mktime(entry.published_parsed))
    return None
