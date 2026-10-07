from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


RESERVED_ALIASES = {
    "api",
    "docs",
    "health",
    "openapi.json",
    "redoc",
}

class URLCreate(BaseModel):
    url: AnyHttpUrl
    custom_alias: str | None = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def validate_expiration(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include timezone information")

        return value
    

    @field_validator("custom_alias")
    @classmethod
    def validate_custom_alias(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if value.lower() in RESERVED_ALIASES:
            raise ValueError("custom alias is reserved")

        return value

class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None