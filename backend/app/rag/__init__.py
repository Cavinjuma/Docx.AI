"""RAG orchestration: prompts and answer generation (Phase 6)."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from app.embeddings import HashingEmbeddingProvider
from app.retrieval import MemoryVectorStore

STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "please",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
    "you",
    "your",
}
NO_ANSWER = (
    "I couldn’t find enough relevant information in the uploaded documents "
    "to answer that question."
)


class GroundedAnswerService:
    """Retrieve relevant context from uploaded documents and generate grounded answers."""

    def __init__(self, embedding_provider: Any | None = None, min_score: float = 0.12) -> None:
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider(dimensions=32)
        self.min_score = min_score

    def answer_question(
        self,
        question: str,
        documents: Iterable[str | dict[str, str]],
    ) -> dict[str, Any]:
        cleaned_documents: list[dict[str, str]] = []
        for document in documents:
            if isinstance(document, dict):
                text = str(document.get("text") or document.get("content") or "").strip()
                source = str(
                    document.get("source") or document.get("filename") or "uploaded-document"
                )
            else:
                text = str(document).strip()
                source = "uploaded-document"

            if text:
                cleaned_documents.append({"text": text, "source": source})

        if not cleaned_documents or not question.strip():
            return {
                "answer": NO_ANSWER,
                "citations": [],
            }

        chunks = self._chunk_documents(cleaned_documents)
        if not chunks:
            return {
                "answer": NO_ANSWER,
                "citations": [],
            }

        store = MemoryVectorStore(self.embedding_provider)
        for index, chunk in enumerate(chunks):
            store.add(f"chunk-{index}", chunk["text"], {"source": chunk["source"]})

        raw_results = store.search(question, limit=len(chunks))
        ranked = []
        query_tokens = self._tokenize(question)
        for result in raw_results:
            chunk_tokens = self._tokenize(result["text"])
            token_union = set(query_tokens) | set(chunk_tokens)
            overlap = len(set(query_tokens) & set(chunk_tokens)) / max(len(token_union), 1)
            # HashingEmbeddingProvider is a deterministic local placeholder, not a semantic model.
            # Keep lexical evidence primary so its random cosine value cannot suppress a match.
            combined_score = overlap + (max(float(result["score"]), 0.0) * 0.05)
            ranked.append({**result, "combined_score": combined_score})

        ranked.sort(key=lambda item: item["combined_score"], reverse=True)
        top_matches = [item for item in ranked if item["combined_score"] >= self.min_score]
        if not top_matches:
            return {
                "answer": NO_ANSWER,
                "citations": [],
            }

        best = top_matches[0]
        answer = self._build_answer(question, best["text"])
        citations = [
            {
                "text": item["text"],
                "score": round(float(item["combined_score"]), 4),
                "source": item["metadata"].get("source", "uploaded-document"),
            }
            for item in top_matches
        ]
        return {"answer": answer, "citations": citations}

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
            if token and token not in STOPWORDS
        }

    @staticmethod
    def _chunk_documents(
        documents: list[dict[str, str]],
        chunk_size: int = 180,
        overlap: int = 30,
    ) -> list[dict[str, str]]:
        chunks: list[dict[str, str]] = []
        for document_index, document in enumerate(documents):
            source = str(
                document.get("source")
                or document.get("filename")
                or f"document-{document_index}"
            )
            text = str(document.get("text") or document.get("content") or "").strip()
            if not text:
                continue
            words = text.split()
            for start in range(0, len(words), chunk_size - overlap):
                segment = words[start : start + chunk_size]
                if not segment:
                    continue
                chunk_text = " ".join(segment)
                chunks.append({"source": source, "text": chunk_text})
        return chunks

    @staticmethod
    def _build_answer(question: str, context: str) -> str:
        question_lower = question.lower()
        number_match = re.search(r"\b\d+(?:\.\d+)?\b", context)
        if number_match:
            number = number_match.group(0)
            if "how many" in question_lower or "many" in question_lower:
                return f"The uploaded document indicates {number}."

        snippet = context.strip()
        if len(snippet) > 180:
            snippet = snippet[:180].rstrip() + "..."
        return f"According to the uploaded documents: {snippet}"


__all__ = ["GroundedAnswerService"]
