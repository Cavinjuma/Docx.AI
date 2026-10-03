from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    processing_status: str
