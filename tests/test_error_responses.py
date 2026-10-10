from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.request_id import RequestIDMiddleware


def make_client():
    app = FastAPI()

    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_middleware(RequestIDMiddleware)

    class Item(BaseModel):
        name: str

    @app.get("/error")
    def raise_error():
        raise HTTPException(status_code=404, detail="Item not found")

    @app.post("/items")
    def create_item(item: Item):
        return item

    return TestClient(app)


def assert_matching_request_id(response):
    request_id = response.headers["x-request-id"]

    assert str(UUID(request_id)) == request_id
    assert response.json()["request_id"] == request_id


def test_http_error_contains_request_id():
    client = make_client()

    response = client.get("/error")

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
    assert_matching_request_id(response)


def test_validation_error_contains_request_id():
    client = make_client()

    response = client.post("/items", json={})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert_matching_request_id(response)


def test_unmatched_route_contains_request_id():
    client = make_client()

    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert_matching_request_id(response)


def test_success_response_format_unchanged():
    client = make_client()

    response = client.post("/items", json={"name": "example"})

    assert response.status_code == 200
    assert response.json() == {"name": "example"}
    assert "x-request-id" in response.headers