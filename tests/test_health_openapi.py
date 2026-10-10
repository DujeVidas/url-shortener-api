def test_readiness_openapi_documents_success(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    operation = schema["paths"]["/health/ready"]["get"]

    assert operation["summary"] == "Check application readiness"

    assert "200" in operation["responses"]

    assert operation["responses"]["200"]["description"] == "Application is ready"

    example = operation["responses"]["200"]["content"]["application/json"]["example"]

    assert example == {"status": "ready"}


def test_readiness_openapi_documents_unavailable(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    operation = schema["paths"]["/health/ready"]["get"]

    assert "503" in operation["responses"]

    unavailable = operation["responses"]["503"]

    assert unavailable["description"] == ("One or more dependencies are unavailable")

    example = unavailable["content"]["application/json"]["example"]

    assert example == {"status": "not_ready"}


def test_readiness_openapi_explains_dependencies(client):
    response = client.get("/openapi.json")

    operation = response.json()["paths"]["/health/ready"]["get"]

    description = operation["description"]

    assert "PostgreSQL" in description
    assert "Redis" in description
    assert "503" in description
