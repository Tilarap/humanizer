"""HTTP routes for operations and the LangGraph humanizer workflow."""

import logging
from functools import lru_cache
from time import monotonic

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from app.agent import create_humanizer_graph
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
_READY_CACHE_SECONDS = 30


class HumanizeRequest(BaseModel):
    """User-controlled writing preferences and source text."""

    text: str = Field(min_length=1, max_length=settings.max_input_chars)
    audience: str = Field(default="general", min_length=1, max_length=100)
    tone: str = Field(default="natural and conversational", min_length=1, max_length=100)


class HumanizeResponse(BaseModel):
    """Final text plus bounded workflow metadata."""

    text: str
    score: float
    passes: int
    model: str


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


@lru_cache(maxsize=1)
def get_humanizer_graph() -> CompiledStateGraph:
    """Build the stateless graph once per API process."""

    return create_humanizer_graph(settings)


@router.post("/humanize", response_model=HumanizeResponse, tags=["agent"])
async def humanize(request: HumanizeRequest) -> HumanizeResponse:
    """Rewrite text and evaluate it until it passes or reaches the pass limit."""

    key = settings.openai_api_key
    if not key or not key.get_secret_value().strip():
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")

    try:
        result = await get_humanizer_graph().ainvoke(
            {
                "original_text": request.text,
                "current_text": request.text,
                "audience": request.audience,
                "tone": request.tone,
                "feedback": [],
                "score": 0.0,
                "passes": 0,
            }
        )
    except Exception as exc:
        logger.exception(
            "humanizer workflow failed",
            extra={"event": "humanizer.failed", "service": settings.app_name},
        )
        raise HTTPException(status_code=502, detail="The model request failed") from exc

    return HumanizeResponse(
        text=result["current_text"],
        score=result["score"],
        passes=result["passes"],
        model=settings.openai_model,
    )
