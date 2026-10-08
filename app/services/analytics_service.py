from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.models import ClickEvent, URL
from app.schemas.analytics import URLAnalyticsResponse


def record_click(
    db: Session,
    url_id: int,
    referrer: str | None,
    user_agent: str | None,
) -> None:
    click_event = ClickEvent(
        url_id=url_id,
        referrer=referrer,
        user_agent=user_agent,
    )

    db.add(click_event)
    db.commit()

def get_url_analytics(
    db: Session,
    short_code: str
) -> URLAnalyticsResponse | None:
    url = db.scalar(
        select(URL).where(URL.short_code == short_code)
    )

    if url is None:
        return None
    
    statement = select(
        func.count(ClickEvent.id),
        func.min(ClickEvent.timestamp),
        func.max(ClickEvent.timestamp)
    ).where(ClickEvent.url_id == url.id)

    total_clicks, first_clicked_at, last_clicked_at = db.execute(statement).one()

    return URLAnalyticsResponse(
        short_code=url.short_code,
        total_clicks=total_clicks,
        first_clicked_at=first_clicked_at,
        last_clicked_at=last_clicked_at
    )