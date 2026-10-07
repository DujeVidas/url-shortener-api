from fastapi import FastAPI

from app.api.routes.urls import router as urls_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A URL shortening and analytics API.",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(urls_router)

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": settings.app_name}