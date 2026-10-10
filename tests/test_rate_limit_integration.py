from unittest.mock import patch

from app.core.rate_limit import RateLimitExceeded
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError


def test_create_url_checks_rate_limit(rate_limited_client):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit"
    ) as check:
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={
                "url": "https://example.com",
            },
        )

    assert response.status_code in (200, 201)
    check.assert_called_once()


def test_create_url_returns_429(rate_limited_client):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RateLimitExceeded(retry_after=30),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={
                "url": "https://example.com",
            },
        )

    assert response.status_code == 429

    assert response.json()["detail"] == "Rate limit exceeded"

    assert response.headers["retry-after"] == "30"

    assert (
        response.json()["request_id"]
        == response.headers["x-request-id"]
    )

def test_create_url_returns_503_when_redis_unavailable(
    rate_limited_client,
):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RedisConnectionError("Redis unavailable"),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "URL creation temporarily unavailable"
    )
    assert response.headers["retry-after"] == "5"


def test_redis_timeout_returns_503(rate_limited_client):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RedisTimeoutError("Redis timed out"),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"


def test_redis_error_response_has_request_id(
    rate_limited_client,
):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RedisConnectionError("Redis unavailable"),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 503
    assert (
        response.json()["request_id"]
        == response.headers["x-request-id"]
    )


def test_redis_error_response_has_security_headers(
    rate_limited_client,
):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RedisConnectionError("Redis unavailable"),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 503
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_redis_failure_does_not_expose_internal_details(
    rate_limited_client,
):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RedisConnectionError(
            "Redis connection refused at internal-host:6379"
        ),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 503
    assert "internal-host" not in response.text
    assert "connection refused" not in response.text.lower()