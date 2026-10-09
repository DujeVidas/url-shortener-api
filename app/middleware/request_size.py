from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from app.core.error_responses import error_response


class RequestBodyTooLarge(Exception):
    pass


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        content_length = headers.get("content-length")

        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = -1

            if declared_size > self.max_body_bytes:
                await self._reject(scope, receive, send)
                return

        received_bytes = 0
        buffered_messages: list[Message] = []

        # Read the body before handing the request to FastAPI.
        # Stop as soon as it exceeds the configured limit.
        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                buffered_messages.append(message)
                continue

            received_bytes += len(message.get("body", b""))

            if received_bytes > self.max_body_bytes:
                await self._reject(scope, receive, send)
                return

            buffered_messages.append(message)

            if not message.get("more_body", False):
                break

        async def buffered_receive() -> Message:
            if buffered_messages:
                return buffered_messages.pop(0)

            return await receive()

        await self.app(scope, buffered_receive, send)

    async def _reject(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        response = error_response(
            status_code=413,
            detail="Request body too large",
        )
        await response(scope, receive, send)