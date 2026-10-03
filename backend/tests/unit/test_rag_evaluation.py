import json
from pathlib import Path

import pytest

from app.rag_evaluation import evaluate_cases

DATASET_PATH = Path(__file__).resolve().parents[3] / "evaluation" / "datasets" / "rag_baseline.json"


def test_baseline_dataset_meets_local_rag_quality_targets() -> None:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    report = evaluate_cases(cases)

    assert report["case_count"] == 7
    metrics = report["metrics"]
    assert metrics["retrieval_recall"] >= 0.7
    assert metrics["citation_precision"] >= 0.9
    assert metrics["answer_term_recall"] >= 0.7
    assert metrics["faithfulness"] >= 0.9
    assert metrics["abstention_accuracy"] == 1.0


def test_evaluation_rejects_an_empty_dataset() -> None:
    with pytest.raises(ValueError, match="at least one case"):
        evaluate_cases([])
