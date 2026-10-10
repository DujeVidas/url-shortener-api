import hashlib
import time

import redis

from app.core.config import get_settings


RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])

if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

return count
"""


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


def check_create_rate_limit(client_ip: str) -> None:
    settings = get_settings()

    client_hash = hashlib.sha256(
        client_ip.encode("utf-8")
    ).hexdigest()

    window = settings.rate_limit_create_window_seconds
    limit = settings.rate_limit_create_requests

    now = int(time.time())
    window_id = now // window

    key = f"rate_limit:create:{client_hash}:{window_id}"

    client = redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

    try:
        count = int(
            client.eval(
                RATE_LIMIT_SCRIPT,
                1,
                key,
                window + 1,
            )
        )

        if count > limit:
            retry_after = window - (now % window)

            raise RateLimitExceeded(
                retry_after=max(1, retry_after)
            )
    finally:
        client.close()