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

def test_liveness_returns_200(client: TestClient):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_liveness_does_not_check_dependencies(client: TestClient):
    with (
        patch(
            "app.api.routes.health.redis_client.ping",
            side_effect=AssertionError("Redis should not be called"),
        ) as mock_redis,
        patch(
            "app.api.routes.health.Session.execute",
            side_effect=AssertionError("Database should not be called"),
        ) as mock_db,
    ):
        response = client.get("/health/live")

    assert response.status_code == 200
    mock_redis.assert_not_called()
    mock_db.assert_not_called()


def test_readiness_returns_200_when_database_available(
    client: TestClient,
):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_503_when_database_unavailable(
    client: TestClient,
):
    with patch(
        "app.api.routes.health.Session.execute",
        side_effect=OperationalError(
            statement="SELECT 1",
            params={},
            orig=Exception("Database unavailable"),
        ),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}