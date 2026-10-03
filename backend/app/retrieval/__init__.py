"""VectorStore interface and retrieval logic (Phase 5-6)."""

from __future__ import annotations

import math
from typing import Any

from app.embeddings import EmbeddingProvider, HashingEmbeddingProvider


class VectorStore:
    """Small interface for storing text records and searching by vector similarity."""

    def add(self, record_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        raise NotImplementedError

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError


class MemoryVectorStore(VectorStore):
    """In-memory vector store used for local development and tests."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self._records: list[dict[str, Any]] = []

    def add(self, record_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        embedding = self.embedding_provider.embed_text(text)
        self._records.append({
            "id": record_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
        })

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_vector = self.embedding_provider.embed_text(query)
        scored: list[dict[str, Any]] = []

        for record in self._records:
            score = self._cosine_similarity(query_vector, record["embedding"])
            scored.append({
                "id": record["id"],
                "text": record["text"],
                "score": score,
                "metadata": record["metadata"],
            })

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            raise ValueError("Embedding vectors must be the same length")

        magnitude_left = math.sqrt(sum(value * value for value in left))
        magnitude_right = math.sqrt(sum(value * value for value in right))
        if magnitude_left == 0.0 or magnitude_right == 0.0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(left, right, strict=True))
        return dot_product / (magnitude_left * magnitude_right)


__all__ = ["MemoryVectorStore", "VectorStore"]
