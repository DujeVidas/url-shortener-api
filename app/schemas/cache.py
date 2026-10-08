from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class CachedURL(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url_id: int = Field(gt=0)
    original_url: AnyHttpUrl
    expires_at: datetime | None