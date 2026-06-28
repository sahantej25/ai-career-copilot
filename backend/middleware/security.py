"""Security headers and request-size guardrails."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config import settings
from services.guardrails.constants import MAX_REQUEST_BODY_MB


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies before they reach route handlers."""

    def __init__(self, app, max_bytes: int | None = None):
        super().__init__(app)
        limit_mb = getattr(settings, "max_request_body_mb", MAX_REQUEST_BODY_MB)
        self.max_bytes = max_bytes or (limit_mb * 1024 * 1024)

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length."})
            if size > self.max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request body exceeds {self.max_bytes // (1024 * 1024)}MB limit."},
                )
        return await call_next(request)
