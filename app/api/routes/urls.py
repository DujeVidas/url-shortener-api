from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import get_settings
from app.db.dependencies import get_db
from app.db.models import URL
from app.schemas.url import URLCreate, URLResponse
from app.services.url_service import (MAX_CODE_GENERATION_ATTEMPTS, generate_unique_short_code)
from app.schemas.analytics import URLAnalyticsResponse
from app.services.analytics_service import get_url_analytics
from app.services.cache_service import delete_cached_url


settings = get_settings()

router = APIRouter(
    prefix="/api/v1/urls",
    tags=["urls"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_url(
    payload: URLCreate,
    db: DbSession,
) -> URLResponse:
    is_custom_alias = payload.custom_alias is not None

    max_attempts = (
        1 if is_custom_alias else MAX_CODE_GENERATION_ATTEMPTS
    )

    for _ in range(max_attempts):
        short_code = (
            payload.custom_alias
            if is_custom_alias
            else generate_unique_short_code(db)
        )

        url = URL(
            short_code=short_code,
            original_url=str(payload.url),
            expires_at=payload.expires_at,
        )

        db.add(url)

        try:
            db.commit()
            db.refresh(url)
            break

        except IntegrityError:
            db.rollback()

            if is_custom_alias:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Custom alias already exists",
                )

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
    )

@router.get(
    "/{short_code}/analytics",
    response_model=URLAnalyticsResponse,
)
def get_analytics(
    short_code: str,
    db: DbSession,
) -> URLAnalyticsResponse:
    analytics = get_url_analytics(db, short_code)

    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found",
        )

    return analytics


@router.delete(
    "/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_url(
    short_code: str,
    db: DbSession,
) -> None:
    url = db.scalar(
        select(URL).where(URL.short_code == short_code)
    )

    if url is None or not url.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found",
        )

    url.is_active = False

    db.commit()

    delete_cached_url(short_code)
