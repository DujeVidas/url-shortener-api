from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.dependencies import get_db
from app.db.models import URL
from app.schemas.url import URLCreate, URLResponse

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
    if payload.custom_alias is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="custom_alias is required until automatic short-code generation is implemented",
        )

    url = URL(
        short_code=payload.custom_alias,
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