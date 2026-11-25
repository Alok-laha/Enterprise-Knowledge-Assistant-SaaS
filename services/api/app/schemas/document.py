from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024


class DocumentUploadRequest(BaseModel):
    filename: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    content_type: Literal["application/pdf"]
    file_size: int = Field(gt=0, le=MAX_PDF_SIZE_BYTES)


class DocumentUploadUrlResponse(BaseModel):
    document_id: UUID
    upload_url: str
    expires_in: int


class DocumentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    status: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentItem]
    total: int
