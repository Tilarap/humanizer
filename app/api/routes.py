"""Dependency-free liveness and cached configuration readiness routes."""

from functools import lru_cache
from time import monotonic

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings

router = APIRouter()
_READY_CACHE_SECONDS = 30


@router.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    """Return process liveness without touching the network, storage, or model."""

    return {"status": "ok"}


@lru_cache(maxsize=1)
def _configuration_ready(_window: int) -> bool:
    key = settings.openai_api_key
    return bool(key and key.get_secret_value().strip())


@router.get("/ready", tags=["operations"])
async def ready() -> JSONResponse:
    """Report whether required request-time configuration is present."""

    is_ready = _configuration_ready(int(monotonic() // _READY_CACHE_SECONDS))
    content = {"status": "ready" if is_ready else "not_ready", "checks": {"config": is_ready}}
    return JSONResponse(content=content, status_code=200 if is_ready else 503)
