import pytest
from pydantic import ValidationError

from app.core.config import Settings

TEST_DATABASE_URL = "postgresql+psycopg://test:test@localhost:5432/test_db"


def make_settings(monkeypatch, **overrides):
    for name in (
        "DB_POOL_SIZE",
        "DB_MAX_OVERFLOW",
        "DB_POOL_TIMEOUT",
        "DB_POOL_RECYCLE",
    ):
        monkeypatch.delenv(name, raising=False)

    return Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
        **overrides,
    )


def test_database_pool_defaults(monkeypatch):
    settings = make_settings(monkeypatch)

    assert settings.db_pool_size == 5
    assert settings.db_max_overflow == 5
    assert settings.db_pool_timeout == 10


def test_database_pool_accepts_custom_values(monkeypatch):
    settings = make_settings(
        monkeypatch,
        db_pool_size=10,
        db_max_overflow=3,
        db_pool_timeout=20,
    )

    assert settings.db_pool_size == 10
    assert settings.db_max_overflow == 3
    assert settings.db_pool_timeout == 20


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("db_pool_size", 0),
        ("db_pool_size", 51),
        ("db_max_overflow", -1),
        ("db_max_overflow", 51),
        ("db_pool_timeout", 0),
        ("db_pool_timeout", 121),
    ],
)
def test_database_pool_rejects_invalid_values(
    monkeypatch,
    field_name,
    value,
):
    with pytest.raises(ValidationError) as exc_info:
        make_settings(monkeypatch, **{field_name: value})

    assert field_name in str(exc_info.value)


def test_database_pool_recycle_defaults_to_thirty_minutes(monkeypatch):
    settings = make_settings(monkeypatch)

    assert settings.db_pool_recycle == 1800


def test_database_pool_recycle_accepts_custom_value(monkeypatch):
    settings = make_settings(
        monkeypatch,
        db_pool_recycle=3600,
    )

    assert settings.db_pool_recycle == 3600


@pytest.mark.parametrize("value", [0, 59, 86401])
def test_database_pool_recycle_rejects_invalid_values(monkeypatch, value):
    with pytest.raises(ValidationError) as exc_info:
        make_settings(
            monkeypatch,
            db_pool_recycle=value,
        )

    assert "db_pool_recycle" in str(exc_info.value)
