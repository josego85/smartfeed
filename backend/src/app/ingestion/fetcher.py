import time
from datetime import datetime

import feedparser
import httpx

from ..core.models import Article, Feed


async def fetch_feed(feed: Feed) -> list[Article]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
        ),
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(feed.url, headers=headers)
        response.raise_for_status()

    parsed = feedparser.parse(response.text)
    articles = []

    for entry in parsed.entries:
        content = (
            entry.get("summary")
            or (entry.get("content") or [{}])[0].get("value")
            or ""
        )
        articles.append(
            Article(
                feed_id=feed.id,
                url=entry.get("link", ""),
                title=entry.get("title", ""),
                content=content,
                published_at=_parse_date(entry),
            )
        )

    return articles


def _parse_date(entry) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime.fromtimestamp(time.mktime(entry.published_parsed))
    return None
