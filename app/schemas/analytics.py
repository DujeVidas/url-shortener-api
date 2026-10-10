from datetime import datetime

from pydantic import BaseModel


class URLAnalyticsResponse(BaseModel):
    short_code: str
    total_clicks: int
    first_clicked_at: datetime | None
    last_clicked_at: datetime | None
