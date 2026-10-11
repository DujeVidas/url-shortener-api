from unittest.mock import MagicMock

from app.services.analytics_service import record_click


def test_record_click_truncates_oversized_metadata():
    db = MagicMock()

    referrer = "r" * 3000
    user_agent = "u" * 1500

    record_click(
        db=db,
        url_id=123,
        referrer=referrer,
        user_agent=user_agent,
    )

    db.add.assert_called_once()
    db.commit.assert_called_once()

    click_event = db.add.call_args.args[0]

    assert click_event.url_id == 123
    assert click_event.referrer == referrer[:2048]
    assert click_event.user_agent == user_agent[:1024]
