import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        access_log=False,
        log_level="info",
        timeout_graceful_shutdown=25,
    )


if __name__ == "__main__":
    main()
