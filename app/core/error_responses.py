from typing import Any

from fastapi.responses import JSONResponse

from app.core.request_context import request_id_context


def error_response(
    status_code: int,
    detail: Any,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "request_id": request_id_context.get(),
        },
        headers=headers,
    )