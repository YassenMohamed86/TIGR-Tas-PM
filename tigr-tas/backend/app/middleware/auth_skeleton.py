from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class AuthSkeletonMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Stub for future JWT logic
        return await call_next(request)
