import asyncio
from fastapi import APIRouter, Response, status
from app.config.settings import get_settings
from app.database.engine import AsyncSessionLocal
from app.cache.redis_client import get_redis_client
from app.worker.celery_app import celery_app
from sqlalchemy import text
from redis.exceptions import ConnectionError

router = APIRouter()

@router.get("/health/live", status_code=status.HTTP_200_OK)
async def health_live():
    settings = get_settings()
    return {
        "status": "alive",
        "app": settings.app_name,
        "version": settings.app_version
    }

async def check_postgres():
    try:
        async with asyncio.timeout(2.0):
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
        return "healthy"
    except Exception:
        return "unhealthy"

async def check_redis():
    try:
        async with asyncio.timeout(2.0):
            client = get_redis_client()
            await client.ping()
        return "healthy"
    except Exception:
        return "unhealthy"

async def check_celery():
    try:
        async with asyncio.timeout(2.0):
            # ping with 1s timeout
            inspector = celery_app.control.inspect(timeout=1.0)
            result = inspector.ping()
            if result:
                return "healthy"
            return "unhealthy"
    except Exception:
        return "unhealthy"

@router.get("/health/ready")
async def health_ready(response: Response):
    pg_status, redis_status, celery_status = await asyncio.gather(
        check_postgres(),
        check_redis(),
        check_celery()
    )
    
    is_ready = pg_status == "healthy" and redis_status == "healthy" and celery_status == "healthy"
    
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return {
        "status": "ready" if is_ready else "degraded",
        "dependencies": {
            "postgresql": pg_status,
            "redis": redis_status,
            "celery": celery_status
        }
    }
