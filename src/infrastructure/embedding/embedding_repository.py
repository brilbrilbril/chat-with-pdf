import os
from openai import AsyncOpenAI

from src.domain.interfaces.embedding_repository import IEmbeddingRepository

class ImpEmbeddingRepository(IEmbeddingRepository):
    def __init__(self, client: AsyncOpenAI | None = None):
        self._client = client or AsyncOpenAI(
            base_url=os.getenv("OPENAI_EMBEDDING_URL"),
            api_key=os.getenv("OPENAI_API_KEY"))
        self._model = os.getenv("EMBEDDING_MODEL")

    async def embed(self, text: str) -> list[float]:
        print(f"actual client base_url: {self._client.base_url}")
        print(f"client embedding: {self._client}")
        print(f"base_url embedding: {os.getenv('OPENAI_EMBEDDING_URL')}")
        print(f"embedding model: {self._model}")
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        print(f"actual client base_url: {self._client.base_url}")
        print(f"client embedding: {self._client}")
        print(f"base_url embedding: {os.getenv('OPENAI_EMBEDDING_URL')}")
        print(f"embedding model: {self._model}")
        if not texts:
            return []
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]