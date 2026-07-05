import numpy as np

from ..core.config import settings
from ..core.interfaces import Classifier
from ..core.models import Topic
from .embeddings import embed

OTHER_TOPIC_NAME = "Other"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


class EmbeddingClassifier(Classifier):
    """Zero-shot classification via cosine similarity against topic description embeddings.

    Topic embeddings are computed once per topic (id + description) and cached in-process —
    descriptions rarely change, and recomputing per article would mean 9 extra Ollama calls
    on every enrichment. Falls back to "Other" when the best match is below
    `classify_confidence_threshold`, so off-topic articles (e.g. consumer gadget news) don't
    get force-fit into an engineering-specific topic.
    """

    def __init__(self) -> None:
        self._topic_embedding_cache: dict[tuple[int | None, str], list[float]] = {}

    async def _topic_embedding(self, topic: Topic) -> list[float]:
        key = (topic.id, topic.description)
        cached = self._topic_embedding_cache.get(key)
        if cached is None:
            cached = await embed(topic.description)
            self._topic_embedding_cache[key] = cached
        return cached

    async def classify(self, text: str, topics: list[Topic]) -> str:
        if not topics:
            return ""

        article_vec = await embed(text[: settings.max_classify_chars])

        best_name = ""
        best_score = -1.0
        for topic in topics:
            topic_vec = await self._topic_embedding(topic)
            score = _cosine_similarity(article_vec, topic_vec)
            if score > best_score:
                best_name, best_score = topic.name, score

        if best_score < settings.classify_confidence_threshold:
            return OTHER_TOPIC_NAME if any(t.name == OTHER_TOPIC_NAME for t in topics) else ""

        return best_name
