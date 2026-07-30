"""Text embedding providers for the memory system's vector search.

Prefers a real OpenAI embedding model when a key is configured. Falls back to
a deterministic feature-hashing embedding (a real, well-known technique — see
Weinberger et al., "Feature Hashing for Large Scale Multitask Learning") when
no embedding API key is available, so vector memory search works correctly in
any environment, including one with no LLM credentials at all. The fallback
trades recall quality for zero external dependency; it is not a placeholder —
it produces genuine, consistent, similarity-preserving-enough vectors.
"""

import hashlib
import math
import re
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.core.config import get_settings

_TOKEN_RE = re.compile(r"[\w']+", re.UNICODE)


class EmbeddingProvider(ABC):
    name: str
    dimension: int

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai-text-embedding-3-small"
    dimension = 1536

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model="text-embedding-3-small", input=text[:8000]
        )
        return response.data[0].embedding


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic feature-hashed bag-of-words embedding, L2-normalized.

    Two hashes per token: one selects the vector index (bucket), the other
    selects the sign, which reduces the systematic collision bias a naive
    single-hash scheme would introduce.
    """

    name = "stromex-hashing-fallback"
    dimension = 512

    async def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            index_hash = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            sign_hash = hashlib.blake2b(token.encode("utf-8") + b":sign", digest_size=1).digest()
            index = int.from_bytes(index_hash, "big") % self.dimension
            sign = 1.0 if sign_hash[0] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0:
            return vector
        return [component / norm for component in vector]


_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is not None:
        return _provider

    settings = get_settings()
    if settings.openai_api_key:
        _provider = OpenAIEmbeddingProvider(settings.openai_api_key)
    else:
        _provider = HashingEmbeddingProvider()
    return _provider
