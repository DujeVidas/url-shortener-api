from app.core.redis import redis_client


CACHE_KEY_PREFIX = "url"
CACHE_TTL_SECONDS = 3600


def _cache_key(short_code: str) -> str:
    return f"{CACHE_KEY_PREFIX}:{short_code}"


def get_cached_url(short_code: str) -> str | None:
    return redis_client.get(_cache_key(short_code))


def cache_url(short_code: str, original_url: str) -> None:
    redis_client.set(
        _cache_key(short_code),
        original_url,
        ex=CACHE_TTL_SECONDS,
    )


def delete_cached_url(short_code: str) -> None:
    redis_client.delete(_cache_key(short_code))