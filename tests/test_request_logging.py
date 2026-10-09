import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import JSONFormatter
from unittest.mock import patch


def test_json_formatter_produces_valid_json():
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="app.requests",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="HTTP request completed",
        args=(),
        exc_info=None,
    )

    record.event = "http_request"
    record.method = "GET"
    record.path = "/health/live"
    record.status_code = 200
    record.duration_ms = 1.5

    result = json.loads(formatter.format(record))

    assert result["level"] == "INFO"
    assert result["event"] == "http_request"
    assert result["method"] == "GET"
    assert result["path"] == "/health/live"
    assert result["status_code"] == 200
    assert result["duration_ms"] == 1.5
    assert "timestamp" in result


def test_request_logging_middleware(client: TestClient, caplog):
    with caplog.at_level(logging.INFO, logger="app.requests"):
        response = client.get("/health/live")

    assert response.status_code == 200

    request_logs = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "http_request"
    ]

    assert len(request_logs) == 1

    record = request_logs[0]

    assert record.method == "GET"
    assert record.path == "/health/live"
    assert record.status_code == 200
    assert record.duration_ms >= 0


def test_request_logging_excludes_query_parameters(
    client: TestClient,
    caplog,
):
    with caplog.at_level(logging.INFO, logger="app.requests"):
        response = client.get(
            "/health/live?token=secret-value"
        )

    assert response.status_code == 200

    request_logs = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "http_request"
    ]

    assert len(request_logs) == 1
    assert request_logs[0].path == "/health/live"
    assert "secret-value" not in request_logs[0].getMessage()




def test_redirect_logs_route_template(
    client: TestClient,
    caplog,
):
    with (
        patch(
            "app.api.routes.redirects.get_cached_url",
            return_value=None,
        ),
        caplog.at_level(logging.INFO, logger="app.requests"),
    ):
        response = client.get(
            "/sensitive-customer-link",
            follow_redirects=False,
        )

    assert response.status_code == 404

    request_logs = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "http_request"
    ]

    assert len(request_logs) == 1

    record = request_logs[0]

    assert record.path == "/{short_code}"
    assert "sensitive-customer-link" not in record.path


def test_analytics_logs_route_template(
    client: TestClient,
    caplog,
):
    with caplog.at_level(logging.INFO, logger="app.requests"):
        response = client.get(
            "/api/v1/urls/private-link/analytics"
        )

    assert response.status_code == 404

    request_logs = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "http_request"
    ]

    assert len(request_logs) == 1

    record = request_logs[0]

    assert record.path == "/api/v1/urls/{short_code}/analytics"
    assert "private-link" not in record.path