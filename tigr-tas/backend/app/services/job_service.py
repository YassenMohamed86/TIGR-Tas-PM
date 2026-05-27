from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import NoResultFound

from app.models.job import AnalysisJob, JobStatus

class JobNotFoundError(Exception):
    pass

class JobNotCancellableError(Exception):
    pass

class JobPermissionError(Exception):
    pass

async def create_job(
    db: AsyncSession,
    job_type: str,
    input_data: dict,
    org_id: UUID | None = None,
    user_id: UUID | None = None,
    priority: int = 5
) -> AnalysisJob:
    job = AnalysisJob(
        job_type=job_type,
        input_data=input_data,
        org_id=org_id,
        user_id=user_id,
        priority=priority,
        status=JobStatus.PENDING.value
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

async def get_job(
    db: AsyncSession, job_id: UUID, org_id: UUID | None = None
) -> AnalysisJob | None:
    stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
    if org_id:
        stmt = stmt.where(AnalysisJob.org_id == org_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def list_jobs(
    db: AsyncSession,
    org_id: UUID | None = None,
    status: JobStatus | None = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[list[AnalysisJob], int]:
    stmt = select(AnalysisJob, func.count().over().label("total_count"))
    
    if org_id:
        stmt = stmt.where(AnalysisJob.org_id == org_id)
    if status:
        stmt = stmt.where(AnalysisJob.status == status.value)
        
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    
    rows = result.all()
    if not rows:
        return [], 0
        
    jobs = [row[0] for row in rows]
    total_count = rows[0].total_count
    
    return jobs, total_count

async def update_job_status(
    db: AsyncSession,
    job_id: UUID,
    status: JobStatus,
    progress: int | None = None,
    celery_task_id: str | None = None,
    result_data: dict | None = None,
    error_message: str | None = None
) -> AnalysisJob:
    job = await get_job(db, job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    job.status = status.value
    
    if progress is not None:
        job.progress = progress
    if celery_task_id is not None:
        job.celery_task_id = celery_task_id
    if result_data is not None:
        job.result_data = result_data
    if error_message is not None:
        job.error_message = error_message
        
    now = datetime.now(timezone.utc)
    
    if status == JobStatus.RUNNING and not job.started_at:
        job.started_at = now
    elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
        job.completed_at = now

    await db.commit()
    await db.refresh(job)
    return job

async def cancel_job(
    db: AsyncSession, job_id: UUID, org_id: UUID | None = None
) -> AnalysisJob:
    job = await get_job(db, job_id, org_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")
        
    if job.status not in (JobStatus.PENDING.value, JobStatus.QUEUED.value):
        raise JobNotCancellableError(f"Job {job_id} is in status {job.status} and cannot be cancelled")
        
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(job)
    return job
