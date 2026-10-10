import hashlib
from unittest.mock import MagicMock

from tests.test_rate_limit_redis_integration import isolated_ip


def test_isolated_ip_fixture_cleans_up_its_keys():
    redis_client = MagicMock()

    fixture_generator = isolated_ip.__wrapped__(
        redis_client
    )

    ip = next(fixture_generator)

    client_hash = hashlib.sha256(
        ip.encode("utf-8")
    ).hexdigest()

    expected_pattern = (
        f"rate_limit:create:{client_hash}:*"
    )

    redis_client.scan_iter.return_value = [
        b"rate_limit:create:test-key-1",
        b"rate_limit:create:test-key-2",
    ]

    try:
        next(fixture_generator)
    except StopIteration:
        pass

    redis_client.scan_iter.assert_called_once_with(
        match=expected_pattern
    )

    assert redis_client.delete.call_count == 2