from fastapi.testclient import TestClient


def test_create_url_with_custom_alias(client: TestClient):
    response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "my-test-link",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["short_code"] == "my-test-link"
    assert data["original_url"] == "https://example.com/"
    assert data["short_url"].endswith("/my-test-link")
    assert data["expires_at"] is None
    assert "created_at" in data


def test_create_url_with_generated_code(client: TestClient):
    response = client.post(
        "/api/v1/urls",
        json={"url": "https://example.com"},
    )

    assert response.status_code == 201

    data = response.json()

    assert len(data["short_code"]) == 6
    assert data["short_code"].isalnum()


def test_duplicate_custom_alias_returns_409(client: TestClient):
    payload = {
        "url": "https://example.com",
        "custom_alias": "duplicate-test",
    }

    first_response = client.post("/api/v1/urls", json=payload)
    second_response = client.post("/api/v1/urls", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_url_returns_422(client: TestClient):
    response = client.post(
        "/api/v1/urls",
        json={"url": "not-a-url"},
    )

    assert response.status_code == 422


def test_reserved_alias_returns_422(client: TestClient):
    response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "api",
        },
    )

    assert response.status_code == 422