from uuid import UUID


def test_health_response_has_request_id(client):
    response = client.get("/health/live")

    assert response.status_code == 200

    request_id = response.headers["x-request-id"]

    assert str(UUID(request_id)) == request_id