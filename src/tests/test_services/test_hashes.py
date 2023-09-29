import uuid

import httpx
import pytest
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app import main


@pytest.mark.asyncio
async def test_create_token_by_username_and_passowrd_hash(
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = str(uuid.uuid4())

    # 模擬前端
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        # 先獲取 hash 資訊
        resp = await client.get(
            f"/v1/auth/users/hashes?username={username}",
        )
        assert resp.status_code == 404
