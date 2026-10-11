from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import URL


def test_analytics_rejects_missing_management_token(
    client: TestClient,
):
    creation_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "protected-analytics",
        },
    )

    assert creation_response.status_code == 201

    response = client.get(
        "/api/v1/urls/protected-analytics/analytics",
    )

    assert response.status_code == 403


def test_analytics_rejects_invalid_management_token(
    client: TestClient,
):
    creation_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "invalid-analytics-token",
        },
    )

    assert creation_response.status_code == 201

    response = client.get(
        "/api/v1/urls/invalid-analytics-token/analytics",
        headers={"X-Management-Token": "incorrect-token"},
    )

    assert response.status_code == 403


def test_analytics_accepts_valid_management_token(
    client: TestClient,
):
    creation_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "authorized-analytics",
        },
    )

    assert creation_response.status_code == 201

    token = creation_response.json()["management_token"]

    response = client.get(
        "/api/v1/urls/authorized-analytics/analytics",
        headers={"X-Management-Token": token},
    )

    assert response.status_code == 200
    assert response.json()["short_code"] == "authorized-analytics"
    assert "management_token" not in response.json()
    assert "management_token_hash" not in response.json()


def test_analytics_unknown_url_returns_404(
    client: TestClient,
):
    response = client.get(
        "/api/v1/urls/nonexistent-url/analytics",
    )

    assert response.status_code == 404


def test_analytics_unknown_url_with_token_returns_404(
    client: TestClient,
):
    response = client.get(
        "/api/v1/urls/nonexistent-url/analytics",
        headers={"X-Management-Token": "invalid-token"},
    )

    assert response.status_code == 404


def test_analytics_legacy_url_rejects_management_token(
    client_and_db: tuple[TestClient, Session],
):
    client, db = client_and_db

    legacy_url = URL(
        short_code="legacy-analytics",
        original_url="https://example.com",
        management_token_hash=None,
    )

    db.add(legacy_url)
    db.commit()

    response = client.get(
        "/api/v1/urls/legacy-analytics/analytics",
        headers={"X-Management-Token": "arbitrary-token"},
    )

    assert response.status_code == 403
