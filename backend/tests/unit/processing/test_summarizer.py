"""Unit tests for LiteLLMSummarizer (litellm mocked)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.processing.summarizer import LiteLLMSummarizer

_MODULE = "app.processing.summarizer.litellm.acompletion"


def _make_llm_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices[0].message.content = content
    return response


@pytest.fixture
def summarizer() -> LiteLLMSummarizer:
    return LiteLLMSummarizer()


class TestSummarize:
    async def test_returns_summary_string(self, summarizer):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("This is a concise summary.")
            result = await summarizer.summarize("Long article content here...")
        assert result == "This is a concise summary."

    async def test_strips_surrounding_whitespace(self, summarizer):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("  Summary with spaces.  ")
            result = await summarizer.summarize("Article")
        assert result == "Summary with spaces."

    async def test_text_is_truncated_to_max_summarize_chars(self, summarizer):
        long_text = "y" * 10_000
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("Short summary")
            await summarizer.summarize(long_text)
            user_content = mock_llm.call_args[1]["messages"][1]["content"]
        assert len(user_content) <= settings.max_summarize_chars

    async def test_system_prompt_is_included(self, summarizer):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("Summary")
            await summarizer.summarize("Article text")
            messages = mock_llm.call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert len(messages[0]["content"]) > 0

    async def test_user_message_contains_article_text(self, summarizer):
        article = "Python is a versatile programming language."
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("Summary")
            await summarizer.summarize(article)
            user_content = mock_llm.call_args[1]["messages"][1]["content"]
        assert "Python" in user_content

    async def test_empty_string_input(self, summarizer):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("")
            result = await summarizer.summarize("")
        assert result == ""


class TestModelId:
    def test_ollama_prefix(self, summarizer):
        with patch.object(settings, "llm_provider", "ollama"), \
             patch.object(settings, "llm_model", "mistral"):
            assert summarizer._model_id() == "ollama/mistral"

    def test_cloud_no_prefix(self, summarizer):
        with patch.object(settings, "llm_provider", "openai"), \
             patch.object(settings, "llm_model", "gpt-4o-mini"):
            assert summarizer._model_id() == "gpt-4o-mini"

    def test_ollama_api_base_is_set(self, summarizer):
        with patch.object(settings, "llm_provider", "ollama"):
            assert summarizer._api_base() == settings.ollama_base_url

    def test_cloud_api_base_is_none(self, summarizer):
        with patch.object(settings, "llm_provider", "anthropic"):
            assert summarizer._api_base() is None
