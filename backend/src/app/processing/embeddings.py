from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
MODEL_NAME = "all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(text: str) -> list[float]:
    return get_model().encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts).tolist()
