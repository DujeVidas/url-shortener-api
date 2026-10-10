from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import SecurityHeadersMiddleware


def make_client():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"message": "ok"}

    @app.get("/redirect")
    def redirect_endpoint():
        from fastapi.responses import RedirectResponse

        return RedirectResponse(
            url="https://example.com",
            status_code=307,
        )

    return TestClient(app)


def test_security_headers_present():
    client = make_client()

    response = client.get("/test")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    assert (
        response.headers["content-security-policy"]
        == "default-src 'none'; frame-ancestors 'none'"
    )


def test_security_headers_on_404():
    client = make_client()

    response = client.get("/missing")

    assert response.status_code == 404
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_security_headers_on_redirect():
    client = make_client()

    response = client.get(
        "/redirect",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_security_headers_override_existing_values():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    def test_endpoint():
        from fastapi.responses import JSONResponse

        return JSONResponse(
            content={"ok": True},
            headers={
                "X-Frame-Options": "SAMEORIGIN",
                "X-Content-Type-Options": "incorrect",
            },
        )

    client = TestClient(app)

    response = client.get("/test")

    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
