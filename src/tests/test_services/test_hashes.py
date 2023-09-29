import uuid

import httpx
import pytest
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio


@pytest.mark.asyncio
async def test_create_token_by_username_and_passowrd_hash(
    client: httpx.AsyncClient,
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = str(uuid.uuid4())

    # 模擬前端
    # 先獲取 hash 資訊
    resp = await client.get(
        f"/v1/auth/users/hashes?username={username}",
    )
    assert resp.status_code == 404
