def get_create_url_operation(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    return response.json()["paths"]["/api/v1/urls"]["post"]


def test_create_url_documents_rate_limit_headers(client):
    operation = get_create_url_operation(client)

    headers = operation["responses"]["201"]["headers"]

    assert "RateLimit-Limit" in headers
    assert "RateLimit-Remaining" in headers
    assert "RateLimit-Reset" in headers


def test_create_url_documents_rate_limit_exceeded(client):
    operation = get_create_url_operation(client)

    response = operation["responses"]["429"]

    assert "Retry-After" in response["headers"]
    assert "RateLimit-Remaining" in response["headers"]
    assert "RateLimit-Reset" in response["headers"]


def test_create_url_documents_redis_unavailable(client):
    operation = get_create_url_operation(client)

    response = operation["responses"]["503"]

    assert "Retry-After" in response["headers"]

    example = response["content"]["application/json"]["example"]

    assert example["detail"] == ("URL creation temporarily unavailable")


def test_rate_limit_headers_have_integer_schemas(client):
    operation = get_create_url_operation(client)

    for header in (
        "RateLimit-Limit",
        "RateLimit-Remaining",
        "RateLimit-Reset",
    ):
        schema = operation["responses"]["201"]["headers"][header]["schema"]

        assert schema["type"] == "integer"
