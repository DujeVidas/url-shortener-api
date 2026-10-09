import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.request_context import request_id_context

logger = logging.getLogger("app.requests")


def get_route_template(request: Request) -> str:
    route = request.scope.get("route")

    if route is None:
        return "<unmatched>"

    return getattr(route, "path", "<unmatched>")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.exception(
                "HTTP request failed",
                extra={
                    "event": "http_request",
                    "method": request.method,
                    "path": get_route_template(request),
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "request_id": request_id_context.get(),
                },
            )
            raise

        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        logger.info(
            "HTTP request completed",
            extra={
                "event": "http_request",
                "method": request.method,
                "path": get_route_template(request),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id_context.get(),
            },
        )

        return response