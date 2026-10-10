import time

from starlette.types import ASGIApp, Receive, Scope, Send


class ServerTimingMiddleware:
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

        start_time = time.perf_counter()

        async def send_with_timing(message):
            if message["type"] == "http.response.start":
                duration_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"server-timing"
                ]

                headers.append(
                    (
                        b"server-timing",
                        f"app;dur={duration_ms:.2f}".encode("ascii"),
                    )
                )

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)

        await self.app(scope, receive, send_with_timing)