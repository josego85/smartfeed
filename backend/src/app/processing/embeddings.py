import httpx
from ..core.config import settings

OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"


async def embed(text: str) -> list[float]:
    """Generate embedding for text via Ollama."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts via Ollama (batch)."""
    embeddings = []
    async with httpx.AsyncClient(timeout=30) as client:
        for text in texts:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text},
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
    return embeddings
