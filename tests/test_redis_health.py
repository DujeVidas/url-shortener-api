from unittest.mock import MagicMock, patch

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.redis_health import check_redis_health


def test_redis_health_returns_true_on_success():
    client = MagicMock()
    client.ping.return_value = True

    with patch(
        "app.core.redis_health.redis.Redis.from_url",
        return_value=client,
    ):
        result = check_redis_health()

    assert result is True
    client.ping.assert_called_once()
    client.close.assert_called_once()


def test_redis_health_returns_false_for_failed_ping():
    client = MagicMock()
    client.ping.return_value = False

    with patch(
        "app.core.redis_health.redis.Redis.from_url",
        return_value=client,
    ):
        result = check_redis_health()

    assert result is False
    client.close.assert_called_once()


def test_redis_health_closes_connection_on_error():
    client = MagicMock()
    client.ping.side_effect = RedisConnectionError(
        "Connection refused"
    )

    with patch(
        "app.core.redis_health.redis.Redis.from_url",
        return_value=client,
    ):
        with pytest.raises(RedisConnectionError):
            check_redis_health()

    client.close.assert_called_once()