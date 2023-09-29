import httpx
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client: httpx.AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"api": "fastit", "version": None}
