import hashlib

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import URL


def test_create_url_returns_management_token_and_stores_only_hash(
    client_and_db: tuple[TestClient, Session],
):
    client, db = client_and_db

    response = client.post(
        "/api/v1/urls",
        json={
            "url": "https://example.com",
            "custom_alias": "managed-url-test",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["short_code"] == "managed-url-test"

    token = data["management_token"]

    assert isinstance(token, str)
    assert len(token) >= 40

    db.expire_all()

    url = db.scalar(select(URL).where(URL.short_code == "managed-url-test"))

    assert url is not None
    assert url.management_token_hash is not None

    expected_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    assert url.management_token_hash == expected_hash
    assert url.management_token_hash != token
