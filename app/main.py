from fastapi import FastAPI

from app.api.routes.urls import router as urls_router
from app.core.config import get_settings
from app.api.routes.redirects import router as redirects_router
from app.api.routes import health
from app.core.logging import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A URL shortening and analytics API.",
    version="0.1.0",
    debug=settings.debug,
)

configure_logging()


app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_body_bytes=get_settings().max_request_body_bytes
)
app.include_router(health.router)
app.include_router(urls_router)
app.include_router(redirects_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": settings.app_name}