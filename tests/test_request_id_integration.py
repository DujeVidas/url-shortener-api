from uuid import UUID


def test_health_response_has_request_id(client):
    response = client.get("/health/live")

    assert response.status_code == 200

    request_id = response.headers["x-request-id"]

    assert str(UUID(request_id)) == request_id

def test_oversized_request_body_contains_request_id(client):
    response = client.post(
        "/api/v1/urls",
        content=b"x" * 20000,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["request_id"] == response.headers["x-request-id"]