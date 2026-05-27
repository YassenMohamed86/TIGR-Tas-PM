from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.job import JobStatus

class JobCreateRequest(BaseModel):
    job_type: str = Field(..., max_length=50)
    input_data: dict[str, Any]
    priority: int = Field(5, ge=1, le=10)

class JobResponse(BaseModel):
    id: UUID
    org_id: UUID | None = None
    user_id: UUID | None = None
    status: JobStatus
    job_type: str
    input_data: dict[str, Any]
    result_data: dict[str, Any] | None = None
    error_message: str | None = None
    celery_task_id: str | None = None
    priority: int
    progress: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    duration_seconds: float | None = None

    model_config = ConfigDict(from_attributes=True)

class JobStatusResponse(BaseModel):
    id: UUID
    status: JobStatus
    progress: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
