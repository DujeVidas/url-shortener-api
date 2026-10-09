from unittest.mock import patch

from app.run import main


def test_uvicorn_access_logs_are_disabled():
    with patch("app.run.uvicorn.run") as mock_run:
        main()

    mock_run.assert_called_once_with(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        access_log=False,
        log_level="info",
    )