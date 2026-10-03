"""Run the deterministic local RAG baseline against the checked-in dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
DEFAULT_DATASET = Path(__file__).parent / "datasets" / "rag_baseline.json"
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag_evaluation import evaluate_cases  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Path to a JSON RAG evaluation dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the JSON report. Defaults to stdout.",
    )
    args = parser.parse_args()

    try:
        cases: list[dict[str, Any]] = json.loads(args.dataset.read_text(encoding="utf-8"))
        report = evaluate_cases(cases)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))

    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Wrote evaluation report to {args.output}")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
