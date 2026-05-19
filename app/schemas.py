from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    message: str


class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["First item"])
    description: str | None = Field(default=None, examples=["Stored in PostgreSQL via SQLAlchemy"])


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ItemRead(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileRecordRead(BaseModel):
    id: int
    original_filename: str
    content_type: str | None
    size_bytes: int
    s3_bucket: str
    s3_key: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileUploadResponse(BaseModel):
    id: int
    original_filename: str
    size_bytes: int
    s3_bucket: str
    s3_key: str
    message: str = "File uploaded successfully"


class PresignedUrlResponse(BaseModel):
    file_id: int
    expires_in_seconds: int
    url: str
