from unittest.mock import patch

from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError

from app.db.dependencies import get_db
from app.main import app


def test_readiness_when_postgres_and_redis_available(client):
    with patch(
        "app.api.routes.health.check_redis_health",
        return_value=True,
    ):
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_when_redis_returns_false(client):
    with patch(
        "app.api.routes.health.check_redis_health",
        return_value=False,
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_readiness_when_redis_connection_fails(client):
    with patch(
        "app.api.routes.health.check_redis_health",
        side_effect=RedisConnectionError("Redis unavailable"),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_readiness_when_postgres_fails(client):
    class FailingSession:
        def execute(self, statement):
            raise OperationalError(
                "SELECT 1",
                {},
                Exception("PostgreSQL unavailable"),
            )

    def override_get_db():
        yield FailingSession()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.routes.health.check_redis_health",
            return_value=True,
        ) as redis_check:
            response = client.get("/health/ready")
    finally:
        if previous is not None:
            app.dependency_overrides[get_db] = previous
        else:
            app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    redis_check.assert_not_called()


def test_liveness_does_not_depend_on_redis(client):
    with patch(
        "app.api.routes.health.check_redis_health",
        side_effect=RedisConnectionError("Redis unavailable"),
    ) as redis_check:
        response = client.get("/health/live")

    assert response.status_code == 200
    redis_check.assert_not_called()
