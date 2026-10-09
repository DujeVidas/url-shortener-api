from unittest.mock import patch

from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError


def test_health_check_all_dependencies_healthy(client: TestClient):
    with patch(
        "app.api.routes.health.redis_client.ping",
        return_value=True,
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "checks": {
            "database": "ok",
            "redis": "ok",
        },
    }


def test_health_check_redis_unavailable(client: TestClient):
    with patch(
        "app.api.routes.health.redis_client.ping",
        side_effect=RedisConnectionError("Redis unavailable"),
    ):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "checks": {
            "database": "ok",
            "redis": "error",
        },
    }


def test_health_check_database_unavailable(client: TestClient):
    with (
        patch(
            "app.api.routes.health.redis_client.ping",
            return_value=True,
        ),
        patch(
            "app.api.routes.health.Session.execute",
            side_effect=OperationalError(
                statement="SELECT 1",
                params={},
                orig=Exception("Database unavailable"),
            ),
        ),
    ):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "checks": {
            "database": "error",
            "redis": "ok",
        },
    }