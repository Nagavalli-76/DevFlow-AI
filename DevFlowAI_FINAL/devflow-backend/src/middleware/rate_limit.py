from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from src.config.redis import cache
from src.config.settings import settings
import ipaddress
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def _get_client_ip(self, request: Request) -> str:
        """Extract and validate client IP from request, checking proxy headers first."""
        # Check X-Forwarded-For header (most common proxy header)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first (original client)
            ip = forwarded_for.split(",")[0].strip()
            if self._is_valid_ip(ip):
                return ip
        
        # Check X-Real-IP header (alternative proxy header)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            ip = real_ip.strip()
            if self._is_valid_ip(ip):
                return ip
        
        # Fall back to request.client.host
        if request.client and request.client.host:
            ip = request.client.host
            if self._is_valid_ip(ip):
                return ip
        
        return "unknown"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate and sanitize IP address."""
        try:
            # This will raise ValueError if IP is invalid
            ipaddress.ip_address(ip)
            return True
        except (ValueError, AttributeError):
            return False
    
    async def dispatch(self, request: Request, call_next):
        # Skip health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        ip = self._get_client_ip(request)
        key = f"rate:{ip}:{request.url.path}"

        try:
            count = await cache.increment_rate(key, window=60)
            if count > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(status_code=429, content={"error": "Rate limit exceeded. Try again in a minute."})
        except Exception as e:
            logger.error(f"Rate limiting error for {ip} on {request.url.path}: {str(e)}", exc_info=True)
            # If Redis is down, let requests through

        return await call_next(request)
