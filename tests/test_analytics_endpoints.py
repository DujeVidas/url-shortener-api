from unittest.mock import patch

from fastapi.testclient import TestClient


def test_analytics_counts_successful_redirects(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "analytics-test",
        },
    )

    assert create_response.status_code == 201

    with (
        patch(
            "app.api.routes.redirects.get_cached_url",
            return_value=None,
        ),
        patch(
            "app.api.routes.redirects.cache_url",
        ),
    ):
        for _ in range(3):
            response = client.get(
                "/analytics-test",
                follow_redirects=False,
            )
            assert response.status_code == 307

    analytics_response = client.get(
        "/api/v1/urls/analytics-test/analytics",
    )

    assert analytics_response.status_code == 200

    data = analytics_response.json()

    assert data["short_code"] == "analytics-test"
    assert data["total_clicks"] == 3
    assert data["first_clicked_at"] is not None
    assert data["last_clicked_at"] is not None


def test_analytics_zero_clicks(client: TestClient):
    create_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "analytics-zero",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/urls/analytics-zero/analytics",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_clicks"] == 0
    assert data["first_clicked_at"] is None
    assert data["last_clicked_at"] is None