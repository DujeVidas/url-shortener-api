import re

TIMING_PATTERN = re.compile(r"^app;dur=\d+\.\d{2}$")


def test_health_response_has_server_timing(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert TIMING_PATTERN.fullmatch(
        response.headers["server-timing"]
    )


def test_oversized_request_has_server_timing(client):
    response = client.post(
        "/api/v1/urls",
        content=b"x" * 20000,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert TIMING_PATTERN.fullmatch(
        response.headers["server-timing"]
    )
    assert "x-request-id" in response.headers