from unittest.mock import patch

from app.core.rate_limit import RateLimitExceeded


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