from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    documents: list[str]


class Citation(BaseModel):
    text: str
    score: float
    source: str


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation]
