from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.url import URL


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    url_id: Mapped[int] = mapped_column(
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    referrer: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    url: Mapped["URL"] = relationship(
        back_populates="click_events",
    )