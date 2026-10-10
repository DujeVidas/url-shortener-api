from unittest.mock import patch

from redis.exceptions import ConnectionError as RedisConnectionError


def test_liveness_does_not_call_rate_limiter(client):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RedisConnectionError("Redis unavailable"),
    ) as check:
        response = client.get("/health/live")

    assert response.status_code == 200
    check.assert_not_called()


def test_version_does_not_call_rate_limiter(client):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RedisConnectionError("Redis unavailable"),
    ) as check:
        response = client.get("/api/v1/version")

    assert response.status_code == 200
    check.assert_not_called()