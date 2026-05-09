import numpy as np

from ..core.config import settings
from ..core.models import Topic
from .embeddings import embed, embed_batch

_topic_embeddings: dict[str, list[float]] = {}


async def classify(text: str, topics: list[Topic]) -> str:
    global _topic_embeddings
    truncated = text[:settings.max_classify_chars]
    article_vec = np.array(await embed(truncated))

    if not _topic_embeddings:
        descriptions = [t.description for t in topics]
        vectors = await embed_batch(descriptions)
        _topic_embeddings = {t.name: vec for t, vec in zip(topics, vectors)}

    best_topic = topics[0].name if topics else ""
    best_score = -1.0

    for name, vec in _topic_embeddings.items():
        topic_vec = np.array(vec)
        score = float(
            np.dot(article_vec, topic_vec)
            / (np.linalg.norm(article_vec) * np.linalg.norm(topic_vec))
        )
        if score > best_score:
            best_score = score
            best_topic = name

    return best_topic
