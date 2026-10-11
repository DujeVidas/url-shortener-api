from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import URL
from app.schemas.cache import CachedURL


def test_deactivate_url_returns_204(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "delete-test",
        },
    )

    assert create_response.status_code == 201
    management_token = create_response.json()["management_token"]

    with patch(
        "app.api.routes.urls.delete_cached_url",
    ) as mock_delete_cache:
        response = client.delete(
            "/api/v1/urls/delete-test",
            headers={"X-Management-Token": management_token},
        )

    assert response.status_code == 204
    assert response.content == b""
    mock_delete_cache.assert_called_once_with("delete-test")


def test_deactivated_url_cannot_redirect(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "inactive-test",
        },
    )

    assert create_response.status_code == 201
    management_token = create_response.json()["management_token"]

    with patch("app.api.routes.urls.delete_cached_url"):
        delete_response = client.delete(
            "/api/v1/urls/inactive-test",
            headers={"X-Management-Token": management_token},
        )

    assert delete_response.status_code == 204

    with patch(
        "app.api.routes.redirects.get_cached_url",
        return_value=None,
    ):
        redirect_response = client.get(
            "/inactive-test",
            follow_redirects=False,
        )

    assert redirect_response.status_code == 404


def test_deactivating_unknown_url_returns_404(client: TestClient):
    response = client.delete("/api/v1/urls/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_deactivating_twice_returns_404(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "delete-twice",
        },
    )

    assert create_response.status_code == 201
    management_token = create_response.json()["management_token"]

    with patch("app.api.routes.urls.delete_cached_url"):
        first_response = client.delete(
            "/api/v1/urls/delete-twice",
            headers={"X-Management-Token": management_token},
        )
        second_response = client.delete(
            "/api/v1/urls/delete-twice",
            headers={"X-Management-Token": management_token},
        )

    assert first_response.status_code == 204
    assert second_response.status_code == 404


def test_analytics_survive_deactivation(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "history-test",
        },
    )

    assert create_response.status_code == 201
    management_token = create_response.json()["management_token"]

    with (
        patch(
            "app.api.routes.redirects.get_cached_url",
            return_value=None,
        ),
        patch("app.api.routes.redirects.cache_url"),
    ):
        redirect_response = client.get(
            "/history-test",
            follow_redirects=False,
        )

    assert redirect_response.status_code == 307

    with patch("app.api.routes.urls.delete_cached_url"):
        delete_response = client.delete(
            "/api/v1/urls/history-test",
            headers={"X-Management-Token": management_token},
        )

    assert delete_response.status_code == 204

    analytics_response = client.get(
        "/api/v1/urls/history-test/analytics",
        headers={"X-Management-Token": management_token},
    )

    assert analytics_response.status_code == 200
    assert analytics_response.json()["total_clicks"] == 1


def test_stale_cache_cannot_redirect_deactivated_url(client_and_db):
    client, db = client_and_db

    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "stale-cache-test",
        },
    )

    assert create_response.status_code == 201
    management_token = create_response.json()["management_token"]

    url = db.scalar(select(URL).where(URL.short_code == "stale-cache-test"))

    assert url is not None

    cached_url = CachedURL(
        url_id=url.id,
        original_url=url.original_url,
        expires_at=url.expires_at,
    )

    # Simulate Redis invalidation failing during deactivation.
    with patch("app.api.routes.urls.delete_cached_url"):
        delete_response = client.delete(
            "/api/v1/urls/stale-cache-test",
            headers={"X-Management-Token": management_token},
        )

    assert delete_response.status_code == 204

    # Simulate Redis still returning the old cached URL.
    with patch(
        "app.api.routes.redirects.get_cached_url",
        return_value=cached_url,
    ):
        redirect_response = client.get(
            "/stale-cache-test",
            follow_redirects=False,
        )

    assert redirect_response.status_code == 404
    assert redirect_response.json()["detail"] == "Short URL not found"
