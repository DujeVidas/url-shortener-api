from unittest.mock import MagicMock, patch

import pytest

from app.core.rate_limit import (
    RateLimitExceeded,
    check_create_rate_limit,
)


def make_redis_mock(count: int):
    client = MagicMock()
    client.eval.return_value = count
    return client


def test_first_request_has_nine_remaining():
    client = make_redis_mock(1)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        info = check_create_rate_limit("127.0.0.1")

    assert info.limit == 10
    assert info.remaining == 9
    assert 1 <= info.reset <= 60


def test_fifth_request_has_five_remaining():
    client = make_redis_mock(5)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        info = check_create_rate_limit("127.0.0.1")

    assert info.remaining == 5


def test_tenth_request_has_zero_remaining():
    client = make_redis_mock(10)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        info = check_create_rate_limit("127.0.0.1")

    assert info.remaining == 0


def test_eleventh_request_is_rejected():
    client = make_redis_mock(11)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit("127.0.0.1")

    assert 1 <= exc_info.value.retry_after <= 60


def test_remaining_never_becomes_negative():
    client = make_redis_mock(100)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        with pytest.raises(RateLimitExceeded):
            check_create_rate_limit("127.0.0.1")
