"""Unit tests for EmbeddingClassifier (Ollama embeddings mocked)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.models import Topic
from app.processing.classifier import EmbeddingClassifier

_MODULE = "app.processing.classifier.embed"

# Orthogonal-ish 3D vectors so cosine similarity is easy to reason about.
_AI_VEC = [1.0, 0.0, 0.0]
_WEB_VEC = [0.0, 1.0, 0.0]
_DEVOPS_VEC = [0.0, 0.0, 1.0]


@pytest.fixture
def classifier() -> EmbeddingClassifier:
    return EmbeddingClassifier()


@pytest.fixture
def topics() -> list[Topic]:
    return [
        Topic(id=1, name="AI & ML", description="machine learning"),
        Topic(id=2, name="Web Development", description="frontend, backend"),
        Topic(id=3, name="DevOps", description="kubernetes, docker"),
        Topic(id=4, name="Other", description="general consumer tech"),
    ]


def _embed_side_effect(topic_vecs: dict[str, list[float]], article_vec: list[float]):
    async def _embed(text: str) -> list[float]:
        for description, vec in topic_vecs.items():
            if description in text:
                return vec
        return article_vec

    return _embed


_DEFAULT_TOPIC_VECS = {
    "machine learning": _AI_VEC,
    "frontend, backend": _WEB_VEC,
    "kubernetes, docker": _DEVOPS_VEC,
    "general consumer tech": [-1.0, -1.0, -1.0],
}


class TestClassifyEmptyTopics:
    async def test_returns_empty_string_when_no_topics(self, classifier):
        result = await classifier.classify("Some article text", topics=[])
        assert result == ""


class TestClassifyBestMatch:
    async def test_picks_topic_with_highest_cosine_similarity(self, classifier, topics):
        with patch(
            _MODULE,
            new=AsyncMock(side_effect=_embed_side_effect(_DEFAULT_TOPIC_VECS, _WEB_VEC)),
        ):
            result = await classifier.classify("An article about React and CSS", topics)
        assert result == "Web Development"

    async def test_caches_topic_embeddings_across_calls(self, classifier, topics):
        mock_embed = AsyncMock(side_effect=_embed_side_effect(_DEFAULT_TOPIC_VECS, _AI_VEC))
        with patch(_MODULE, new=mock_embed):
            await classifier.classify("Neural networks", topics)
            call_count_after_first = mock_embed.call_count
            await classifier.classify("More neural networks", topics)

        # Second call should only re-embed the article, not the 4 topics again.
        assert mock_embed.call_count == call_count_after_first + 1


class TestClassifyLowConfidence:
    async def test_falls_back_to_other_when_below_threshold(self, classifier, topics):
        topic_vecs = {**_DEFAULT_TOPIC_VECS, "general consumer tech": [0.1, 0.1, 0.1]}
        # Points away from every specific topic axis -> low cosine similarity to all.
        article_vec = [-1.0, -1.0, -1.0]
        with patch(_MODULE, new=AsyncMock(side_effect=_embed_side_effect(topic_vecs, article_vec))):
            result = await classifier.classify("Buried iPhone feature for kids", topics)
        assert result == "Other"

    async def test_returns_empty_string_when_no_other_topic_configured(self, classifier):
        topics_without_other = [Topic(id=1, name="AI & ML", description="machine learning")]
        article_vec = [-1.0, -1.0, -1.0]
        with patch(
            _MODULE,
            new=AsyncMock(
                side_effect=_embed_side_effect({"machine learning": _AI_VEC}, article_vec)
            ),
        ):
            result = await classifier.classify("Unrelated content", topics_without_other)
        assert result == ""
