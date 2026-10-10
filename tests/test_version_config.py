import pytest
from pydantic import ValidationError

from app.core.config import Settings

DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/testdb"


def test_default_app_version():
    settings = Settings(
        database_url=DATABASE_URL,
        _env_file=None,
    )

    assert settings.app_version == "0.1.0"


def test_custom_app_version():
    settings = Settings(
        database_url=DATABASE_URL,
        app_version="1.2.3",
        _env_file=None,
    )

    assert settings.app_version == "1.2.3"


def test_empty_app_version_rejected():
    with pytest.raises(ValidationError):
        Settings(
            database_url=DATABASE_URL,
            app_version="",
            _env_file=None,
        )


def test_oversized_app_version_rejected():
    with pytest.raises(ValidationError):
        Settings(
            database_url=DATABASE_URL,
            app_version="x" * 51,
            _env_file=None,
        )
