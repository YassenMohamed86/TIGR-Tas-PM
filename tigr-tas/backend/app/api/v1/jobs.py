from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_session
from app.schemas.job import JobCreateRequest, JobResponse, JobStatusResponse
from app.schemas.common import PaginatedResponse
from app.models.job import JobStatus
from app.services import job_service

router = APIRouter()

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job_endpoint(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_async_session)
):
    job = await job_service.create_job(
        db=db,
        job_type=request.job_type,
        input_data=request.input_data,
        priority=request.priority
    )
    # TODO: Submits to Celery queue
    return job

@router.get("/", response_model=PaginatedResponse[JobResponse])
async def list_jobs_endpoint(
    status_filter: JobStatus | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session)
):
    jobs, total = await job_service.list_jobs(
        db=db,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    return PaginatedResponse(
        items=jobs,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_endpoint(
    job_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"detail": "Job not found", "error_code": "JOB_NOT_FOUND"})
    return job

@router.delete("/{job_id}", response_model=JobResponse)
async def delete_job_endpoint(
    job_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    try:
        job = await job_service.cancel_job(db, job_id)
        return job
    except job_service.JobNotFoundError:
        raise HTTPException(status_code=404, detail={"detail": "Job not found", "error_code": "JOB_NOT_FOUND"})
    except job_service.JobNotCancellableError as e:
        raise HTTPException(status_code=409, detail={"detail": str(e), "error_code": "JOB_NOT_CANCELLABLE"})

@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status_endpoint(
    job_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"detail": "Job not found", "error_code": "JOB_NOT_FOUND"})
    return job
