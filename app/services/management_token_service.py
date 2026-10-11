import hashlib
import secrets


def generate_management_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    return token, token_hash


def verify_management_token(
    token: str,
    stored_hash: str | None,
) -> bool:
    if not token or stored_hash is None:
        return False

    supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    return secrets.compare_digest(supplied_hash, stored_hash)
