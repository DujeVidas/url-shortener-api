from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.db.models import URL
from app.services.analytics_service import record_click
from app.services.cache_service import cache_url, get_cached_url

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]

def is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    return expires_at <= datetime.now(timezone.utc)


@router.get("/{short_code}", response_class=RedirectResponse)
def redirect_to_url(short_code: str, request: Request, db: DbSession) -> RedirectResponse:
    cached_url = get_cached_url(short_code)

    if cached_url is not None:
        statement = select(URL).where(
            URL.id == cached_url.url_id,
            URL.short_code == short_code,
            URL.is_active.is_(True),
        )

        url = db.scalar(statement)

        if url is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found",
            )

        if is_expired(url.expires_at):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Short URL has expired",
            )

        record_click(
            db=db,
            url_id=url.id,
            referrer=request.headers.get("referer"),
            user_agent=request.headers.get("user-agent"),
        )

        return RedirectResponse(
            url=url.original_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    statement = select(URL).where(
        URL.short_code == short_code,
        URL.is_active.is_(True),
    )

    url = db.scalar(statement)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found",
        )
    if is_expired(url.expires_at):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Short URL has expired",
        )

    cache_url(
        short_code=url.short_code, 
        url_id=url.id,
        original_url=url.original_url,
        expires_at=url.expires_at,
    )

    record_click(
        db=db,
        url_id=url.id,
        referrer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
    )

    return RedirectResponse(
        url=url.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )