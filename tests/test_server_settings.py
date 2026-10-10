import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_server_settings():
    settings = Settings(
        database_url="sqlite://",
        app_host="127.0.0.1",
        app_port=8000,
    )

    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8000


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_invalid_server_port_is_rejected(port):
    with pytest.raises(ValidationError):
        Settings(
            database_url="sqlite://",
            app_port=port,
        )
