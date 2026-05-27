from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
from contextlib import asynccontextmanager

from app.config.logging_config import setup_logging
from app.config.settings import get_settings
from app.middleware.cors import add_cors_middleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.auth_skeleton import AuthSkeletonMiddleware
from app.middleware.rate_limit_skeleton import RateLimitSkeletonMiddleware
from app.api.v1.router import router as api_v1_router
from app.api.v1.health import router as health_router
from app.cache.redis_client import close_redis_pool
from app.database.engine import async_engine

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Application {settings.app_name} v{settings.app_version} starting up in {settings.app_env} mode")
    yield
    logger.info("Application shutting down, cleaning up resources...")
    await async_engine.dispose()
    await close_redis_pool()

def create_app() -> FastAPI:
    # 1. Structured logging initialization
    setup_logging()
    
    # 2. Settings validation
    settings = get_settings()
    
    # App initialization
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )
    
    # 3. CORSMiddleware
    add_cors_middleware(app)
    
    # 4. LoggingMiddleware
    app.add_middleware(LoggingMiddleware)
    
    # 5. AuthSkeletonMiddleware
    app.add_middleware(AuthSkeletonMiddleware)
    
    # 6. RateLimitSkeletonMiddleware
    app.add_middleware(RateLimitSkeletonMiddleware)
    
    # 7. APIRouter for /api/v1
    app.include_router(api_v1_router, prefix="/api/v1")
    
    # 8. /health/live and /health/ready
    app.include_router(health_router)
    
    # 9. Exception handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not Found"}
        )
        
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc.errors())}
        )

    return app

# The global app used for uvicorn
app = create_app()
