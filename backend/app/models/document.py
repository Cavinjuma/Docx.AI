from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    upload_date: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="UPLOADED", nullable=False)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    processing_error: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    sources: Mapped[list["Source"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Document(id={self.id!r}, filename={self.filename!r})"
