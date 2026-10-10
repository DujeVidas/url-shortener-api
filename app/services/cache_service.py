import json
import logging
from datetime import datetime

from pydantic import ValidationError
from redis.exceptions import RedisError

from app.core.redis import redis_client
from app.schemas.cache import CachedURL

logger = logging.getLogger(__name__)


CACHE_KEY_PREFIX = "url"
CACHE_TTL_SECONDS = 3600


def _cache_key(short_code: str) -> str:
    return f"{CACHE_KEY_PREFIX}:{short_code}"


def get_cached_url(short_code: str) -> CachedURL | None:
    try:
        cached_value = redis_client.get(_cache_key(short_code))
    except RedisError:
        logger.warning(
            "Redis unavailable while reading short code %s",
            short_code,
        )
        return None

    if cached_value is None:
        return None

    try:
        return CachedURL.model_validate_json(cached_value)
    except (ValidationError, ValueError, TypeError):
        logger.warning(
            "Invalid cached data for short code %s",
            short_code,
        )
        return None


def cache_url(
    short_code: str, url_id: int, original_url: str, expires_at: datetime | None
) -> None:

    cached_value = json.dumps(
        {
            "url_id": url_id,
            "original_url": original_url,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
    )
    try:
        redis_client.set(
            _cache_key(short_code),
            cached_value,
            ex=CACHE_TTL_SECONDS,
        )
    except RedisError:
        logger.warning(
            "Redis unavailable while caching short code %s",
            short_code,
        )


def delete_cached_url(short_code: str) -> None:
    try:
        redis_client.delete(_cache_key(short_code))
    except RedisError:
        logger.warning(
            "Redis unavailable while invalidating short code %s",
            short_code,
        )
