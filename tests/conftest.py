import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies.rate_limit import enforce_create_rate_limit
from app.db.base import Base
from app.db.dependencies import get_db
from app.db.models import URL, ClickEvent
from app.main import app


@pytest.fixture
def client_and_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Skip rate limiting in existing endpoint tests.
    app.dependency_overrides[enforce_create_rate_limit] = lambda: None

    try:
        with TestClient(app) as test_client:
            with TestingSessionLocal() as db:
                yield test_client, db
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(client_and_db):
    test_client, _ = client_and_db
    return test_client


@pytest.fixture
def rate_limited_client(client):
    # Temporarily enable the real rate-limit dependency.
    previous = app.dependency_overrides.pop(
        enforce_create_rate_limit,
        None,
    )

    try:
        yield client
    finally:
        # Restore the override so other tests remain isolated.
        if previous is not None:
            app.dependency_overrides[enforce_create_rate_limit] = previous