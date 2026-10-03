"""EmbeddingProvider interface and implementations (Phase 5)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence


class EmbeddingProvider:
    """Base interface for text embedding providers."""

    dimensions: int

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


class HashingEmbeddingProvider(EmbeddingProvider):
    """A deterministic, dependency-free embedding provider used as a local fallback.

    This keeps the project runnable without installing sentence-transformers while still
    providing stable vectors for basic semantic matching logic and tests.
    """

    def __init__(self, dimensions: int = 32, seed: str = "ai-document-intelligence") -> None:
        self.dimensions = dimensions
        self.seed = seed

    def embed_text(self, text: str) -> list[float]:
        normalized = text.strip().lower()
        if not normalized:
            return [0.0 for _ in range(self.dimensions)]

        vector: list[float] = []
        for index in range(self.dimensions):
            digest = hashlib.sha256(f"{self.seed}:{normalized}:{index}".encode("utf-8")).digest()
            value = int.from_bytes(digest[:8], byteorder="big", signed=False) / float(2**64)
            vector.append((value * 2.0) - 1.0)
        return vector


__all__ = ["EmbeddingProvider", "HashingEmbeddingProvider"]
