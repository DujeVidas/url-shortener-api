from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.dependencies import get_db
from app.db.models import URL
from app.schemas.url import URLCreate, URLResponse
from app.services.url_service import generate_unique_short_code

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
def create_url(payload: URLCreate, db: DbSession) -> URLResponse:
    short_code = (
        payload.custom_alias
        if payload.custom_alias is not None
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
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Short code already exists",
        ) from None

    db.refresh(url)

    settings = get_settings()

    return URLResponse(
        short_code=url.short_code,
        short_url=f"{settings.base_url.rstrip('/')}/{url.short_code}",
        original_url=url.original_url,
        created_at=url.created_at,
        expires_at=url.expires_at,
    )