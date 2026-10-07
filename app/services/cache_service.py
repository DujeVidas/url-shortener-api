from app.core.redis import redis_client
import json
from datetime import datetime


CACHE_KEY_PREFIX = "url"
CACHE_TTL_SECONDS = 3600


def _cache_key(short_code: str) -> str:
    return f"{CACHE_KEY_PREFIX}:{short_code}"


def get_cached_url(short_code: str) -> dict[str, int | str] | None:
    cached_value = redis_client.get(_cache_key(short_code))

    if cached_value is None:
        return None

    return json.loads(cached_value)


def cache_url(short_code: str, url_id: int, original_url: str, expires_at: datetime | None) -> None:

    cached_value = json.dumps(
        {
            "url_id": url_id,
            "original_url": original_url,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
    )

    redis_client.set(
        _cache_key(short_code),
        cached_value,
        ex=CACHE_TTL_SECONDS,
    )


def delete_cached_url(short_code: str) -> None:
    redis_client.delete(_cache_key(short_code))