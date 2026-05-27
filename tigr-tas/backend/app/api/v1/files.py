from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_async_session
from app.config.settings import get_settings, Settings
from app.schemas.genome_file import GenomeFileResponse
from app.schemas.common import PaginatedResponse
from app.services import file_service
from app.models.genome_file import GenomeFile

router = APIRouter()

@router.post("/upload", response_model=GenomeFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings)
):
    try:
        genome_file = await file_service.save_upload(db, file, settings)
        return genome_file
    except file_service.FileValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/", response_model=PaginatedResponse[GenomeFileResponse])
async def list_files_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session)
):
    stmt = select(GenomeFile, func.count().over().label("total_count")).limit(limit).offset(offset)
    result = await db.execute(stmt)
    rows = result.all()
    
    if not rows:
        return PaginatedResponse(items=[], total=0, limit=limit, offset=offset)
        
    files = [row[0] for row in rows]
    total_count = rows[0].total_count
    
    return PaginatedResponse(items=files, total=total_count, limit=limit, offset=offset)

@router.get("/{file_id}", response_model=GenomeFileResponse)
async def get_file_endpoint(
    file_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    genome_file = await file_service.get_file(db, file_id)
    if not genome_file:
        raise HTTPException(status_code=404, detail="File not found")
    return genome_file

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
    file_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    try:
        await file_service.delete_file(db, file_id)
    except file_service.FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
