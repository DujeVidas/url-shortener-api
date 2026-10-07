from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.db.models import URL

from app.services.cache_service import cache_url, get_cached_url
from app.services.analytics_service import record_click

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/{short_code}", response_class=RedirectResponse)
def redirect_to_url(short_code: str, request: Request, db: DbSession) -> RedirectResponse:
    cached_url = get_cached_url(short_code)

    if cached_url is not None:
        url_id = int(cached_url["url_id"])
        original_url = str(cached_url["original_url"])

        record_click(
            db=db,
            url_id=url_id,
            referrer=request.headers.get("referer"),
            user_agent=request.headers.get("user-agent"),
        )

        return RedirectResponse(
            url=original_url,
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
    
    cache_url(
        short_code=url.short_code, 
        url_id=url.id,
        original_url=url.original_url
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