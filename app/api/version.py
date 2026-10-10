from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(tags=["metadata"])


class VersionResponse(BaseModel):
    name: str
    version: str
    environment: str


@router.get("/api/v1/version", response_model=VersionResponse)
def get_version() -> VersionResponse:
    settings = get_settings()

    return VersionResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
