import hashlib
from unittest.mock import MagicMock, patch

import pytest

from app.core.rate_limit import (
    RateLimitExceeded,
    check_create_rate_limit,
)


def make_redis_mock(count: int) -> MagicMock:
    client = MagicMock()
    client.eval.return_value = count
    return client


def run_check(ip: str, now: int, count: int):
    client = make_redis_mock(count)

    with (
        patch("app.core.rate_limit.time.time", return_value=now),
        patch(
            "app.core.rate_limit.redis.Redis.from_url",
            return_value=client,
        ),
    ):
        result = check_create_rate_limit(ip)

    return result, client


def test_first_second_of_window():
    info, client = run_check(
        ip="192.0.2.10",
        now=120,
        count=1,
    )

    assert info.limit == 10
    assert info.remaining == 9
    assert info.reset == 60
    client.close.assert_called_once()


def test_last_second_of_window():
    info, client = run_check(
        ip="192.0.2.10",
        now=179,
        count=1,
    )

    assert info.reset == 1
    client.close.assert_called_once()


def test_window_boundary_changes_redis_key():
    ip = "192.0.2.10"

    _, first_client = run_check(ip, now=179, count=10)
    _, second_client = run_check(ip, now=180, count=1)

    first_key = first_client.eval.call_args.args[2]
    second_key = second_client.eval.call_args.args[2]

    assert first_key != second_key

    assert first_key.endswith(":2")
    assert second_key.endswith(":3")


def test_new_window_restores_full_quota():
    ip = "192.0.2.10"

    old_info, _ = run_check(ip, now=179, count=10)
    new_info, _ = run_check(ip, now=180, count=1)

    assert old_info.remaining == 0
    assert new_info.remaining == 9


def test_rejected_request_at_window_end():
    client = make_redis_mock(11)

    with (
        patch("app.core.rate_limit.time.time", return_value=179),
        patch(
            "app.core.rate_limit.redis.Redis.from_url",
            return_value=client,
        ),
    ):
        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit("192.0.2.10")

    assert exc_info.value.retry_after == 1
    assert exc_info.value.limit == 10
    client.close.assert_called_once()


def test_rejected_request_at_window_start():
    client = make_redis_mock(11)

    with (
        patch("app.core.rate_limit.time.time", return_value=180),
        patch(
            "app.core.rate_limit.redis.Redis.from_url",
            return_value=client,
        ),
    ):
        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit("192.0.2.10")

    assert exc_info.value.retry_after == 60
    client.close.assert_called_once()


def test_redis_key_contains_sha256_hash():
    ip = "192.0.2.10"
    expected_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()

    _, client = run_check(ip, now=120, count=1)

    key = client.eval.call_args.args[2]

    assert key == f"rate_limit:create:{expected_hash}:2"


def test_expiration_is_longer_than_window():
    _, client = run_check(
        ip="192.0.2.10",
        now=120,
        count=1,
    )

    args = client.eval.call_args.args

    assert args[3] == 61