from fastapi import FastAPI

app = FastAPI(
    title="URL Shortener API",
    description="A URL shortening and analytics API.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "URL Shortener API"}