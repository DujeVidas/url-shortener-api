import pytest
from pydantic import ValidationError

from app.core.config import Settings


TEST_DATABASE_URL = "postgresql+psycopg://test:test@localhost:5432/test_db"


def test_request_size_default(monkeypatch):
    monkeypatch.delenv("MAX_REQUEST_BODY_BYTES", raising=False)

    settings = Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
    )

    assert settings.max_request_body_bytes == 16384


def test_request_size_accepts_custom_value():
    settings = Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
        max_request_body_bytes=32768,
    )

    assert settings.max_request_body_bytes == 32768


@pytest.mark.parametrize("value", [0, 1023, 1048577])
def test_request_size_rejects_invalid_values(value):
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            database_url=TEST_DATABASE_URL,
            max_request_body_bytes=value,
        )

    assert "max_request_body_bytes" in str(exc_info.value)