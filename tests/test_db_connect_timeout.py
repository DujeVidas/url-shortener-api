import pytest
from pydantic import ValidationError

from app.core.config import Settings

TEST_DATABASE_URL = "postgresql+psycopg://test:test@localhost:5432/test_db"


def test_database_connect_timeout_defaults_to_five_seconds(monkeypatch):
    monkeypatch.delenv("DB_CONNECT_TIMEOUT", raising=False)

    settings = Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
    )

    assert settings.db_connect_timeout == 5


@pytest.mark.parametrize("value", [0, -1, 61])
def test_database_connect_timeout_rejects_invalid_values(value):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            db_connect_timeout=value,
        )


def test_database_connect_timeout_accepts_valid_value():
    settings = Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
        db_connect_timeout=10,
    )

    assert settings.db_connect_timeout == 10