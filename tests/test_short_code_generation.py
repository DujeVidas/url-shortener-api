from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.services.url_service import generate_short_code


def test_generated_short_code_format():
    short_code = generate_short_code()

    assert len(short_code) == 6
    assert short_code.isalnum()


def test_generated_short_code_custom_length():
    short_code = generate_short_code(length=10)

    assert len(short_code) == 10
    assert short_code.isalnum()


def test_generated_code_collision_generates_another(client: TestClient):
    first_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "taken-code",
        },
    )

    assert first_response.status_code == 201

    with patch(
        "app.services.url_service.generate_short_code",
        side_effect=["taken-code", "new-code"],
    ) as mock_generate:
        response = client.post(
            "/api/v1/urls",
            json={"url": "https://example.org"},
        )

    assert response.status_code == 201
    assert response.json()["short_code"] == "new-code"
    assert mock_generate.call_count == 2


def test_database_collision_retries_generated_code(client: TestClient):
    with patch(
        "app.api.routes.urls.generate_unique_short_code",
        side_effect=["retry-code", "successful-code"],
    ):
        first_response = client.post(
            "/api/v1/urls",
            json={
                "url": "https://example.com",
                "custom_alias": "retry-code",
            },
        )

        assert first_response.status_code == 201

        response = client.post(
            "/api/v1/urls",
            json={"url": "https://example.org"},
        )

    assert response.status_code == 201
    assert response.json()["short_code"] == "successful-code"


def test_exhausted_generation_attempts_returns_503(client: TestClient):
    first_response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "always-taken",
        },
    )

    assert first_response.status_code == 201

    with patch(
        "app.api.routes.urls.generate_unique_short_code",
        return_value="always-taken",
    ):
        response = client.post(
            "/api/v1/urls",
            json={"url": "https://example.org"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Could not generate a unique short code"
    )


def test_duplicate_custom_alias_returns_409(client: TestClient):
    payload = {
        "url": "https://example.com",
        "custom_alias": "duplicate-alias",
    }

    first_response = client.post("/api/v1/urls", json=payload)
    second_response = client.post("/api/v1/urls", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409