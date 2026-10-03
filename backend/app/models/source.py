from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    chunk_id: Mapped[int | None] = mapped_column(nullable=True)
    snippet: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    message: Mapped["Message"] = relationship(back_populates="sources")
    document: Mapped["Document"] = relationship(back_populates="sources")

    def __repr__(self) -> str:
        return f"Source(id={self.id!r}, document_name={self.document_name!r})"
