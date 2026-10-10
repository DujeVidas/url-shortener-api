from starlette.types import ASGIApp, Receive, Scope, Send


SECURITY_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-frame-options", b"DENY"),
    (
        b"content-security-policy",
        b"default-src 'none'; frame-ancestors 'none'",
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

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                header_names = {
                    name for name, _ in SECURITY_HEADERS
                }

                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in header_names
                ]

                headers.extend(SECURITY_HEADERS)

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)

        await self.app(scope, receive, send_with_security_headers)