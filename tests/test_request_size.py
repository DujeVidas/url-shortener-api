from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.request_size import RequestSizeLimitMiddleware


def make_client(max_body_bytes=16384):
    app = FastAPI()

    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_body_bytes=max_body_bytes,
    )

    @app.post("/echo")
    async def echo(payload: dict):
        return payload

    return TestClient(app)


def test_small_request_is_allowed():
    client = make_client()

    response = client.post(
        "/echo",
        json={"message": "hello"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_request_exceeding_content_length_is_rejected():
    client = make_client(max_body_bytes=1024)

    response = client.post(
        "/echo",
        json={"message": "x" * 2000},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"
    assert "request_id" in response.json()


def test_request_at_limit_is_allowed():
    client = make_client(max_body_bytes=1024)

    payload = b'{"message":"' + b"x" * 1010 + b'"}'

    assert len(payload) == 1024

    response = client.post(
        "/echo",
        content=payload,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200


def test_missing_content_length_is_checked():
    client = make_client(max_body_bytes=1024)

    def body():
        yield b'{"message":"'
        yield b"x" * 2000
        yield b'"}'

    response = client.post(
        "/echo",
        content=body(),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413