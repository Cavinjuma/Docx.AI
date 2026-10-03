from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class MessageCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class Citation(BaseModel):
    text: str
    score: float
    source: str


class ConversationMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    citations: list[Citation] = []


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[ConversationMessageResponse] = []
