from starlette.types import ASGIApp, Receive, Scope, Send

DEFAULT_CSP = (
    b"default-src 'none'; frame-ancestors 'none'"
)

SWAGGER_CSP = (
    b"default-src 'none'; "
    b"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    b"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    b"img-src 'self' data: https://fastapi.tiangolo.com; "
    b"connect-src 'self'; "
    b"font-src https://cdn.jsdelivr.net; "
    b"frame-ancestors 'none'"
)

SECURITY_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-frame-options", b"DENY"),
    (
        b"content-security-policy",
        DEFAULT_CSP,
    ),
)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if path == "/docs":
            security_headers = (
                *SECURITY_HEADERS[:-1],
                (b"content-security-policy", SWAGGER_CSP),
            )
        else:
            security_headers = SECURITY_HEADERS

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                header_names = {
                    name for name, _ in security_headers
                }

                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in header_names
                ]

                headers.extend(security_headers)

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)

        await self.app(scope, receive, send_with_security_headers)