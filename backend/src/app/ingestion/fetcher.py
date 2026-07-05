import time
from dataclasses import dataclass, field
from datetime import datetime

import feedparser
import httpx

from ..core.config import settings
from ..core.models import Article, Feed

# HTTP status codes that indicate permanent rejection (no point retrying)
_PERMANENT_CODES = {403, 404, 410, 451}


class FetchError(Exception):
    pass


class PermanentFetchError(FetchError):
    """Non-retryable: server explicitly rejects the request (403, 404, 410, 451)."""

    def __init__(self, message: str, http_status: int) -> None:
        super().__init__(message)
        self.http_status = http_status


class TransientFetchError(FetchError):
    """Retryable: server error, timeout, or network failure."""

    pass


def _is_promotional(entry) -> bool:
    """True if the entry's RSS <category> tags mark it as a coupon/deal listicle.

    Matches on the publisher-provided category, not the title — title text (e.g.
    "20% Off") is too easy to confuse with a genuine editorial article about prices.
    """
    promotional_tags = {t.lower() for t in settings.promotional_feed_tags}
    entry_tags = {t.get("term", "").lower() for t in entry.get("tags", [])}
    return bool(entry_tags & promotional_tags)


@dataclass
class FetchResult:
    title: str
    description: str
    articles: list[Article] = field(default_factory=list)


async def fetch_feed(feed: Feed) -> FetchResult:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    try:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout, follow_redirects=True
        ) as client:
            response = await client.get(feed.url, headers=headers)
    except httpx.UnsupportedProtocol as exc:
        raise PermanentFetchError(str(exc), http_status=0) from exc
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise TransientFetchError(str(exc)) from exc

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code in _PERMANENT_CODES:
            raise PermanentFetchError(str(exc), http_status=code) from exc
        raise TransientFetchError(str(exc)) from exc

    parsed = feedparser.parse(response.text)
    title = getattr(parsed.feed, "title", "") or ""
    description = (
        getattr(parsed.feed, "description", "") or getattr(parsed.feed, "subtitle", "") or ""
    )
    articles = []

    for entry in parsed.entries:
        if _is_promotional(entry):
            continue
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
