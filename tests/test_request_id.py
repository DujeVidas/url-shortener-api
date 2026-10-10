from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_context import request_id_context
from app.middleware.request_id import RequestIDMiddleware


def make_client():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"request_id": request_id_context.get()}

    return TestClient(app)


def test_response_contains_request_id():
    client = make_client()

    response = client.get("/test")

    assert response.status_code == 200

    request_id = response.headers["x-request-id"]

    assert str(UUID(request_id)) == request_id


def test_request_id_is_available_inside_endpoint():
    client = make_client()

    response = client.get("/test")

    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_each_request_receives_unique_id():
    client = make_client()

    first = client.get("/test")
    second = client.get("/test")

    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_client_cannot_override_request_id():
    client = make_client()

    response = client.get(
        "/test",
        headers={"X-Request-ID": "client-controlled-value"},
    )

    assert response.headers["x-request-id"] != "client-controlled-value"
    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_request_id_context_is_reset():
    client = make_client()

    client.get("/test")

    assert request_id_context.get() is None
