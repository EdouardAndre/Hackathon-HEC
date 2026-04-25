from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    # TODO: add authentication and authorization before production use.
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
