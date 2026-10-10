import hashlib
import time
from dataclasses import dataclass

import redis

from app.core.config import get_settings


RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])

if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

return count
"""


@dataclass(frozen=True)
class RateLimitInfo:
    limit: int
    remaining: int
    reset: int


class RateLimitExceeded(Exception):
    def __init__(
        self,
        retry_after: int,
        limit: int | None = None,
    ):
        self.retry_after = retry_after
        self.limit = limit


def check_create_rate_limit(client_ip: str) -> RateLimitInfo:
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

        reset = max(1, window - (now % window))
        remaining = max(0, limit - count)

        if count > limit:
            raise RateLimitExceeded(
                retry_after=reset,
                limit=limit
                )

        return RateLimitInfo(
            limit=limit,
            remaining=remaining,
            reset=reset,
        )
    finally:
        client.close()