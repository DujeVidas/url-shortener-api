import hashlib

from app.services.management_token_service import (
    generate_management_token,
    verify_management_token,
)


def test_generate_management_token_returns_token_and_hash():
    token, token_hash = generate_management_token()

    assert isinstance(token, str)
    assert len(token) >= 40

    assert len(token_hash) == 64
    assert token_hash == hashlib.sha256(token.encode("utf-8")).hexdigest()

    assert token != token_hash


def test_generate_management_tokens_are_distinct():
    first_token, first_hash = generate_management_token()
    second_token, second_hash = generate_management_token()

    assert first_token != second_token
    assert first_hash != second_hash


def test_verify_management_token_accepts_valid_token():
    token, token_hash = generate_management_token()

    assert verify_management_token(token, token_hash) is True


def test_verify_management_token_rejects_invalid_token():
    token, token_hash = generate_management_token()

    assert verify_management_token("incorrect-token", token_hash) is False
    assert verify_management_token(token, None) is False
    assert verify_management_token("", token_hash) is False
