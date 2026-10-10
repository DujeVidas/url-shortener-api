from unittest.mock import MagicMock, patch

import pytest

from app.core.rate_limit import (
    RateLimitExceeded,
    check_create_rate_limit,
)


def test_exceeded_limit_contains_limit_information():
    client = MagicMock()
    client.eval.return_value = 11

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit("127.0.0.1")

    assert exc_info.value.limit == 10
    assert 1 <= exc_info.value.retry_after <= 60
    client.close.assert_called_once()


def test_exception_remains_backward_compatible():
    exc = RateLimitExceeded(retry_after=30)

    assert exc.retry_after == 30
    assert exc.limit is None


def test_exceeded_limit_uses_configured_limit():
    client = MagicMock()
    client.eval.return_value = 11

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit("192.0.2.15")

    assert exc_info.value.limit == 10