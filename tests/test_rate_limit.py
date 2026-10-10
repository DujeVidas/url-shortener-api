from unittest.mock import MagicMock, patch

import pytest

from app.core.rate_limit import (
    RateLimitExceeded,
    check_create_rate_limit,
)


def make_redis_mock():
    client = MagicMock()
    return client


def test_first_request_is_allowed():
    client = make_redis_mock()
    client.incr.return_value = 1

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("127.0.0.1")

    client.incr.assert_called_once()
    client.expire.assert_called_once()
    client.close.assert_called_once()


def test_request_within_limit_is_allowed():
    client = make_redis_mock()
    client.incr.return_value = 5

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("127.0.0.1")

    client.expire.assert_not_called()
    client.close.assert_called_once()


def test_request_above_limit_is_rejected():
    client = make_redis_mock()
    client.incr.return_value = 11

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit("127.0.0.1")

    assert exc_info.value.retry_after >= 1
    client.close.assert_called_once()


def test_client_ip_is_hashed_in_redis_key():
    client = make_redis_mock()
    client.incr.return_value = 1

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("192.0.2.15")

    key = client.incr.call_args.args[0]

    assert "192.0.2.15" not in key
    assert key.startswith("rate_limit:create:")


def test_different_ips_generate_different_keys():
    keys = []

    for ip in ("192.0.2.15", "192.0.2.16"):
        client = make_redis_mock()
        client.incr.return_value = 1

        with patch(
            "app.core.rate_limit.redis.Redis.from_url",
            return_value=client,
        ):
            check_create_rate_limit(ip)

        keys.append(client.incr.call_args.args[0])

    assert keys[0] != keys[1]