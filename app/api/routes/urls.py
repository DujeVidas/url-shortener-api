from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.rate_limit import enforce_create_rate_limit
from app.core.config import get_settings
from app.db.dependencies import get_db
from app.db.models import URL
from app.schemas.analytics import URLAnalyticsResponse
from app.schemas.url import URLCreate, URLResponse
from app.services.analytics_service import get_url_analytics
from app.services.cache_service import delete_cached_url
from app.services.management_token_service import (
    generate_management_token,
    verify_management_token,
)
from app.services.url_service import (
    MAX_CODE_GENERATION_ATTEMPTS,
    ShortCodeGenerationError,
    generate_unique_short_code,
    is_short_code_collision,
)

settings = get_settings()

router = APIRouter(
    prefix="/api/v1/urls",
    tags=["urls"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    dependencies=[Depends(enforce_create_rate_limit)],
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Short URL created successfully",
            "headers": {
                "RateLimit-Limit": {
                    "description": "Maximum requests allowed per window",
                    "schema": {"type": "integer"},
                },
                "RateLimit-Remaining": {
                    "description": "Requests remaining in the current window",
                    "schema": {"type": "integer"},
                },
                "RateLimit-Reset": {
                    "description": "Seconds until the rate-limit window resets",
                    "schema": {"type": "integer"},
                },
            },
        },
        429: {
            "description": "URL creation rate limit exceeded",
            "headers": {
                "Retry-After": {
                    "description": "Seconds to wait before retrying",
                    "schema": {"type": "integer"},
                },
                "RateLimit-Remaining": {
                    "description": "Requests remaining (zero)",
                    "schema": {"type": "integer"},
                },
                "RateLimit-Reset": {
                    "description": "Seconds until the current window resets",
                    "schema": {"type": "integer"},
                },
            },
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded",
                    }
                }
            },
        },
        503: {
            "description": "Rate limiting temporarily unavailable",
            "headers": {
                "Retry-After": {
                    "description": "Seconds to wait before retrying",
                    "schema": {"type": "integer"},
                },
            },
            "content": {
                "application/json": {
                    "example": {
                        "detail": "URL creation temporarily unavailable",
                    }
                }
            },
        },
    },
)
def create_url(
    payload: URLCreate,
    db: DbSession,
) -> URLResponse:
    is_custom_alias = payload.custom_alias is not None

    max_attempts = 1 if is_custom_alias else MAX_CODE_GENERATION_ATTEMPTS

    for _ in range(max_attempts):
        try:
            short_code = (
                payload.custom_alias
                if is_custom_alias
                else generate_unique_short_code(db)
            )
        except ShortCodeGenerationError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not generate a unique short code",
            ) from None

        management_token, management_token_hash = generate_management_token()

        url = URL(
            short_code=short_code,
            original_url=str(payload.url),
            expires_at=payload.expires_at,
            management_token_hash=management_token_hash,
        )

        db.add(url)

        try:
            db.commit()
            db.refresh(url)
            break

        except IntegrityError as exc:
            db.rollback()

            if not is_short_code_collision(exc):
                raise

            if is_custom_alias:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Custom alias already exists",
                ) from exc

    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate a unique short code",
        )

    return URLResponse(
        short_code=url.short_code,
        short_url=f"{settings.base_url.rstrip('/')}/{url.short_code}",
        original_url=url.original_url,
        created_at=url.created_at,
        expires_at=url.expires_at,
        management_token=management_token,
    )


@router.get(
    "/{short_code}/analytics",
    response_model=URLAnalyticsResponse,
    responses={
        403: {
            "description": "Invalid or missing management token",
        },
        404: {
            "description": "Short URL not found",
        },
    },
)
def get_analytics(
    short_code: str,
    db: DbSession,
    management_token: str | None = Header(
        default=None,
        alias="X-Management-Token",
    ),
) -> URLAnalyticsResponse:
    url = db.scalar(select(URL).where(URL.short_code == short_code))

    if url is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    if not verify_management_token(
        management_token or "",
        url.management_token_hash,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing management token",
        )

    analytics = get_url_analytics(db, short_code)

    if analytics is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    return analytics


@router.delete(
    "/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {
            "description": "Invalid or missing management token",
        },
        404: {
            "description": "Short URL not found or already deactivated",
        },
    },
)
def deactivate_url(
    short_code: str,
    db: DbSession,
    management_token: str | None = Header(
        default=None,
        alias="X-Management-Token",
    ),
) -> None:
    url = db.scalar(select(URL).where(URL.short_code == short_code))

    if url is None or not url.is_active:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    if not verify_management_token(
        management_token or "",
        url.management_token_hash,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing management token",
        )

    url.is_active = False
    db.commit()
    delete_cached_url(short_code)
