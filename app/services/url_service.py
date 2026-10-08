import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import URL

from sqlalchemy.exc import IntegrityError

SHORT_CODE_LENGTH = 6

SHORT_CODE_ALPHABET = string.ascii_letters + string.digits

MAX_CODE_GENERATION_ATTEMPTS = 5

class ShortCodeGenerationError(Exception):
    """Raised when no available short code is found."""

SHORT_CODE_UNIQUE_CONSTRAINT = "ix_urls_short_code"


def is_short_code_collision(error: IntegrityError) -> bool:
    original_error = error.orig

    # PostgreSQL reports the violated constraint's name.
    diagnostic = getattr(original_error, "diag", None)

    constraint_name = getattr(
        diagnostic,
        "constraint_name",
        None,
    )

    if constraint_name is not None:
        return constraint_name == SHORT_CODE_UNIQUE_CONSTRAINT

    # SQLite does not expose PostgreSQL-style diagnostics.
    # This fallback is used by our SQLite endpoint tests.
    return (
        "UNIQUE constraint failed: urls.short_code"
        in str(original_error)
    )

def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    return "".join(
        secrets.choice(SHORT_CODE_ALPHABET)
        for _ in range(length)
    )


def short_code_exists(db: Session, short_code: str) -> bool:
    statement = select(URL.id).where(URL.short_code == short_code)

    return db.scalar(statement) is not None


def generate_unique_short_code(db: Session) -> str:
    for _ in range(MAX_CODE_GENERATION_ATTEMPTS):
        short_code = generate_short_code()

        if not short_code_exists(db, short_code):
            return short_code

    raise ShortCodeGenerationError(
        "Could not generate a unique short code"
    )
