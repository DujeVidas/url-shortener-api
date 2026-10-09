from unittest.mock import patch

from app.core.config import Settings
from app.run import main


def test_uvicorn_uses_configured_host_and_port():
    settings = Settings(
        database_url="sqlite://",
        app_host="127.0.0.1",
        app_port=8000,
    )

    with (
        patch("app.run.get_settings", return_value=settings),
        patch("app.run.uvicorn.run") as mock_run,
    ):
        main()

    mock_run.assert_called_once_with(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        access_log=False,
        log_level="info",
    )


def test_uvicorn_accepts_custom_host_and_port():
    settings = Settings(
        database_url="sqlite://",
        app_host="0.0.0.0",
        app_port=9000,
    )

    with (
        patch("app.run.get_settings", return_value=settings),
        patch("app.run.uvicorn.run") as mock_run,
    ):
        main()

    mock_run.assert_called_once_with(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        access_log=False,
        log_level="info",
    )