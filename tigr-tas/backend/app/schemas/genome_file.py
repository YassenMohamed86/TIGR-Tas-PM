from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict
from app.models.genome_file import UploadStatus

class GenomeFileResponse(BaseModel):
    id: UUID
    org_id: UUID | None = None
    user_id: UUID | None = None
    original_name: str
    stored_name: str
    file_path: str
    file_size_bytes: int
    file_extension: str
    mime_type: str | None = None
    md5_hash: str | None = None
    sha256_hash: str | None = None
    upload_status: UploadStatus
    genome_build: str | None = None
    annotation: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    size_mb: float

    model_config = ConfigDict(from_attributes=True)
