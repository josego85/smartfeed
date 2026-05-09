import httpx
from ..core.config import settings



async def embed(text: str) -> list[float]:
    """Generate embedding for text via Ollama."""
    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={"model": settings.embedding_model, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts via Ollama (batch)."""
    embeddings = []
    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        for text in texts:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={"model": settings.embedding_model, "prompt": text},
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
    return embeddings
