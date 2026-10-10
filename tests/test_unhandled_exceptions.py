from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exception_handlers import unhandled_exception_handler
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


def make_client():
    app = FastAPI()

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)

    @app.get("/unexpected")
    def unexpected_error():
        raise RuntimeError("SECRET_INTERNAL_ERROR_DETAILS")

    return TestClient(
        app,
        raise_server_exceptions=False,
    )


def test_unexpected_error_returns_500():
    client = make_client()

    response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_unexpected_error_does_not_expose_details():
    client = make_client()

    response = client.get("/unexpected")

    assert "SECRET_INTERNAL_ERROR_DETAILS" not in response.text


def test_unexpected_error_has_matching_request_id():
    client = make_client()

    response = client.get("/unexpected")

    request_id = response.headers["x-request-id"]

    assert str(UUID(request_id)) == request_id
    assert response.json()["request_id"] == request_id


def test_unexpected_error_has_security_headers():
    client = make_client()

    response = client.get("/unexpected")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"