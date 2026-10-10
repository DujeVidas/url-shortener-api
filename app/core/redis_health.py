import redis

from app.core.config import get_settings


def check_redis_health() -> bool:
    settings = get_settings()

    client = redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

    try:
        return bool(client.ping())
    finally:
        client.close()