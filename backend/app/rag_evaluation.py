"""Deterministic evaluation helpers for the current local RAG pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from app.rag import NO_ANSWER, GroundedAnswerService


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate_cases(
    cases: Iterable[Mapping[str, Any]],
    service: GroundedAnswerService | None = None,
) -> dict[str, Any]:
    """Run cases and report source, answer-term, grounding, and abstention metrics."""
    answer_service = service or GroundedAnswerService()
    results: list[dict[str, Any]] = []

    for case in cases:
        documents = case["documents"]
        response = answer_service.answer_question(case["question"], documents)
        answer = str(response["answer"])
        citations = response.get("citations", [])
        cited_sources = {str(citation.get("source", "")) for citation in citations}
        expected_sources = {str(source) for source in case.get("expected_sources", [])}
        expected_terms = [str(term) for term in case.get("expected_answer_terms", [])]
        should_abstain = bool(case.get("should_abstain", False))
        did_abstain = answer == NO_ANSWER

        relevant_citations = cited_sources & expected_sources
        citation_precision = (
            len(relevant_citations) / len(cited_sources)
            if cited_sources
            else float(not expected_sources)
        )
        source_recall = (
            len(relevant_citations) / len(expected_sources)
            if expected_sources
            else float(not cited_sources)
        )
        normalized_answer = _normalize(answer)
        answer_term_recall = (
            sum(_normalize(term) in normalized_answer for term in expected_terms)
            / len(expected_terms)
            if expected_terms
            else float(should_abstain and did_abstain)
        )

        cited_evidence = " ".join(str(citation.get("text", "")) for citation in citations)
        answer_terms = answer_service._tokenize(answer) - {
            "according",
            "uploaded",
            "documents",
            "indicates",
        }
        evidence_terms = answer_service._tokenize(cited_evidence)
        faithfulness = (
            float(not citations)
            if did_abstain
            else len(answer_terms & evidence_terms) / len(answer_terms)
            if answer_terms
            else 0.0
        )

        results.append(
            {
                "id": str(case["id"]),
                "answer": answer,
                "cited_sources": sorted(cited_sources),
                "expected_sources": sorted(expected_sources),
                "retrieval_recall": round(source_recall, 4),
                "citation_precision": round(citation_precision, 4),
                "answer_term_recall": round(answer_term_recall, 4),
                "faithfulness": round(faithfulness, 4),
                "abstention_correct": did_abstain == should_abstain,
                "abstained": did_abstain,
            }
        )

    if not results:
        raise ValueError("Evaluation dataset must contain at least one case")

    return {
        "case_count": len(results),
        "metrics": {
            "retrieval_recall": round(_mean([item["retrieval_recall"] for item in results]), 4),
            "citation_precision": round(_mean([item["citation_precision"] for item in results]), 4),
            "answer_term_recall": round(_mean([item["answer_term_recall"] for item in results]), 4),
            "faithfulness": round(_mean([item["faithfulness"] for item in results]), 4),
            "abstention_accuracy": round(
                _mean([float(item["abstention_correct"]) for item in results]), 4
            ),
        },
        "cases": results,
    }
