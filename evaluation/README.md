# Evaluation

**Status: local deterministic baseline implemented (Phase 9).**

Run the baseline from the repository root:

```bash
python evaluation/run_evaluation.py
```

The runner prints a JSON report for `datasets/rag_baseline.json`. Save a report locally with:

```bash
python evaluation/run_evaluation.py --output evaluation/results/local-baseline.json
```

The report includes:

- `retrieval_recall`: fraction of expected source documents returned in citations.
- `citation_precision`: fraction of cited sources that are expected relevant sources.
- `answer_term_recall`: fraction of expected answer terms present in the answer.
- `faithfulness`: fraction of informative answer tokens also found in cited evidence.
- `abstention_accuracy`: fraction of cases where the system correctly answers or abstains.

The checked-in set contains five answerable questions and two questions whose answers are not in
the documents. `backend/tests/unit/test_rag_evaluation.py` keeps basic quality thresholds from
regressing.

These scores evaluate only the current deterministic local baseline (hashing vectors and the
project's extractive answer builder). They are not measurements of a production embedding model,
pgvector deployment, or external LLM. Faithfulness and answer-term matching are lexical proxies;
they do not establish semantic correctness. Treat results as regression checks, not as an external
benchmark or production quality claim.
