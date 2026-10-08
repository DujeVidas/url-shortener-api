from unittest.mock import Mock

from sqlalchemy.exc import IntegrityError

from app.services.url_service import is_short_code_collision


def make_integrity_error(
    constraint_name: str | None,
    message: str,
) -> IntegrityError:
    original_error = Exception(message)

    if constraint_name is not None:
        diagnostic = Mock()
        diagnostic.constraint_name = constraint_name
        original_error.diag = diagnostic

    return IntegrityError(
        statement="INSERT INTO urls ...",
        params={},
        orig=original_error,
    )


def test_postgres_short_code_collision():
    error = make_integrity_error(
        constraint_name="ix_urls_short_code",
        message="duplicate key value violates unique constraint",
    )

    assert is_short_code_collision(error) is True


def test_postgres_unrelated_constraint():
    error = make_integrity_error(
        constraint_name="some_other_constraint",
        message="duplicate key value violates unique constraint",
    )

    assert is_short_code_collision(error) is False


def test_sqlite_short_code_collision():
    error = make_integrity_error(
        constraint_name=None,
        message="UNIQUE constraint failed: urls.short_code",
    )

    assert is_short_code_collision(error) is True


def test_sqlite_unrelated_constraint():
    error = make_integrity_error(
        constraint_name=None,
        message="NOT NULL constraint failed: urls.original_url",
    )

    assert is_short_code_collision(error) is False