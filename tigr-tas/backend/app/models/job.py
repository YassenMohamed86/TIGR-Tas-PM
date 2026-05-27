import enum
from uuid import UUID
from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    Text, 
    func, 
    CheckConstraint, 
    Index, 
    text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from app.database.base import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    org_id = Column(PGUUID(as_uuid=True), nullable=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    status = Column(String(50), nullable=False, default=JobStatus.PENDING.value) # Use String for Enum backends, but alembic will create real ENUM
    job_type = Column(String(50), nullable=False, index=True)
    input_data = Column(JSONB, nullable=False)
    result_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True, index=True)
    priority = Column(Integer, default=5, nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 10", name="check_priority_range"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="check_progress_range"),
        Index("ix_analysis_jobs_org_status", "org_id", "status"),
        Index("ix_analysis_jobs_status_created_at", "status", "created_at"),
    )

    @property
    def duration_seconds(self) -> float | None:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
