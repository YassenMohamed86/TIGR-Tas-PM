from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="TIGR-Tas Dual-Guide RNA Scoring Platform")

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routers import scan, auth, export
from app.envelope import error_envelope
import uuid
from datetime import datetime, timezone

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.middleware("http")
async def envelope_middleware(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    request.state.timestamp = datetime.now(timezone.utc).isoformat()
    response = await call_next(request)
    return response

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    env = error_envelope(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        request=request
    )
    return JSONResponse(status_code=exc.status_code, content=env)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    env = error_envelope(
        code="VALIDATION_ERROR",
        message="Request payload validation failed",
        details=exc.errors(),
        request=request
    )
    return JSONResponse(status_code=422, content=env)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    env = error_envelope(
        code="INTERNAL_ERROR",
        message="An unexpected internal server error occurred",
        details={"type": type(exc).__name__, "msg": str(exc)},
        request=request
    )
    return JSONResponse(status_code=500, content=env)

@app.middleware("http")
async def protect_api(request: Request, call_next):
    protected_paths = [
        '/api/v1/scan', 
        '/api/v1/scan/jobs/', 
        '/api/v1/offtarget/analyze', 
        '/api/v1/oracle/score', 
        '/api/v1/export/', 
        '/auth/me'
    ]
    
    path = request.url.path
    is_protected = False
    for p in protected_paths:
        if path.startswith(p) and not (path == '/api/v1/scan/variants' and request.method == 'GET'):
            is_protected = True
            
    if is_protected and 'Authorization' not in request.headers:
        env = error_envelope("UNAUTHORIZED", "Not authenticated", request=request)
        return JSONResponse(status_code=401, content=env)
        
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        env = error_envelope("INTERNAL_ERROR", "Internal server error", request=request)
        return JSONResponse(status_code=500, content=env)

app.include_router(scan.router)
app.include_router(export.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health/ready")
async def readiness_check():
    import redis
    redis_status = "healthy"
    try:
        r = redis.from_url(settings.celery_broker_url)
        r.ping()
    except Exception:
        redis_status = "unhealthy"
        
    return {
        "status": "ready" if redis_status == "healthy" else "degraded",
        "dependencies": {
            "postgresql": "not_configured",
            "redis": redis_status,
            "celery": "assumed_healthy" # Celery check is complex and often skipped for basic readiness
        }
    }
