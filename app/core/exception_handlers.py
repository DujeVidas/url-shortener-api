import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_responses import error_response
from app.core.request_context import request_id_context
from app.middleware.security_headers import SECURITY_HEADERS

logger = logging.getLogger("app.errors")


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    return error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return error_response(
        status_code=422,
        detail=jsonable_encoder(exc.errors()),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    request_id = request_id_context.get()

    if request_id is None:
        request_id = getattr(request.state, "request_id", None)

    headers = {
        name.decode("ascii"): value.decode("ascii") for name, value in SECURITY_HEADERS
    }

    if request_id is not None:
        headers["X-Request-ID"] = request_id

    return error_response(
        status_code=500,
        detail="Internal server error",
        headers=headers,
        request_id=request_id,
    )
