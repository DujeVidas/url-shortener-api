import pytest
from pydantic import ValidationError

from app.core.config import Settings


TEST_DATABASE_URL = "postgresql+psycopg://test:test@localhost:5432/test_db"


def test_statement_timeout_defaults_to_ten_seconds(monkeypatch):
    monkeypatch.delenv("DB_STATEMENT_TIMEOUT_MS", raising=False)

    settings = Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
    )

    assert settings.db_statement_timeout_ms == 10000


def test_statement_timeout_accepts_custom_value():
    settings = Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
        db_statement_timeout_ms=30000,
    )

    assert settings.db_statement_timeout_ms == 30000


@pytest.mark.parametrize("value", [0, 999, 300001])
def test_statement_timeout_rejects_invalid_values(value):
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            database_url=TEST_DATABASE_URL,
            db_statement_timeout_ms=value,
        )

    assert "db_statement_timeout_ms" in str(exc_info.value)