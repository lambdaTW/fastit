import httpx
import pytest

from app import main


@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"api": "fastit", "version": None}
