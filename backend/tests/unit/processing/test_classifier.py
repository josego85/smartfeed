"""Unit tests for LLMClassifier (litellm mocked)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.core.models import Topic
from app.processing.classifier import LLMClassifier

_MODULE = "app.processing.classifier.litellm.acompletion"


def _make_llm_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices[0].message.content = content
    return response


@pytest.fixture
def classifier() -> LLMClassifier:
    return LLMClassifier()


@pytest.fixture
def topics() -> list[Topic]:
    return [
        Topic(id=1, name="AI & ML", description="machine learning"),
        Topic(id=2, name="Web Development", description="frontend, backend"),
        Topic(id=3, name="DevOps", description="kubernetes, docker"),
    ]


class TestClassifyEmptyTopics:
    async def test_returns_empty_string_when_no_topics(self, classifier):
        result = await classifier.classify("Some article text", topics=[])
        assert result == ""


class TestClassifyExactMatch:
    async def test_returns_matching_topic_name(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("AI & ML")
            result = await classifier.classify("Deep learning and neural networks", topics)
        assert result == "AI & ML"

    async def test_returns_devops_topic(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("DevOps")
            result = await classifier.classify("Kubernetes deployment strategies", topics)
        assert result == "DevOps"


class TestClassifyFuzzyMatch:
    async def test_case_insensitive_match(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("ai & ml")
            result = await classifier.classify("Some AI text", topics)
        assert result == "AI & ML"

    async def test_partial_match_in_response(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            # LLM adds extra words — fuzzy match should still resolve
            mock_llm.return_value = _make_llm_response("AI & ML topic")
            result = await classifier.classify("Neural network article", topics)
        assert result == "AI & ML"


class TestClassifyInvalidResponse:
    async def test_returns_empty_string_for_unknown_topic(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("Sports News")
            result = await classifier.classify("Football match results", topics)
        assert result == ""


class TestClassifyLLMCall:
    async def test_topic_list_included_in_user_message(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("DevOps")
            await classifier.classify("CI/CD pipeline setup", topics)
            user_content = mock_llm.call_args[1]["messages"][1]["content"]
        assert "AI & ML" in user_content
        assert "Web Development" in user_content
        assert "DevOps" in user_content

    async def test_uses_temperature_zero(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("AI & ML")
            await classifier.classify("Article text", topics)
        assert mock_llm.call_args[1]["temperature"] == 0

    async def test_text_is_truncated_to_max_classify_chars(self, classifier, topics):
        long_text = "x" * 10_000
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("DevOps")
            await classifier.classify(long_text, topics)
            user_content = mock_llm.call_args[1]["messages"][1]["content"]
        # The article portion must not exceed the char limit
        assert "x" * (settings.max_classify_chars + 1) not in user_content

    async def test_system_prompt_is_first_message(self, classifier, topics):
        with patch(_MODULE, new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _make_llm_response("AI & ML")
            await classifier.classify("Text", topics)
            messages = mock_llm.call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert "classifier" in messages[0]["content"].lower()


class TestModelId:
    def test_ollama_prefix(self, classifier):
        with patch.object(settings, "llm_provider", "ollama"), \
             patch.object(settings, "llm_model", "llama3.2"):
            assert classifier._model_id() == "ollama/llama3.2"

    def test_cloud_no_prefix(self, classifier):
        with patch.object(settings, "llm_provider", "anthropic"), \
             patch.object(settings, "llm_model", "claude-haiku-4-5"):
            assert classifier._model_id() == "claude-haiku-4-5"

    def test_ollama_api_base_set(self, classifier):
        with patch.object(settings, "llm_provider", "ollama"):
            assert classifier._api_base() == settings.ollama_base_url

    def test_cloud_api_base_is_none(self, classifier):
        with patch.object(settings, "llm_provider", "openai"):
            assert classifier._api_base() is None
