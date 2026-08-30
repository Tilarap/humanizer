import json
import logging
from time import perf_counter

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.logging_conf import JsonFormatter
from app.main import app


@pytest.mark.asyncio
async def test_health_is_dependency_free_and_fast() -> None:
    # The installed Starlette TestClient warns that its HTTPX integration is deprecated.
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/health")
        started = perf_counter()
        responses = [await client.get("/health") for _ in range(5)]
        elapsed_per_request = (perf_counter() - started) / len(responses)

    assert all(response.status_code == 200 for response in responses)
    assert all(response.json() == {"status": "ok"} for response in responses)
    assert elapsed_per_request < 0.005


@pytest.mark.asyncio
async def test_ready_is_separate_from_liveness_without_a_key() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"config": False}}


@pytest.mark.asyncio
async def test_docs_are_available() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/docs")).status_code == 200


def test_settings_reject_an_invalid_port() -> None:
    try:
        Settings(_env_file=None, port=0)
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid ports must fail at boot")


def test_log_formatter_emits_json() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "service ready", (), None)
    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "service ready"
