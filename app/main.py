"""FastAPI application factory and local process entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.routes import router
from app.config import PORT, settings
from app.logging_conf import configure_logging

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "application started",
        extra={"event": "application.started", "service": settings.app_name},
    )
    yield
    logger.info(
        "application stopped",
        extra={"event": "application.stopped", "service": settings.app_name},
    )


def create_app() -> FastAPI:
    application = FastAPI(title="Humanizer Agent", version=__version__, lifespan=lifespan)
    application.state.settings = settings
    application.include_router(router)
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_config=None)
