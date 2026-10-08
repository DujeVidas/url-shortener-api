from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.url import URLCreate


def test_create_url_with_valid_url():
    payload = URLCreate(url="https://example.com")

    assert str(payload.url) == "https://example.com/"
    assert payload.custom_alias is None
    assert payload.expires_at is None


def test_create_url_with_valid_custom_alias():
    payload = URLCreate(
        url="https://example.com",
        custom_alias="my-link_123",
    )

    assert payload.custom_alias == "my-link_123"


@pytest.mark.parametrize(
    "alias",
    [
        "ab",
        "invalid alias",
        "invalid.alias",
        "invalid/alias",
        "api",
        "docs",
    ],
)
def test_create_url_rejects_invalid_alias(alias):
    with pytest.raises(ValidationError):
        URLCreate(
            url="https://example.com",
            custom_alias=alias,
        )


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "ftp://example.com",
        "javascript:alert(1)",
    ],
)
def test_create_url_rejects_invalid_url(url):
    with pytest.raises(ValidationError):
        URLCreate(url=url)


def test_create_url_accepts_future_expiration():
    future = datetime.now(timezone.utc) + timedelta(days=1)

    payload = URLCreate(
        url="https://example.com",
        expires_at=future,
    )

    assert payload.expires_at == future


def test_create_url_rejects_past_expiration():
    past = datetime.now(timezone.utc) - timedelta(days=1)

    with pytest.raises(ValidationError):
        URLCreate(
            url="https://example.com",
            expires_at=past,
        )


def test_create_url_rejects_naive_expiration():
    naive = datetime(2030, 1, 1, 12, 0, 0)

    with pytest.raises(ValidationError):
        URLCreate(
            url="https://example.com",
            expires_at=naive,
        )