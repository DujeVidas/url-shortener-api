from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.request_context import request_id_context


class RequestIDMiddleware:
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

        request_id = str(uuid4())
        token = request_id_context.set(request_id)

        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
                message = {**message, "headers": headers}

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_context.reset(token)