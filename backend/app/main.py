from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api_docs import DESCRIPTION, TAGS_METADATA
from app.core.config import get_settings
from app.presentation.router import api_router

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hackathon HEC — Supply Chain API",
        version="1.0.0",
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"], summary="Liveness check")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
