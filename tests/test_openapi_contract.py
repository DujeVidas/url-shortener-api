from openapi_spec_validator import validate


def test_openapi_schema_is_valid(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    validate(schema)


def test_openapi_contains_required_endpoints(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    required_operations = {
        "/health/live": "get",
        "/health/ready": "get",
        "/api/v1/version": "get",
        "/api/v1/urls": "post",
        "/api/v1/urls/{short_code}/analytics": "get",
        "/api/v1/urls/{short_code}": "delete",
        "/{short_code}": "get",
    }

    for path, method in required_operations.items():
        assert path in paths, f"Missing endpoint: {path}"
        assert method in paths[path], f"Missing {method.upper()} operation for {path}"
