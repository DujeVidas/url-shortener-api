def test_swagger_docs_allows_required_assets(client):
    response = client.get("/docs")

    assert response.status_code == 200

    csp = response.headers["content-security-policy"]

    assert "https://cdn.jsdelivr.net" in csp
    assert "'unsafe-inline'" in csp
    assert "connect-src 'self'" in csp
    assert "font-src https://cdn.jsdelivr.net" in csp


def test_api_keeps_strict_csp(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )
