"""HTTP client for communicating with the Ableton Control Surface bridge."""

import httpx


class AbletonClient:
    """HTTP client that talks to the Control Surface HTTP server running inside Ableton."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.base_url = f"http://{host}:{port}"
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def ping(self) -> dict:
        resp = await self._client.get("/live/ping")
        resp.raise_for_status()
        return resp.json()

    async def get(self, path: str) -> dict:
        resp = await self._client.get(path)
        resp.raise_for_status()
        return resp.json()

    async def post(self, path: str, data: dict | None = None) -> dict:
        resp = await self._client.post(path, json=data or {})
        resp.raise_for_status()
        return resp.json()

    async def delete(self, path: str, data: dict | None = None) -> dict:
        resp = await self._client.request("DELETE", path, json=data or {})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()
