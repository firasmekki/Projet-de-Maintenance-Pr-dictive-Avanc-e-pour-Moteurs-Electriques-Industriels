import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.predictions import router as prediction_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Module 5 — ML prediction routes
    app.include_router(prediction_router)

    @app.get("/api/v1/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "version": settings.app_version}

    logger.info("%s v%s started", settings.app_name, settings.app_version)
    return app


app = create_app()
