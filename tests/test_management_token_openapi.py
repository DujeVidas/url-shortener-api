import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("path", "method", "success_status"),
    [
        ("/api/v1/urls/{short_code}/analytics", "get", "200"),
        ("/api/v1/urls/{short_code}", "delete", "204"),
    ],
)
def test_management_token_openapi_contract(
    client: TestClient,
    path: str,
    method: str,
    success_status: str,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    operation = response.json()["paths"][path][method]

    token_headers = [
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == "X-Management-Token" and parameter["in"] == "header"
    ]

    assert len(token_headers) == 1
    assert token_headers[0]["required"] is False

    documented_responses = operation["responses"]

    for status_code in (success_status, "403", "404"):
        assert status_code in documented_responses
