import time
import structlog
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = structlog.get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid4())
        request.state.correlation_id = correlation_id
        client_ip = request.client.host if request.client else None
        
        start_time = time.time()
        logger.info(
            event="request_started",
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id,
            client_ip=client_ip
        )
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                event="request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                correlation_id=correlation_id
            )
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                event="request_failed",
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "correlation_id": correlation_id}
            )
