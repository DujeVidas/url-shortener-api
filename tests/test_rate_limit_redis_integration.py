import hashlib
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
import redis

from app.core.config import get_settings
from app.core.rate_limit import (
    RateLimitExceeded,
    check_create_rate_limit,
)

pytestmark = pytest.mark.redis_integration


@pytest.fixture
def redis_client():
    settings = get_settings()

    client = redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

    try:
        client.ping()
    except redis.exceptions.RedisError:
        client.close()
        pytest.skip("Redis is not available")

    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def isolated_ip(redis_client):
    # Each test gets a unique identity to avoid sharing counters.
    ip = f"test-{uuid.uuid4().hex}"

    yield ip

    # Remove only keys created for this test identity.
    client_hash = hashlib.sha256(
        ip.encode("utf-8")
    ).hexdigest()

    pattern = f"rate_limit:create:{client_hash}:*"

    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)


def rate_limit_key(ip: str, now: int, window: int) -> str:
    client_hash = hashlib.sha256(
        ip.encode("utf-8")
    ).hexdigest()

    window_id = now // window

    return f"rate_limit:create:{client_hash}:{window_id}"


def test_real_redis_increments_counter(redis_client, isolated_ip):
    settings = get_settings()
    now = int(time.time())

    with patch("app.core.rate_limit.time.time", return_value=now):
        first = check_create_rate_limit(isolated_ip)
        second = check_create_rate_limit(isolated_ip)

    assert first.remaining == settings.rate_limit_create_requests - 1
    assert second.remaining == settings.rate_limit_create_requests - 2

    key = rate_limit_key(
        isolated_ip,
        now,
        settings.rate_limit_create_window_seconds,
    )

    assert int(redis_client.get(key)) == 2


def test_real_redis_sets_expiration(redis_client, isolated_ip):
    settings = get_settings()
    now = int(time.time())

    with patch("app.core.rate_limit.time.time", return_value=now):
        check_create_rate_limit(isolated_ip)

    key = rate_limit_key(
        isolated_ip,
        now,
        settings.rate_limit_create_window_seconds,
    )

    ttl = redis_client.ttl(key)

    assert 0 < ttl <= settings.rate_limit_create_window_seconds + 1


def test_real_redis_rejects_excess_requests(redis_client, isolated_ip):
    settings = get_settings()
    now = int(time.time())

    with patch("app.core.rate_limit.time.time", return_value=now):
        for _ in range(settings.rate_limit_create_requests):
            check_create_rate_limit(isolated_ip)

        with pytest.raises(RateLimitExceeded) as exc_info:
            check_create_rate_limit(isolated_ip)

    assert exc_info.value.limit == settings.rate_limit_create_requests
    assert exc_info.value.retry_after >= 1


def test_real_redis_new_window_has_fresh_quota(
    redis_client,
    isolated_ip,
):
    settings = get_settings()
    window = settings.rate_limit_create_window_seconds

    current_window = int(time.time()) // window
    first_time = current_window * window
    second_time = (current_window + 1) * window

    with patch(
        "app.core.rate_limit.time.time",
        return_value=first_time,
    ):
        first = check_create_rate_limit(isolated_ip)

    with patch(
        "app.core.rate_limit.time.time",
        return_value=second_time,
    ):
        second = check_create_rate_limit(isolated_ip)

    assert first.remaining == settings.rate_limit_create_requests - 1
    assert second.remaining == settings.rate_limit_create_requests - 1

    first_key = rate_limit_key(isolated_ip, first_time, window)
    second_key = rate_limit_key(isolated_ip, second_time, window)

    assert first_key != second_key
    assert redis_client.exists(first_key) == 1
    assert redis_client.exists(second_key) == 1


def test_real_redis_concurrent_requests_are_atomic(
    redis_client,
    isolated_ip,
):
    settings = get_settings()
    limit = settings.rate_limit_create_requests
    now = int(time.time())

    def attempt():
        try:
            check_create_rate_limit(isolated_ip)
            return True
        except RateLimitExceeded:
            return False

    with patch("app.core.rate_limit.time.time", return_value=now):
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(
                lambda _: attempt(),
                range(limit + 10),
            ))

    assert sum(results) == limit
    assert results.count(False) == 10

    key = rate_limit_key(
        isolated_ip,
        now,
        settings.rate_limit_create_window_seconds,
    )

    assert int(redis_client.get(key)) == limit + 10
    assert redis_client.ttl(key) > 0