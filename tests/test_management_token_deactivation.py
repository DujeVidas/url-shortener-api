from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import URL


def test_delete_rejects_missing_management_token_without_deactivating(
    client_and_db: tuple[TestClient, Session],
):
    client, db = client_and_db

    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "missing-delete-token",
        },
    )

    assert create_response.status_code == 201

    response = client.delete(
        "/api/v1/urls/missing-delete-token",
    )

    assert response.status_code == 403

    db.expire_all()
    url = db.scalar(select(URL).where(URL.short_code == "missing-delete-token"))

    assert url is not None
    assert url.is_active is True


def test_delete_rejects_invalid_management_token_without_deactivating(
    client_and_db: tuple[TestClient, Session],
):
    client, db = client_and_db

    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "invalid-delete-token",
        },
    )

    assert create_response.status_code == 201

    response = client.delete(
        "/api/v1/urls/invalid-delete-token",
        headers={"X-Management-Token": "incorrect-token"},
    )

    assert response.status_code == 403

    db.expire_all()
    url = db.scalar(select(URL).where(URL.short_code == "invalid-delete-token"))

    assert url is not None
    assert url.is_active is True


def test_delete_unknown_url_returns_404(
    client: TestClient,
):
    response = client.delete(
        "/api/v1/urls/unknown-delete-url",
    )

    assert response.status_code == 404


def test_delete_unknown_url_with_token_returns_404(
    client: TestClient,
):
    response = client.delete(
        "/api/v1/urls/unknown-delete-url",
        headers={"X-Management-Token": "invalid-token"},
    )

    assert response.status_code == 404


def test_delete_legacy_url_rejects_token_without_deactivating(
    client_and_db: tuple[TestClient, Session],
):
    client, db = client_and_db

    legacy_url = URL(
        short_code="legacy-delete",
        original_url="https://example.com",
        management_token_hash=None,
    )

    db.add(legacy_url)
    db.commit()

    response = client.delete(
        "/api/v1/urls/legacy-delete",
        headers={"X-Management-Token": "arbitrary-token"},
    )

    assert response.status_code == 403

    db.expire_all()

    url = db.scalar(select(URL).where(URL.short_code == "legacy-delete"))

    assert url is not None
    assert url.is_active is True


def test_unauthorized_delete_does_not_invalidate_cache(
    client: TestClient,
):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "protected-cache",
        },
    )

    assert create_response.status_code == 201

    with patch("app.api.routes.urls.delete_cached_url") as mock_delete_cache:
        missing_token_response = client.delete(
            "/api/v1/urls/protected-cache",
        )

        invalid_token_response = client.delete(
            "/api/v1/urls/protected-cache",
            headers={"X-Management-Token": "incorrect-token"},
        )

    assert missing_token_response.status_code == 403
    assert invalid_token_response.status_code == 403

    mock_delete_cache.assert_not_called()
