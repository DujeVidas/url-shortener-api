import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import URL

SHORT_CODE_LENGTH = 6

SHORT_CODE_ALPHABET = string.ascii_letters + string.digits

MAX_CODE_GENERATION_ATTEMPTS = 5

def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    return "".join(
        secrets.choice(SHORT_CODE_ALPHABET)
        for _ in range(length)
    )


def short_code_exists(db: Session, short_code: str) -> bool:
    statement = select(URL.id).where(URL.short_code == short_code)

    return db.scalar(statement) is not None


def generate_unique_short_code(db: Session) -> str:
    while True:
        short_code = generate_short_code()

        if not short_code_exists(db, short_code):
            return short_code
