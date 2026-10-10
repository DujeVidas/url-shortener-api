from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.schemas.cache import CachedURL


def test_redirect_cache_miss(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "cache-miss-test",
        },
    )

    assert create_response.status_code == 201

    with (
        patch(
            "app.api.routes.redirects.get_cached_url",
            return_value=None,
        ) as mock_get,
        patch(
            "app.api.routes.redirects.cache_url",
        ) as mock_set,
    ):
        response = client.get(
            "/cache-miss-test",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"

    mock_get.assert_called_once_with("cache-miss-test")
    mock_set.assert_called_once()

    assert mock_set.call_args.kwargs["short_code"] == "cache-miss-test"
    assert mock_set.call_args.kwargs["original_url"] == "https://example.com/"

def test_redirect_cache_hit(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "cache-hit-test",
        },
    )

    assert create_response.status_code == 201

    with patch(
        "app.api.routes.redirects.get_cached_url",
        return_value=None,
    ), patch(
        "app.api.routes.redirects.cache_url",
    ):
        first_response = client.get(
            "/cache-hit-test",
            follow_redirects=False,
        )

    assert first_response.status_code == 307

    cached_url = CachedURL(
        url_id=1,
        original_url="https://example.com/",
        expires_at=None,
    )

    with (
        patch(
            "app.api.routes.redirects.get_cached_url",
            return_value=cached_url,
        ),
        patch(
            "app.api.routes.redirects.cache_url",
        ) as mock_set,
    ):
        response = client.get(
            "/cache-hit-test",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"

    mock_set.assert_not_called()

def test_redirect_unknown_code_returns_404(client: TestClient):
    with patch(
        "app.api.routes.redirects.get_cached_url",
        return_value=None,
    ):
        response = client.get(
            "/unknown-code-123",
            follow_redirects=False,
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_stale_cached_expiration_does_not_block_active_url(
    client: TestClient,
):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "stale-expiration-test",
        },
    )

    assert create_response.status_code == 201

    expired = datetime.now(timezone.utc) - timedelta(minutes=1)

    cached_url = CachedURL(
        url_id=1,
        original_url="https://example.com/",
        expires_at=expired,
    )

    with patch(
        "app.api.routes.redirects.get_cached_url",
        return_value=cached_url,
    ):
        response = client.get(
            "/stale-expiration-test",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"