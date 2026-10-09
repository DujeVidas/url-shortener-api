import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_responses import error_response
from fastapi.encoders import jsonable_encoder

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