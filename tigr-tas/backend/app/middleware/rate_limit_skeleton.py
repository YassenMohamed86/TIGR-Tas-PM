from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RateLimitSkeletonMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Stub for future rate limit logic
        return await call_next(request)
