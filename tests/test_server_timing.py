import re

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.server_timing import ServerTimingMiddleware


TIMING_PATTERN = re.compile(r"^app;dur=\d+\.\d{2}$")


def make_client():
    app = FastAPI()
    app.add_middleware(ServerTimingMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"message": "ok"}

    return TestClient(app)


def test_server_timing_header_present():
    client = make_client()

    response = client.get("/test")

    assert response.status_code == 200
    assert TIMING_PATTERN.fullmatch(
        response.headers["server-timing"]
    )


def test_server_timing_is_non_negative():
    client = make_client()

    response = client.get("/test")

    value = response.headers["server-timing"]
    duration = float(value.split("=", 1)[1])

    assert duration >= 0


def test_server_timing_on_404():
    client = make_client()

    response = client.get("/missing")

    assert response.status_code == 404
    assert TIMING_PATTERN.fullmatch(
        response.headers["server-timing"]
    )


def test_server_timing_overrides_existing_value():
    app = FastAPI()
    app.add_middleware(ServerTimingMiddleware)

    @app.get("/test")
    def test_endpoint():
        return JSONResponse(
            content={"ok": True},
            headers={"Server-Timing": "incorrect"},
        )

    client = TestClient(app)

    response = client.get("/test")

    assert TIMING_PATTERN.fullmatch(
        response.headers["server-timing"]
    )
    assert "incorrect" not in response.headers["server-timing"]