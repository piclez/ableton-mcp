"""Tests for AbletonClient HTTP error handling."""

import httpx
import pytest
import respx

from ableton_mcp.client import AbletonClient, AbletonError

BASE = "http://localhost:8765"


@pytest.fixture
def client():
    return AbletonClient()


@pytest.mark.anyio
@respx.mock
async def test_get_returns_json(client):
    respx.get(f"{BASE}/live/ping").mock(return_value=httpx.Response(200, json={"status": "ok"}))
    result = await client.get("/live/ping")
    assert result == {"status": "ok"}


@pytest.mark.anyio
@respx.mock
async def test_post_sends_json_body(client):
    route = respx.post(f"{BASE}/live/transport/bpm").mock(
        return_value=httpx.Response(200, json={"bpm": 128.0})
    )
    await client.post("/live/transport/bpm", {"bpm": 128.0})
    assert route.called
    import json
    body = json.loads(route.calls.last.request.content)
    assert body == {"bpm": 128.0}


@pytest.mark.anyio
@respx.mock
async def test_404_raises_ableton_error(client):
    respx.get(f"{BASE}/live/bogus").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    with pytest.raises(AbletonError, match="Not found"):
        await client.get("/live/bogus")


@pytest.mark.anyio
@respx.mock
async def test_500_raises_ableton_error(client):
    respx.post(f"{BASE}/live/transport/play").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    with pytest.raises(AbletonError, match="boom"):
        await client.post("/live/transport/play")


@pytest.mark.anyio
async def test_connect_error_raises_ableton_error(client):
    # No respx mock → real connection attempt → ConnectError
    with pytest.raises(AbletonError, match="Cannot connect"):
        await client.get("/live/ping")


@pytest.mark.anyio
@respx.mock
async def test_delete_passes_body(client):
    route = respx.delete(f"{BASE}/live/tracks/0").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    await client.delete("/live/tracks/0", {"confirm": True})
    assert route.called
