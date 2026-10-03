from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserDep, SessionDep
from app.models import Conversation, Document, DocumentChunk, Message, Source
from app.rag import GroundedAnswerService
from app.schemas.conversation import (
    Citation,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationMessageResponse,
    ConversationResponse,
    MessageCreate,
)

router = APIRouter(tags=["conversations"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    conversation = Conversation(user_id=current_user.id, title=payload.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    db: SessionDep,
    current_user: CurrentUserDep,
) -> list[ConversationResponse]:
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return [
        ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
        )
        for conversation in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: int,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> ConversationDetailResponse:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = []
    for message in sorted(conversation.messages, key=lambda item: item.created_at):
        citations = [
            Citation(text=source.snippet or "", score=0.0, source=source.document_name)
            for source in message.sources
        ]
        messages.append(
            ConversationMessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                citations=citations,
            )
        )

    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=messages,
    )


@router.post("/conversations/{conversation_id}/messages", response_model=dict[str, ConversationMessageResponse])
def add_message(
    conversation_id: int,
    payload: MessageCreate,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, ConversationMessageResponse]:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    user_message = Message(conversation_id=conversation.id, role="user", content=payload.question)
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    document_chunks = (
        db.query(DocumentChunk)
        .join(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
        .all()
    )
    document_texts = [
        {"text": chunk.chunk_text, "source": chunk.document.filename if chunk.document else "uploaded-document"}
        for chunk in document_chunks
    ]
    service = GroundedAnswerService()
    answer = service.answer_question(payload.question, document_texts)

    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=answer["answer"])
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    document_lookup = {document.filename: document for document in db.query(Document).filter(Document.user_id == current_user.id).all()}
    for citation in answer.get("citations", []):
        document = document_lookup.get(citation.get("source"), None)
        if document is None:
            continue
        db.add(
            Source(
                message_id=assistant_message.id,
                document_id=document.id,
                document_name=document.filename,
                snippet=citation.get("text"),
            )
        )
    db.commit()

    return {
        "user": ConversationMessageResponse(
            id=user_message.id,
            role=user_message.role,
            content=user_message.content,
            created_at=user_message.created_at,
            citations=[],
        ),
        "assistant": ConversationMessageResponse(
            id=assistant_message.id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
            citations=[
                Citation(text=item["text"], score=float(item["score"]), source=item["source"])
                for item in answer.get("citations", [])
            ],
        ),
    }
