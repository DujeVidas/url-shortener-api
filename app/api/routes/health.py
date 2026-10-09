from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.redis import redis_client
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
            status.HTTP_200_OK
            if healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "healthy" if healthy else "unhealthy",
            "checks": checks,
        },
    )