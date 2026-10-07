from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.db.models import URL

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/{short_code}", response_class=RedirectResponse)
def redirect_to_url(short_code: str, db: DbSession) -> RedirectResponse:
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

    return RedirectResponse(
        url=url.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )