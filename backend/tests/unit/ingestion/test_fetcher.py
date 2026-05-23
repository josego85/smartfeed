"""Unit tests for the RSS/Atom feed fetcher (httpx mocked via respx)."""
import time

import httpx
import pytest
import respx

from app.core.models import Feed
from app.ingestion.fetcher import FetchResult, _parse_date, fetch_feed

_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <description>A test RSS feed</description>
    <link>https://example.com</link>
    <item>
      <title>Article One</title>
      <link>https://example.com/article-1</link>
      <description>Content of article one.</description>
      <pubDate>Mon, 15 Jan 2024 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Article Two</title>
      <link>https://example.com/article-2</link>
      <description>Content of article two.</description>
    </item>
  </channel>
</rss>"""

_ATOM_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Feed</title>
  <subtitle>Subtitle used as description</subtitle>
  <entry>
    <title>Atom Article</title>
    <link href="https://atom.example.com/article-1"/>
    <summary>Summary of the atom article.</summary>
  </entry>
</feed>"""

_EMPTY_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title/>
    <description/>
  </channel>
</rss>"""


class TestFetchFeed:
    @respx.mock
    async def test_returns_fetch_result_type(self, sample_feed):
        respx.get(sample_feed.url).mock(return_value=httpx.Response(200, text=_RSS_XML))
        result = await fetch_feed(sample_feed)
        assert isinstance(result, FetchResult)

    @respx.mock
    async def test_parses_feed_title_and_description(self):
        feed = Feed(id=1, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_RSS_XML))
        result = await fetch_feed(feed)
        assert result.title == "Test Feed"
        assert result.description == "A test RSS feed"

    @respx.mock
    async def test_parses_article_count(self):
        feed = Feed(id=1, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_RSS_XML))
        result = await fetch_feed(feed)
        assert len(result.articles) == 2

    @respx.mock
    async def test_article_urls_and_titles(self):
        feed = Feed(id=1, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_RSS_XML))
        result = await fetch_feed(feed)
        assert result.articles[0].url == "https://example.com/article-1"
        assert result.articles[0].title == "Article One"
        assert result.articles[1].url == "https://example.com/article-2"

    @respx.mock
    async def test_article_feed_id_propagated(self):
        feed = Feed(id=42, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_RSS_XML))
        result = await fetch_feed(feed)
        for article in result.articles:
            assert article.feed_id == 42

    @respx.mock
    async def test_parses_published_date_for_item_with_pubdate(self):
        feed = Feed(id=1, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_RSS_XML))
        result = await fetch_feed(feed)
        assert result.articles[0].published_at is not None

    @respx.mock
    async def test_published_at_is_none_when_missing(self):
        feed = Feed(id=1, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_RSS_XML))
        result = await fetch_feed(feed)
        assert result.articles[1].published_at is None

    @respx.mock
    async def test_raises_on_404(self):
        feed = Feed(id=1, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(404))
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_feed(feed)

    @respx.mock
    async def test_raises_on_500(self):
        feed = Feed(id=1, url="https://example.com/rss")
        respx.get(feed.url).mock(return_value=httpx.Response(500))
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_feed(feed)

    @respx.mock
    async def test_parses_atom_feed_title(self):
        feed = Feed(id=1, url="https://atom.example.com/feed")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_ATOM_XML))
        result = await fetch_feed(feed)
        assert result.title == "Atom Feed"

    @respx.mock
    async def test_uses_subtitle_as_description_for_atom(self):
        feed = Feed(id=1, url="https://atom.example.com/feed")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_ATOM_XML))
        result = await fetch_feed(feed)
        assert result.description == "Subtitle used as description"

    @respx.mock
    async def test_parses_atom_entry(self):
        feed = Feed(id=1, url="https://atom.example.com/feed")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_ATOM_XML))
        result = await fetch_feed(feed)
        assert len(result.articles) == 1
        assert result.articles[0].title == "Atom Article"

    @respx.mock
    async def test_empty_feed_returns_empty_articles(self):
        feed = Feed(id=1, url="https://example.com/empty")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_EMPTY_RSS_XML))
        result = await fetch_feed(feed)
        assert result.articles == []

    @respx.mock
    async def test_empty_feed_returns_empty_title(self):
        feed = Feed(id=1, url="https://example.com/empty")
        respx.get(feed.url).mock(return_value=httpx.Response(200, text=_EMPTY_RSS_XML))
        result = await fetch_feed(feed)
        assert result.title == ""
        assert result.description == ""


class TestParseDate:
    def test_returns_none_when_published_parsed_missing(self):
        class _Entry:
            published_parsed = None

        assert _parse_date(_Entry()) is None

    def test_returns_none_when_attribute_absent(self):
        class _Entry:
            pass

        assert _parse_date(_Entry()) is None

    def test_returns_datetime_for_valid_struct_time(self):
        struct = time.strptime("2024-01-15", "%Y-%m-%d")

        class _Entry:
            published_parsed = struct

        result = _parse_date(_Entry())
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
