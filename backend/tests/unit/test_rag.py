from app.rag import GroundedAnswerService


def test_grounded_answer_service_returns_evidence_from_relevant_document() -> None:
    service = GroundedAnswerService()
    question = "How many leave days does the policy allow?"
    documents = [
        "The employee leave policy allows 21 paid vacation days each year.",
        "Employees must submit expenses within 30 days.",
    ]

    result = service.answer_question(question, documents)

    assert "21" in result["answer"]
    assert result["citations"]
    assert any("21 paid vacation days" in citation["text"] for citation in result["citations"])


def test_grounded_answer_service_returns_no_answer_when_context_is_inadequate() -> None:
    service = GroundedAnswerService()

    result = service.answer_question(
        "What is the capital of France?",
        ["The sky is blue on clear days."],
    )

    assert result["answer"] == (
        "I couldn’t find enough relevant information in the uploaded documents "
        "to answer that question."
    )
    assert result["citations"] == []


def test_grounded_answer_service_finds_relevant_document_among_many_chunks() -> None:
    service = GroundedAnswerService()
    documents = [
        {
            "source": f"unrelated-{index}.txt",
            "text": f"Gardening notes discuss soil, plants, and watering schedule {index}.",
        }
        for index in range(5)
    ]
    documents.append(
        {
            "source": "northwind-budget.txt",
            "text": (
                "The Northwind bridge project has an approved construction budget "
                "of 450000 dollars."
            ),
        }
    )

    result = service.answer_question(
        "What is the approved budget for the Northwind bridge project?",
        documents,
    )

    assert "450000" in result["answer"]
    assert result["citations"]
    assert result["citations"][0]["source"] == "northwind-budget.txt"
