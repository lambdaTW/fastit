import httpx
import pytest

from app import main


@pytest.mark.asyncio
async def test_create_jwt_token_by_username_and_passowrd():
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post(
            "/v1/auth/users/tokens", json={"username": "test", "password": "testme"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
