from unittest.mock import patch

from app.core.rate_limit import RateLimitExceeded, RateLimitInfo
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError


def test_create_url_checks_rate_limit(rate_limited_client):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        return_value=RateLimitInfo(
            limit=10,
            remaining=9,
            reset=45,
        ),
    ) as check:
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code in (200, 201), response.json()
    check.assert_called_once()

    assert response.headers["ratelimit-limit"] == "10"
    assert response.headers["ratelimit-remaining"] == "9"
    assert response.headers["ratelimit-reset"] == "45"

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



def test_429_contains_rate_limit_headers(rate_limited_client):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RateLimitExceeded(
            retry_after=30,
            limit=10,
        ),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 429
    assert response.headers["retry-after"] == "30"
    assert response.headers["ratelimit-limit"] == "10"
    assert response.headers["ratelimit-remaining"] == "0"
    assert response.headers["ratelimit-reset"] == "30"


def test_429_without_limit_keeps_existing_behavior(
    rate_limited_client,
):
    with patch(
        "app.api.dependencies.rate_limit.check_create_rate_limit",
        side_effect=RateLimitExceeded(retry_after=15),
    ):
        response = rate_limited_client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 429
    assert response.headers["retry-after"] == "15"
    assert response.headers["ratelimit-remaining"] == "0"
    assert response.headers["ratelimit-reset"] == "15"
    assert "ratelimit-limit" not in response.headers