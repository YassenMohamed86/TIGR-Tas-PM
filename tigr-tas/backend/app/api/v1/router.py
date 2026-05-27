from fastapi import APIRouter
from app.api.v1.jobs import router as jobs_router
from app.api.v1.files import router as files_router

router = APIRouter()

router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
router.include_router(files_router, prefix="/files", tags=["Files"])
