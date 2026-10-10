from unittest.mock import MagicMock, patch

import pytest

from app.core.rate_limit import (
    RATE_LIMIT_SCRIPT,
    RateLimitExceeded,
    check_create_rate_limit,
)


def make_redis_mock(count: int):
    client = MagicMock()
    client.eval.return_value = count
    return client


def test_first_request_is_allowed():
    client = make_redis_mock(1)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("127.0.0.1")

    client.eval.assert_called_once()
    client.close.assert_called_once()


def test_request_within_limit_is_allowed():
    client = make_redis_mock(5)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("127.0.0.1")

    client.eval.assert_called_once()
    client.close.assert_called_once()


def test_request_above_limit_is_rejected():
    client = make_redis_mock(11)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit("127.0.0.1")

    assert exc_info.value.retry_after >= 1
    client.close.assert_called_once()


def test_client_ip_is_hashed_in_redis_key():
    client = make_redis_mock(1)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("192.0.2.15")

    args = client.eval.call_args.args

    assert args[0] == RATE_LIMIT_SCRIPT
    assert args[1] == 1

    key = args[2]

    assert "192.0.2.15" not in key
    assert key.startswith("rate_limit:create:")


def test_different_ips_generate_different_keys():
    keys = []

    for ip in ("192.0.2.15", "192.0.2.16"):
        client = make_redis_mock(1)

        with patch(
            "app.core.rate_limit.redis.Redis.from_url",
            return_value=client,
        ):
            check_create_rate_limit(ip)

        keys.append(client.eval.call_args.args[2])

    assert keys[0] != keys[1]


def test_rate_limit_uses_atomic_script():
    client = make_redis_mock(1)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("127.0.0.1")

    client.eval.assert_called_once()
    client.incr.assert_not_called()
    client.expire.assert_not_called()


def test_script_sets_expiration_for_new_counter():
    assert "redis.call('INCR', KEYS[1])" in RATE_LIMIT_SCRIPT
    assert "if count == 1 then" in RATE_LIMIT_SCRIPT
    assert "redis.call('EXPIRE', KEYS[1], ARGV[1])" in RATE_LIMIT_SCRIPT


def test_expiration_argument_is_window_plus_one():
    client = make_redis_mock(1)

    with patch(
        "app.core.rate_limit.redis.Redis.from_url",
        return_value=client,
    ):
        check_create_rate_limit("127.0.0.1")

    args = client.eval.call_args.args

    # Default window is 60 seconds.
    assert args[3] == 61
