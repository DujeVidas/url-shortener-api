from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A URL shortening and analytics API.",
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": settings.app_name}