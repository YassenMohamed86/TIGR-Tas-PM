import enum
from sqlalchemy import (
    Column, 
    String, 
    BigInteger,
    DateTime, 
    Text, 
    func, 
    Index, 
    text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from app.database.base import Base

class UploadStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"

class GenomeFile(Base):
    __tablename__ = "genome_files"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    org_id = Column(PGUUID(as_uuid=True), nullable=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    file_extension = Column(String(20), nullable=False, index=True)
    mime_type = Column(String(100), nullable=True)
    md5_hash = Column(String(32), nullable=True, index=True)
    sha256_hash = Column(String(64), nullable=True)
    upload_status = Column(String(50), nullable=False, default=UploadStatus.UPLOADING.value)
    genome_build = Column(String(20), nullable=True)
    annotation = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    __table_args__ = (
        Index("ix_genome_files_org_status", "org_id", "upload_status"),
    )

    @property
    def size_mb(self) -> float:
        return round(self.file_size_bytes / (1024 * 1024), 2)
