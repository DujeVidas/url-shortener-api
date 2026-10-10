from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.redis import redis_client
from app.core.redis_health import check_redis_health
from app.db.dependencies import get_db

router = APIRouter(prefix="/health", tags=["health"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("")
def health_check(db: DbSession) -> JSONResponse:
    checks = {
        "database": "ok",
        "redis": "ok",
    }

    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        checks["database"] = "error"

    try:
        redis_client.ping()
    except RedisError:
        checks["redis"] = "error"

    healthy = all(value == "ok" for value in checks.values())

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "healthy" if healthy else "unhealthy",
            "checks": checks,
        },
    )


@router.get("/live")
def liveness_check() -> dict[str, str]:
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Check application readiness",
    description=(
        "Checks PostgreSQL and Redis connectivity. "
        "Returns HTTP 200 when both dependencies are available, "
        "or HTTP 503 when either dependency is unavailable."
    ),
    responses={
        200: {
            "description": "Application is ready",
            "content": {"application/json": {"example": {"status": "ready"}}},
        },
        503: {
            "description": "One or more dependencies are unavailable",
            "content": {"application/json": {"example": {"status": "not_ready"}}},
        },
    },
)
def readiness_check(db: DbSession) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )
    try:
        redis_ready = check_redis_health()
    except RedisError:
        redis_ready = False

    if not redis_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready"},
    )
