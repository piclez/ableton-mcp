"""HTTP client for communicating with the Ableton Control Surface bridge."""

import httpx


class AbletonError(Exception):
    """Raised when communication with Ableton fails."""


class AbletonClient:
    """HTTP client that talks to the Control Surface HTTP server running inside Ableton."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.base_url = f"http://{host}:{port}"
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def _request(self, method: str, path: str, data=None) -> dict:
        try:
            resp = await self._client.request(method, path, json=data)
        except httpx.ConnectError:
            raise AbletonError(
                "Cannot connect to Ableton. Is Live running with the "
                "ableton_http_bridge Control Surface enabled?"
            )
        except httpx.TimeoutException:
            raise AbletonError(
                "Ableton did not respond in time. The operation may be too "
                "heavy or Live is unresponsive."
            )
        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("error", resp.text)
            except Exception:
                msg = resp.text
            raise AbletonError(f"Ableton returned error: {msg}")
        return resp.json()

    async def ping(self) -> dict:
        return await self._request("GET", "/live/ping")

    async def get(self, path: str) -> dict:
        return await self._request("GET", path)

    async def post(self, path: str, data=None) -> dict:
        return await self._request("POST", path, data or {})

    async def delete(self, path: str, data=None) -> dict:
        return await self._request("DELETE", path, data or {})

    async def close(self):
        await self._client.aclose()
