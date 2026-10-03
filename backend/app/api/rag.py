from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.rag import GroundedAnswerService
from app.schemas.rag import AnswerResponse, QuestionRequest

router = APIRouter(tags=["rag"])


@router.post("/query", response_model=AnswerResponse)
def query_documents(payload: QuestionRequest, current_user: CurrentUserDep) -> AnswerResponse:
    """Answer a question grounded in uploaded document context."""
    service = GroundedAnswerService()
    result = service.answer_question(payload.question, payload.documents)

    citations = [
        {
            "text": citation["text"],
            "score": citation["score"],
            "source": citation["source"],
        }
        for citation in result["citations"]
    ]
    return AnswerResponse(answer=result["answer"], citations=citations)
