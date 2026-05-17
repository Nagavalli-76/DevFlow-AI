from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging, time

logger = logging.getLogger("devflow.http")

class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)
        logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
        return response
