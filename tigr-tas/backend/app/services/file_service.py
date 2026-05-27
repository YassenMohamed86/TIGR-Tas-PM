import os
import hashlib
from uuid import UUID, uuid4
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles
import logging

from app.models.genome_file import GenomeFile, UploadStatus
from app.config.settings import Settings

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(self.reason)

class FileNotFoundError(Exception):
    pass

async def validate_upload(
    filename: str, content_type: str, size_bytes: int, settings: Settings
) -> None:
    if not filename or len(filename) > 255:
        raise FileValidationError("Filename is empty or too long")
        
    if ".." in filename or "/" in filename or "\\" in filename:
        raise FileValidationError("Filename contains invalid path traversal characters")
        
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_extensions:
        raise FileValidationError(f"File extension '{ext}' is not allowed. Allowed: {', '.join(settings.allowed_extensions)}")
        
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileValidationError(f"File size exceeds maximum allowed size of {settings.max_upload_size_mb}MB")

async def save_upload(
    db: AsyncSession,
    file: UploadFile,
    settings: Settings,
    org_id: UUID | None = None,
    user_id: UUID | None = None
) -> GenomeFile:
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)
    
    await validate_upload(file.filename or "unknown", file.content_type or "application/octet-stream", size_bytes, settings)
    
    filename = file.filename or "unknown"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    stored_name = f"{uuid4()}.{ext}"
    
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / stored_name
    
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            md5_hash.update(chunk)
            sha256_hash.update(chunk)
            await f.write(chunk)
            
    genome_file = GenomeFile(
        org_id=org_id,
        user_id=user_id,
        original_name=filename,
        stored_name=stored_name,
        file_path=str(file_path),
        file_size_bytes=size_bytes,
        file_extension=ext,
        mime_type=file.content_type,
        md5_hash=md5_hash.hexdigest(),
        sha256_hash=sha256_hash.hexdigest(),
        upload_status=UploadStatus.COMPLETE.value,
    )
    
    db.add(genome_file)
    await db.commit()
    await db.refresh(genome_file)
    
    return genome_file

async def get_file(
    db: AsyncSession, file_id: UUID, org_id: UUID | None = None
) -> GenomeFile | None:
    stmt = select(GenomeFile).where(GenomeFile.id == file_id)
    if org_id:
        stmt = stmt.where(GenomeFile.org_id == org_id)
        
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def delete_file(
    db: AsyncSession, file_id: UUID, org_id: UUID | None = None
) -> None:
    genome_file = await get_file(db, file_id, org_id)
    if not genome_file:
        raise FileNotFoundError(f"File {file_id} not found")
        
    try:
        if os.path.exists(genome_file.file_path):
            os.remove(genome_file.file_path)
        else:
            logger.warning(f"Physical file not found for deletion: {genome_file.file_path}")
    except Exception as e:
        logger.error(f"Failed to delete physical file {genome_file.file_path}: {e}")
        
    await db.delete(genome_file)
    await db.commit()
