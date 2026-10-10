from fastapi import HTTPException, Request

from app.core.rate_limit import (
    RateLimitExceeded,
    check_create_rate_limit,
)


def enforce_create_rate_limit(request: Request) -> None:
    client_ip = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    try:
        check_create_rate_limit(client_ip)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(exc.retry_after),
            },
        ) from exc