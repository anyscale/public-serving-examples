import time
import json
import uuid
from typing import Callable
import logging

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from example_app.config import RATE_LIMIT_PER_MINUTE
from example_app.db.database import increment_rate_limit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request and response details."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request details
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Request started: {request_id}",
            extra={
                "request_id": request_id,
                "client_ip": client_host,
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
            },
        )

        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # Log response details
            logger.info(
                f"Request completed: {request_id}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "response_headers": dict(response.headers),
                },
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request_id}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time": process_time,
                },
                exc_info=True,
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for certain paths
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Increment rate counter
        current = await increment_rate_limit(client_ip)

        # Check if rate limit exceeded
        if current > RATE_LIMIT_PER_MINUTE:
            return Response(
                content=json.dumps(
                    {
                        "detail": "Rate limit exceeded",
                        "error_type": "rate_limit",
                        "error_code": 429,
                    }
                ),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-Rate-Limit-Limit"] = str(RATE_LIMIT_PER_MINUTE)
        response.headers["X-Rate-Limit-Remaining"] = str(
            max(0, RATE_LIMIT_PER_MINUTE - current)
        )
        response.headers["X-Rate-Limit-Reset"] = "60"  # Reset after 1 minute

        return response


def add_middleware(app: FastAPI) -> None:
    """Add all middleware to the application."""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, you'd restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-Process-Time",
            "X-Rate-Limit-Limit",
            "X-Rate-Limit-Remaining",
            "X-Rate-Limit-Reset",
            # These headers are needed for SSE/EventSource
            "Content-Type",
            "Cache-Control",
            "Connection",
            "X-Accel-Buffering",
        ],
    )

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Custom middlewares
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
