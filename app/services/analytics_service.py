from sqlalchemy.orm import Session

from app.db.models import ClickEvent


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