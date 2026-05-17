"""Unit tests for embed / embed_batch (Ollama HTTP mocked via respx)."""
import json

import httpx
import pytest
import respx

from app.core.config import settings
from app.processing.embeddings import embed, embed_batch

_EMBED_URL = f"{settings.ollama_base_url}/api/embeddings"
_MOCK_VECTOR = [0.1] * 768


class TestEmbed:
    @respx.mock
    async def test_returns_float_list(self):
        respx.post(_EMBED_URL).mock(
            return_value=httpx.Response(200, json={"embedding": _MOCK_VECTOR})
        )
        result = await embed("test text")
        assert result == _MOCK_VECTOR

    @respx.mock
    async def test_vector_length_matches_dim(self):
        respx.post(_EMBED_URL).mock(
            return_value=httpx.Response(200, json={"embedding": _MOCK_VECTOR})
        )
        result = await embed("hello")
        assert len(result) == settings.embedding_dim

    @respx.mock
    async def test_sends_correct_prompt(self):
        route = respx.post(_EMBED_URL).mock(
            return_value=httpx.Response(200, json={"embedding": _MOCK_VECTOR})
        )
        await embed("hello world")
        payload = json.loads(route.calls.last.request.content)
        assert payload["prompt"] == "hello world"

    @respx.mock
    async def test_sends_configured_model(self):
        route = respx.post(_EMBED_URL).mock(
            return_value=httpx.Response(200, json={"embedding": _MOCK_VECTOR})
        )
        await embed("text")
        payload = json.loads(route.calls.last.request.content)
        assert payload["model"] == settings.embedding_model

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.post(_EMBED_URL).mock(return_value=httpx.Response(500))
        with pytest.raises(httpx.HTTPStatusError):
            await embed("text")

    @respx.mock
    async def test_raises_on_service_unavailable(self):
        respx.post(_EMBED_URL).mock(return_value=httpx.Response(503))
        with pytest.raises(httpx.HTTPStatusError):
            await embed("text")


class TestEmbedBatch:
    @respx.mock
    async def test_returns_one_vector_per_text(self):
        respx.post(_EMBED_URL).mock(
            return_value=httpx.Response(200, json={"embedding": _MOCK_VECTOR})
        )
        results = await embed_batch(["a", "b", "c"])
        assert len(results) == 3

    @respx.mock
    async def test_each_result_is_a_vector(self):
        respx.post(_EMBED_URL).mock(
            return_value=httpx.Response(200, json={"embedding": _MOCK_VECTOR})
        )
        results = await embed_batch(["text one", "text two"])
        for vec in results:
            assert vec == _MOCK_VECTOR

    async def test_empty_batch_returns_empty_list(self):
        results = await embed_batch([])
        assert results == []

    @respx.mock
    async def test_raises_on_http_error(self):
        respx.post(_EMBED_URL).mock(return_value=httpx.Response(503))
        with pytest.raises(httpx.HTTPStatusError):
            await embed_batch(["text"])
