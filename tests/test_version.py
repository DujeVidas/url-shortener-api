def test_version_endpoint_returns_metadata(client):
    response = client.get("/api/v1/version")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "URL Shortener API"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"


def test_version_endpoint_does_not_expose_secrets(client):
    response = client.get("/api/v1/version")

    assert response.status_code == 200

    data = response.json()

    assert set(data) == {"name", "version", "environment"}

    assert "database_url" not in data
    assert "redis_url" not in data


def test_version_endpoint_has_request_id(client):
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert "x-request-id" in response.headers


def test_version_endpoint_has_security_headers(client):
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
