import hashlib
import time

import redis

from app.core.config import get_settings


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


def check_create_rate_limit(client_ip: str) -> None:
    settings = get_settings()

    # Avoid placing raw client IP addresses in Redis keys.
    client_hash = hashlib.sha256(
        client_ip.encode("utf-8")
    ).hexdigest()

    window = settings.rate_limit_create_window_seconds
    limit = settings.rate_limit_create_requests

    # Fixed time-window identifier.
    window_id = int(time.time()) // window

    key = f"rate_limit:create:{client_hash}:{window_id}"

    client = redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

    try:
        # Atomic increment ensures concurrent requests cannot
        # bypass the counter.
        count = client.incr(key)

        if count == 1:
            client.expire(key, window + 1)

        if count > limit:
            retry_after = window - (int(time.time()) % window)

            raise RateLimitExceeded(
                retry_after=max(1, retry_after)
            )
    finally:
        client.close()